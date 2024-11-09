from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from .models import ChatSession, ChatMessage, History
from django.http import StreamingHttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import uuid
import asyncio
import re
from langchain_core.messages import SystemMessage, AIMessage
from .stream_structure_agent8 import ABHFL


# Render the main page
def my_view(request):
    return render(request, "index.html")


# Utility function to replace slashes with spaces
def replace_slashes(input_string: str) -> str:
    return re.sub(r"[\\/]", " ", input_string)


# Utility function to iterate over async generator
async def iter_over_async(ait):
    async for event in ait:
        yield event


# API to create a new chat session
class NewChatAPIView(generics.CreateAPIView):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer

    def post(self, request, *args, **kwargs):
        HF_email = request.data.get("HF_email")
        if not HF_email:
            return Response(
                {"error": "HF_email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        chat_session = ChatSession.objects.create(
            user_id=HF_email, session_id=str(uuid.uuid4())
        )
        return Response(
            self.get_serializer(chat_session).data, status=status.HTTP_201_CREATED
        )


# Main chat handling API
# Optimized ChatAPIView for generating and streaming bot responses without storing data
class ChatAPIView(APIView):
    serializer_class = ChatMessageSerializer

    def post(self, request):
        # Deserialize incoming data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            session_id = serializer.validated_data.get("session").session_id
            message = serializer.validated_data.get("input_prompt")
            ques_id = serializer.validated_data.get("ques_id")
            print(serializer)
            # Retrieve the session, if not found return error
            session = get_object_or_404(ChatSession, session_id=session_id)

            # Handle bot interaction if no answer is provided
            chat_history, created = History.objects.get_or_create(session=session)
            messages = chat_history.get_messages() if not created else []
            bot_instance = ABHFL(messages)

            def generate():
                try:
                    # Add system message to the bot instance if not already set
                    if not bot_instance.message:
                        with open(
                            "prompts/main_prompt2.txt", "r", encoding="utf-8"
                        ) as f:
                            bot_instance.message.append(SystemMessage(content=f.read()))

                    # Preprocess the question message (replace slashes in the message)
                    questions = replace_slashes(message)
                    openai_response = iter_over_async(
                        bot_instance.run_conversation(questions.lower())
                    )

                    response_chunks = []
                    for event in openai_response:
                        if event["event"] == "on_chat_model_stream":
                            content = event["data"]["chunk"].content
                            if content:
                                response_chunks.append(content)
                                yield content

                    # Collect the final answer from the bot
                    final_answer = "".join(response_chunks)
                    bot_instance.message.append(AIMessage(content=final_answer))

                    # Optionally, update chat history with the generated message, but do not store it
                    chat_history.set_messages(bot_instance.message)
                    chat_history.save()

                except Exception as e:
                    yield f"Error: {str(e)}"

            # Stream the response to the client
            response = StreamingHttpResponse(
                generate(), content_type="text/event-stream"
            )
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
            session_id = serializer.validated_data.get("session").session_id
            message = serializer.validated_data.get("input_prompt")
            ques_id = serializer.validated_data.get("ques_id")
            answer = serializer.validated_data.get("output", None)
            feedback = serializer.validated_data.get("feedback", None)
            input_prompt_timestamp = serializer.validated_data.get(
                "input_prompt_timestamp", None
            )
            output_timestamp = serializer.validated_data.get("output_timestamp", None)
            feedback = serializer.validated_data.get("feedback", None)
            select_feedback_response = serializer.validated_data.get(
                "select_feedback_response", None
            )
            additional_comments = serializer.validated_data.get(
                "additional_comments", None
            )

            # Validate required fields
            if not all([session_id, message, ques_id]):
                return Response(
                    {
                        "error": "Invalid payload. session_id, message, and ques_id are required."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update or create the message in the database
            chat_message, created = ChatMessage.objects.update_or_create(
                session_id=session_id,
                ques_id=ques_id,
                defaults={
                    "input_prompt": message,
                    "output": answer,
                    "input_prompt_timestamp": input_prompt_timestamp,
                    "output_timestamp": output_timestamp,
                    "feedback": feedback,
                    "select_feedback_response": select_feedback_response,
                    "additional_comments": additional_comments,
                },
            )

            status_message = (
                "Message saved successfully"
                if created
                else "Message updated successfully"
            )
            return Response(
                {"status": status_message, "message_id": chat_message.ques_id},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# History API to retrieve or delete chat session data
class HistoryAPIView(APIView):
    def post(self, request):
        HF_email = request.data.get("HF_email")
        session_id = request.data.get("session", None)

        if HF_email and not session_id:
            sessions = ChatSession.objects.filter(
                user_id=HF_email, is_activate=True
            ).order_by("-created_on")
            response_data = []

            for session in sessions:
                # Retrieve the first message for each session
                first_message = ChatMessage.objects.filter(session=session).first()

                # Build response data for each session
                response_data.append(
                    {
                        "sessionid": session.session_id,
                        "first_message": (
                            first_message.input_prompt if first_message else ""
                        ),
                        "created_on": first_message.created_on if first_message else "",
                    }
                )

            return Response(response_data, status=status.HTTP_200_OK)

        elif HF_email and session_id:
            try:
                session = ChatSession.objects.get(
                    user_id=HF_email, session_id=session_id
                )
            except ChatSession.DoesNotExist:
                return Response(
                    {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                )

            messages = ChatMessage.objects.filter(session=session)
            response_data = [
                {
                    "ques_id": message.ques_id,
                    "message": message.input_prompt,
                    "answer": message.output,
                    "created_on": message.created_on,
                }
                for message in messages
            ]
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request):
        user_id = request.data.get("userid")
        session_id = request.data.get("sessionid", None)

        if user_id and session_id:
            try:
                session = ChatSession.objects.get(
                    user_id=user_id, session_id=session_id
                )
                session.is_activate = False
                session.save()
                return Response(
                    {"status": "Session deleted successfully"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            except ChatSession.DoesNotExist:
                return Response(
                    {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                )

        return Response(
            {"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST
        )
