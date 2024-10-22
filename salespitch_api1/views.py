from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from .models import ChatSession, ChatMessage2 , History
from django.http import StreamingHttpResponse
from django.contrib.auth.models import User
import uuid
import asyncio
import re
from langchain_core.messages import HumanMessage, SystemMessage ,AIMessage
from .stream_structure_agent8 import ABHFL
from django.shortcuts import render



def my_view(request):
    return render(request, "index.html")
# Utility function to replace slashes with spaces
def replace_slashes(input_string: str) -> str:
    return re.sub(r'[\\/]', ' ', input_string)

# Utility function to iterate over async generator
def iter_over_async(ait, loop):
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

# New Chat API using CreateAPIView
class NewChatAPIView(generics.CreateAPIView):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer

    def post(self, request, *args, **kwargs):
        HF_email = request.data.get('HF_email')

        if not HF_email:
            return Response({"error": "HF_email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # user = get_object_or_404(User, email=HF_email)
        chat_session = ChatSession.objects.create(user_id=HF_email, session_id=str(uuid.uuid4()))
        serializer = self.get_serializer(chat_session)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

# Main Chat API using APIView
class ChatAPIView(APIView):
    serializer_class = ChatMessageSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # HF_email = serializer.validated_data.get('HF_email')
            session_id = serializer.validated_data.get('session').session_id
            message = serializer.validated_data.get('message')
            ques_id = serializer.validated_data.get('ques_id')
            answer = serializer.validated_data.get('answer', None)

            # user = get_object_or_404(User, email=HF_email)
            session = get_object_or_404(ChatSession,session_id=session_id)

            if answer:
                chat_message = ChatMessage2.objects.create(
                    session=session,
                    message=message,
                    ques_id=ques_id,
                    answer=answer
                )
                message_serializer = ChatMessageSerializer(chat_message)
                return Response({'status': 'Message saved successfully', 'message_id': message_serializer.data['ques_id']}, status=status.HTTP_201_CREATED)

            else:
                # previous_messages = ChatMessage.objects.filter(session=session).order_by('created_on')
                # Fetch or create chat history
                chat_history, created = History.objects.get_or_create(session = session)
                # Prepare the history in the desired format
                if created:
                    chat_history.messages = []
                # print(history)
                messages = chat_history.get_messages()
                bot_instance = ABHFL(messages)  # Placeholder for bot logic
                response_chunks = []

                def generate():
                    try:
                        if not bot_instance.message:
                            with open("prompts/main_prompt2.txt", "r", encoding="utf-8") as f:
                                text = f.read()
                            bot_instance.message.append(SystemMessage(content=text))
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        questions = replace_slashes(message)
                        openai_response = iter_over_async(bot_instance.run_conversation(questions.lower()), loop)

                        for event in openai_response:
                            kind = event["event"]
                            if kind == "on_chat_model_stream":
                                content = event["data"]["chunk"].content
                                if content:
                                    response_chunks.append(content)
                                    yield content

                        final_answer = "".join(response_chunks)
                        bot_instance.message.append(AIMessage(content=final_answer))
                        chat_history.set_messages(bot_instance.message)
                        chat_history.save()
                        # yield f"\n[Final Answer Saved for Ques ID: {ques_id}]"

                    except Exception as e:
                        yield f"Error: {str(e)}"

                response = StreamingHttpResponse(generate(), content_type="text/event-stream")
                response["Cache-Control"] = "no-cache"
                response["X-Accel-Buffering"] = "no"
                return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StoreChat(APIView):
    serializer_class = ChatMessageSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # HF_email = serializer.validated_data.get('HF_email')
            session_id = serializer.validated_data.get('session').session_id
            message = serializer.validated_data.get('message')
            ques_id = serializer.validated_data.get('ques_id')
            answer = serializer.validated_data.get('answer', None)
            # print(session_id)

            # Validate the input
            if not session_id or not message or not ques_id:
                return Response({'error': 'Invalid payload. session_id, message, and ques_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure the session exists
            # try:
            #     session = ChatSession.objects.get(session_id=session_id)
            # except ChatSession.DoesNotExist:
            #     return Response({'error': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Create or update the ChatMessage record
            chat_message, created = ChatMessage2.objects.update_or_create(
                session_id=session_id,
                ques_id=ques_id,
                defaults={
                    'message': message,
                    'answer': answer
                }
            )

            if created:
                status_message = 'Message saved successfully'
            else:
                status_message = 'Message updated successfully'

            return Response({'status': status_message, 'message_id': chat_message.ques_id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# History API
class HistoryAPIView(APIView):
    def post(self, request):
        HF_email = request.data.get('HF_email')
        session_id = request.data.get('session', None)

        if HF_email and not session_id:
            sessions = ChatSession.objects.filter(user_id=HF_email,is_activate=True).order_by("-created_on")
            response_data = []
            for session in sessions:
                first_message = ChatMessage2.objects.filter(session=session).first()
                response_data.append({
                    'sessionid': session.session_id,
                    'first_message': first_message.message if first_message else '',
                    'created_on' : first_message.created_on if first_message else ""
                })
            return Response(response_data, status=status.HTTP_200_OK)

        elif HF_email and session_id:
            try:
                session = ChatSession.objects.get(user_id=HF_email, session_id=session_id)
            except ChatSession.DoesNotExist:
                return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

            messages = ChatMessage2.objects.filter(session=session)
            response_data = []
            for message in messages:
                response_data.append({
                    'ques_id': message.ques_id,
                    'message': message.message,
                    'answer': message.answer,
                    'created_on': message.created_on
                })
            return Response(response_data, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        user_id = request.data.get('userid')
        session_id = request.data.get('sessionid', None)

        if user_id and session_id:
            try:
                session = ChatSession.objects.get(user_id=user_id, session_id=session_id)
                session.is_activate = False
                session.save()
                return Response({'status': 'Session Deleted Succefully'}, status=status.HTTP_204_NO_CONTENT)

            except ChatSession.DoesNotExist:
                return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
            
            
        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)

