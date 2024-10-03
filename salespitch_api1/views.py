from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets, status
from rest_framework.response import Response
# from .models import Chat
from .models import ChatSession, ChatMessage
from .serializers import ChatMessageSerializer , ChatSessionSerializer
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from .stream_structure_agent8 import ABHFL
from langchain_core.messages import HumanMessage, SystemMessage ,AIMessage
import os
from django.http import FileResponse , HttpResponse
# from .langchain_retrival import answer_question_from_chunk

from django.http import StreamingHttpResponse
import json
import uuid
import datetime
import asyncio
from json.decoder import JSONDecodeError

def my_view(request):
    return render(request, "index.html")

def iter_over_async(ait, loop):
    ait = ait.__aiter__()
    async def get_next():
        try: obj = await ait.__anext__(); return False, obj
        except StopAsyncIteration: return True, None
    while True:
        done, obj = loop.run_until_complete(get_next())
        if done: break
        yield obj



class NewChatAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatSessionSerializer
    def post(self, request, ip=None):
        serializer = ChatSessionSerializer(data=request.data)
        if serializer.is_valid():
            ip = ip or serializer.validated_data['ip']

            if not ip:
                return Response({"error": "ip is required"}, status=status.HTTP_400_BAD_REQUEST)

            chat_session = ChatSession.objects.create(ip=ip)
            serializer = ChatSessionSerializer(chat_session)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

def generate_user_id():
        return str(uuid.uuid4())
    
# bot_instance = ABHFL()
import io
chat_history = {}
class ChatAPIView(APIView):

    def post(self, request, *args, **kwargs):
        # Use request.data to parse the incoming JSON request automatically
        data = request.data

        # Check for existing user session, or create a new one
        session_id = data.get("session_id")
        if not session_id:
            return JsonResponse({"error": "Missing session_id in request"}, status=400)

        if 'user_id' not in request.session or request.session['user_id'] != session_id:
            request.session['user_id'] = session_id

            # Create ChatSession if it doesn't exist
            if not ChatSession.objects.filter(session_id=session_id).exists():
                ChatSession.objects.create(session_id=session_id)

            # Update session activity
            request.session['last_activity'] = datetime.datetime.now().isoformat()

        session_id = request.session['user_id']
        chat_session = ChatSession.objects.get(session_id=session_id)

        # Initialize chat history for the session
        if session_id not in chat_history:
            chat_history[session_id] = []

        # Initialize the bot instance
        bot_instance = ABHFL(chat_history[session_id])

        # Parse the incoming question from the data
        question = data.get("question")
        if not question:
            return JsonResponse({"error": "Missing question in request"}, status=400)

        def generate():
            chunks = []
            try:
                # Load the initial prompt if the bot instance has no message history
                if not bot_instance.message:
                    with open(f"prompts/main_prompt2.txt", "r", encoding="utf-8") as f:
                        text = f.read()
                    bot_instance.message.append(SystemMessage(content=text))

                # Create event loop and process the conversation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                openairesponse = iter_over_async(bot_instance.run_conversation(question), loop)

                # Stream the AI's responses chunk by chunk
                for event in openairesponse:
                    kind = event["event"]
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            chunks.append(content)
                            yield content

                # Combine all chunks into the final answer
                answer = "".join(chunks)
                bot_instance.message.append(AIMessage(content=answer))
                chat_history[session_id] = bot_instance.message

                # Store the chat message in the database
                ChatMessage.objects.create(
                    session=chat_session,
                    message=question,
                    answer=answer
                )

            except Exception as e:
                yield JsonResponse({"error": str(e)}, status=500)

        # Return a streaming response
        response = StreamingHttpResponse(generate(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"  # Prevent client caching
        response["X-Accel-Buffering"] = "no"  # Enable streaming over NGINX
        try:
            return response

        except Exception as e:
            return JsonResponse({"error": f"Database Error: {str(e)}"}, status=500)



    