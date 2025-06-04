from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from .serializers import ChatSessionSerializer, ChatMessageSerializer , BookMarkSerializer , EvaluationSerializer
from .models import ChatSession, ChatMessage, History , Bookmark , Evaluation
from django.http import StreamingHttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import uuid
import asyncio
import re
from langchain_core.messages import SystemMessage, AIMessage
from .stream_structure_agent8 import ABHFL
from threading import Thread
import concurrent.futures
import time
import traceback
import threading
from .evalution import StepNecessityEvaluator
import logging
import tiktoken
import time

logger = logging.getLogger(__name__)
# Render the main page
def my_view(request):
    return render(request, "index.html")


# Utility function to replace slashes with spaces
def replace_slashes(input_string: str) -> str:
    return re.sub(r'[\\/]', ' ', input_string)


# Helper function to iterate over async generator
def iter_over_async(ait):
    # Create a new event loop for this thread if one doesn't exist
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    ait = ait.__aiter__()
    
    async def get_next():
        try:
            obj = await ait.__anext__()
            return False, obj
        except StopAsyncIteration:
            return True, None
    
    while True:
        done, obj = loop.run_until_complete(get_next())
        if done:
            break
        yield obj



encoding = tiktoken.encoding_for_model("gpt-4-0613")
def calculate_token_length(messages):
            num_tokens = len(encoding.encode(messages))
            
            return num_tokens

def evaluate_and_save(evaluator1,questions, final_answer, events, ques_id,session_id):
    # Evaluate the agent's trajectory and save the data asynchronously
    input_token  = calculate_token_length(questions)
    output_token =  calculate_token_length(final_answer)
    eval_res = evaluator1.evaluate_agent_trajectory(
        input=questions.lower(),
        session_id=session_id,
        ques_id = ques_id,
        prediction=final_answer,
        agent_trajectory=events,
        input_token=input_token,
        output_token=output_token
    )
# API to create a new chat session
class NewChatAPIView(generics.CreateAPIView):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer

    def post(self, request, *args, **kwargs):
        HF_email = request.data.get('HF_email')
        if not HF_email:
            return Response({"error": "HF_email is required"}, status=status.HTTP_400_BAD_REQUEST)

        chat_session = ChatSession.objects.create(user_id=HF_email, session_id=str(uuid.uuid4()))
        return Response(self.get_serializer(chat_session).data, status=status.HTTP_201_CREATED)


# Main chat handling API
# Optimized ChatAPIView for generating and streaming bot responses without storing data
class ChatAPIView(APIView):
    serializer_class = ChatMessageSerializer

    def post(self, request):
        # Deserialize incoming data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            session_id = serializer.validated_data.get('session').session_id
            message = serializer.validated_data.get('input_prompt')
            ques_id = serializer.validated_data.get('ques_id')
            num_token = calculate_token_length(message)
            # Retrieve the session, if not found return error
            session = get_object_or_404(ChatSession, session_id=session_id)

            # Handle bot interaction if no answer is provided
            chat_history, created = History.objects.get_or_create(session = session)
                # Prepare the history in the desired format
            if created:
                chat_history.messages = []
                # print(history)
            messages = chat_history.get_messages()
            bot_instance = ABHFL(messages)  # Placeholder for bot logic
            response_chunks = []
            events = []

            evaluator1 = StepNecessityEvaluator()
            def generate():
                try:
                    if not bot_instance.message:
                        with open("prompts/main_prompt2.txt", "r", encoding="utf-8") as f:
                            text = f.read()
                            if num_token <= 8:
                                text += f"""
🚨 MANDATORY: ALL responses must be {num_token*65} tokens maximum. If longer content needed, provide brief summary + probe for specifics with suggestion from existing data.
"""
                        bot_instance.message.append(SystemMessage(content=text))
                    
                    
                    # asyncio.set_event_loop(loop)
                    questions = replace_slashes(message)
                    openai_response = iter_over_async(bot_instance.run_conversation(questions.lower()))

                    for event in openai_response:
                        kind = event["event"]
                        if kind == "on_chat_model_stream":
                            content = event["data"]["chunk"].content
                            if content:
                                response_chunks.append(content)
                                time.sleep(0.05)
                                yield content

                        if kind == "on_chain_end":
                            try:
                                
                                actions = event.get("data", {}).get("output", {}).get("actions", [])
                                for action in actions:
                                    output_str = "[No output found]"
                                    try:
                                        message_log = action.message_log
                                        for msg in reversed(message_log):
                                            if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content.strip():
                                                output_str = msg.content.strip()
                                                break
                                    except Exception as e:
                                        logger.warning(f"Failed to extract message content from action log: {e}")
                                        # pass  # Skip if message_log or content access fails

                                    events.append((action, output_str))
                            except Exception as e:
                                logger.error(f"Failed to process on_chain_end event data: {e}")
                                

                    final_answer = "".join(response_chunks)
                    bot_instance.message.append(AIMessage(content=final_answer))
                    chat_history.set_messages(bot_instance.message)
                    chat_history.save()
                    # yield f"\n[Final Answer Saved for Ques ID: {ques_id}]"
                    import threading
                    # evaluate_and_save(evaluator1,questions, final_answer, events, session_id)
                    threading.Thread(target=evaluate_and_save, args=(evaluator1,questions, final_answer, events,ques_id ,session)).start()

                except Exception as e:
                    yield f"Something went wrong. Please try again later"
                    # yield f"Error: {str(e)}"

            response = StreamingHttpResponse(generate(), content_type="text/event-stream")
            response["Cache-Control"] = "no-cache"
            response["X-Accel-Buffering"] = "no"
            return response


        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# API to store chat messages
# API to store chat messages (for saving/updating user messages)
class StoreChat(APIView):
    serializer_class = ChatMessageSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            session_id = serializer.validated_data.get('session').session_id
            message = serializer.validated_data.get('input_prompt')
            ques_id = serializer.validated_data.get('ques_id')
            answer = serializer.validated_data.get('output', None)
            feedback = serializer.validated_data.get('feedback', None)
            input_prompt_timestamp = serializer.validated_data.get('input_prompt_timestamp', None)
            output_timestamp = serializer.validated_data.get('output_timestamp', None)
            feedback = serializer.validated_data.get('feedback', None)
            select_feedback_response = serializer.validated_data.get('select_feedback_response', None)
            additional_comments = serializer.validated_data.get('additional_comments', None)

            # Validate required fields
            if not all([session_id, message, ques_id]):
                return Response({'error': 'Invalid payload. session_id, message, and ques_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Update or create the message in the database
            chat_message, created = ChatMessage.objects.update_or_create(
                session_id=session_id,
                ques_id=ques_id,
                defaults={
                'input_prompt': message,
                'output': answer,
                'input_prompt_timestamp': input_prompt_timestamp,
                'output_timestamp': output_timestamp,
                'feedback': feedback,
                'select_feedback_response': select_feedback_response,
                'additional_comments': additional_comments
            }
            )

            status_message = 'Message saved successfully' if created else 'Message updated successfully'
            return Response({
                'status': status_message,
                'message_id': chat_message.ques_id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# History API to retrieve or delete chat session data
class HistoryAPIView(APIView):
    def post(self, request):
        HF_email = request.data.get('HF_email')
        session_id = request.data.get('session', None)

        if HF_email and not session_id:
            sessions = ChatSession.objects.filter(user_id=HF_email, is_activate=True).order_by("-created_on")
            response_data = []

            for session in sessions:
                # Retrieve the first message for each session
                first_message = ChatMessage.objects.filter(session=session).first()
                
                # Build response data for each session
                response_data.append({
                    'session_id': session.session_id,
                    'first_message': first_message.input_prompt if first_message else '',
                    'session_name' : session.session_name,
                    'created_on': first_message.created_on if first_message else ""
                })

            return Response(response_data, status=status.HTTP_200_OK)

        elif HF_email and session_id:
            try:
                session = ChatSession.objects.get(user_id=HF_email, session_id=session_id)
            except ChatSession.DoesNotExist:
                return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

            messages = ChatMessage.objects.filter(session=session).order_by('created_on')
            
            serializer = ChatMessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        HF_email = request.data.get('HF_email')
        session_id = request.data.get('session', None)
        print(HF_email , session_id)
        if HF_email and session_id:
            try:
                session = ChatSession.objects.get(user_id=HF_email, session_id=session_id)
                session.is_activate = False
                session.save()
                return Response({'status': 'Session deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            except ChatSession.DoesNotExist:
                return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)

# Bookmark View
class BookmarkMessage(APIView):
    def post(self, request):
        """
        Add a bookmark for a session.
        """
        session_id = request.data.get('session_id')

        # Validate the required data
        if not session_id:
            return Response({"detail": "Session_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Fetch the session using session_id
            session = ChatSession.objects.get(session_id=session_id)
            
            # Check if the session is already bookmarked
            if Bookmark.objects.filter(session=session).exists():
                return Response({"detail": "This session is already bookmarked."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the bookmark
            bookmark = Bookmark.objects.create(session=session)
            
            # Serialize the bookmark data for response
            serializer = BookMarkSerializer(bookmark)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ChatSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request):
        session_id = request.data.get('session_id')

        # Validate the required data
        if not session_id:
            return Response({"detail": "Session_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the session using session_id
            session = ChatSession.objects.get(session_id=session_id)

            # Check if a bookmark exists for the session
            bookmark = Bookmark.objects.get(session=session)
            
            # Delete the bookmark
            bookmark.delete()
            return Response({"detail": f"Bookmark deleted successfully for session {session_id}."}, status=status.HTTP_200_OK)

        except ChatSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        except Bookmark.DoesNotExist:
            return Response({"detail": "Bookmark not found for this session."}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        """
        Retrieve details for bookmarked sessions for a specific user_id.
        """
        user_id = request.query_params.get('HF_id')

        # Validate the required data
        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch all sessions for the user
            sessions = ChatSession.objects.filter(user_id=user_id)

            # Fetch only sessions that are bookmarked
            bookmarks = Bookmark.objects.filter(session__in=sessions).select_related('session')
            
            # Prepare response data
            response_data = []
            for bookmark in bookmarks:
                session = bookmark.session
                session = bookmark.session
                first_message = ChatMessage.objects.filter(session=session).first()
                response_data.append({
                    "session_id": str(session.session_id),
                    "session_name": session.session_name,
                    "first_message": first_message.input_prompt if first_message else '',
                    "created_on": session.created_on,
                })

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Rename Session View
class RenameSessionAPIView(APIView):
    
    def patch(self, request):
        """
        Rename an existing chat session.
        """
        session_id = request.data.get('session_id')
        try:
            # Fetch the session
            session = ChatSession.objects.get(session_id=session_id)

            # Get the new name from the request body
            new_name = request.data.get("session_name")

            if not new_name:
                return Response({"detail": "Session name is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update the session name
            session.session_name = new_name
            session.save()

            # Serialize the updated session data
            serializer = ChatSessionSerializer(session)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ChatSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

class EvaluationAPIView(APIView):

    def get(self, request):
        # GET: Return all evaluations
        evaluations = Evaluation.objects.all()
        serializer = EvaluationSerializer(evaluations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # POST: Expect 'ques_id' in request.data
        ques_id = request.data.get('ques_id')
        if not ques_id:
            return Response({'error': 'ques_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        evaluation = Evaluation.objects.filter(ques_id=ques_id).first()

        if not evaluation:
            return Response({'error': 'No evaluation found for the given ques_id.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'score': evaluation.score}, status=status.HTTP_200_OK)