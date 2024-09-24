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
from .stream_structure_agent7 import ABHFL
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
    # serializer_class = ChatSerializer
    
    def post(self, request, *args, **kwargs):
        
        if 'user_id' not in request.session:
            request.session['user_id'] = generate_user_id()
            request.session['last_activity'] = datetime.datetime.now().isoformat()

        session_id = request.session['user_id']
        if session_id not in chat_history:
            chat_history[session_id] = []
        # print(chat_history)
        bot_instance = ABHFL(chat_history[session_id])
       
        data_str = request.body
        data_str = data_str.decode('utf-8')
        # If the operation expects a file-like object, wrap the string in io.StringIO
        data_file_like = io.StringIO(data_str)
        try:
            data =  json.load(data_file_like)
            print(data["question"])
            chunks = []
            question =  data["question"]
        except JSONDecodeError as e:
            return JsonResponse({"error": f"Invalid JSON: {e}"}, status=400)

        def generate():
            # print(data["question"])
            try:    
                if len(bot_instance.message) == 0:
                    with open(f"prompts/main_prompt2.txt", "r", encoding="utf-8") as f:
                        text = f.read()
                # print(text)
                # ob1.message.append(SystemMessage(content=f"{text}"))
                # bot_instance.message.clear()
                    bot_instance.message.append(SystemMessage(content=f"{text}"))
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                openairesponse = iter_over_async(bot_instance.run_conversation(question), loop)
                # openairesponse = ob1.run_conversation(prompt)
                # Yield response
                for event in openairesponse:
                    kind = event["event"]
                    if kind == "on_chain_start":
                        if event["name"] == "Agent":
                            print(f"Starting agent: {event['name']} with input: {event['data'].get('input')}")
                    elif kind == "on_chain_end":
                        if event["name"] == "Agent":
                            print()
                            print("--")
                            print(f"Done agent: {event['name']} with output: {event['data'].get('output')['output']}")
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            print(content, end="|")
                            chunks.append(content)
                            yield content
                    elif kind == "on_tool_start":
                        print("--")
                        print(f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}")
                    elif kind == "on_tool_end":
                        print(f"Done tool: {event['name']}")
                        print(f"Tool output was: {event['data'].get('output')}")
                        print("--")
                    # return Response({'responce': f"{chunks}"})
                answer = "".join(chunks)
                # response = bot_instance.run_conversation(question)
                
                response_output = answer

                bot_instance.message.append(AIMessage(content=f"{response_output}"))
                chat_history[session_id] = bot_instance.message
            # return Response({'response': response_output}, status=status.HTTP_200_OK)
        # except Exception as e:
        #         return Response({'error': f"An error occurred: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        # else:
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                    yield JsonResponse({"error": str(e)}, status=500)

        return StreamingHttpResponse(generate(), content_type="application/json")



    