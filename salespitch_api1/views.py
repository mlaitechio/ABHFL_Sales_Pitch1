from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ChatSession, ChatMessage
from .serializers import ChatMessageSerializer, ChatSessionSerializer
from .stream_structure_agent5 import ABHFL
from langchain_core.messages import SystemMessage, AIMessage
import json
import uuid
import io
import datetime

# View to render the index page
def my_view(request):
    return render(request, "index.html")

# Helper function to generate a unique user ID
def generate_user_id():
    return str(uuid.uuid4())

chat_history = {}
# View to handle chat interactions and create a new session on each call
class ChatAPIView(APIView):
    
    def post(self, request, *args, **kwargs):
        # Generate a new session ID and create a new chat session
        
        
        if 'user_id' not in request.session:
            request.session['user_id'] = generate_user_id()
            # session_id = request.session['user_id']
            request.session['last_activity'] = datetime.datetime.now().isoformat()
            
        # Initialize bot instance and chat history for the session
        session_id = request.session['user_id']
        chat_session = ChatSession.objects.get_or_create(session_id=session_id)
        print(chat_session)
        if session_id not in chat_history:
            chat_history[session_id] = []
        # print(chat_history)
        bot_instance = ABHFL(chat_history[session_id])
        

        try:
            # Parse request data
            data_str = request.body.decode('utf-8')
            data_file_like = io.StringIO(data_str)
            data = json.load(data_file_like)

            question = data.get("question")
            if not question:
                return Response({'error': 'Question is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Load the initial system message if it's the first interaction
            if len(bot_instance.message) == 0:
                with open("prompts/main_prompt2.txt", "r", encoding="utf-8") as f:
                    initial_prompt = f.read()
                    bot_instance.message.append(SystemMessage(content=initial_prompt))

            # Process the question and generate a response
            response_output = bot_instance.run_conversation(question)

            # Save the question and response in the chat history
            bot_instance.message.append(AIMessage(content=response_output))
            chat_history[session_id] = bot_instance.message

            # Store the chat message in the database
            ChatMessage.objects.create(
                session=chat_session[0],
                message=question,
                answer=response_output
            )

            # Return the response
            return Response({'response': response_output}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': f"An error occurred: {e}"}, status=status.HTTP_400_BAD_REQUEST)
