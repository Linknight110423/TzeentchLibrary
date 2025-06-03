from ollama import chat
from ollama import ChatResponse

response: ChatResponse = chat(model='deepseek-r1:1.5b', messages=[
    {
        'role': 'user',
        'content': 'Why is the sky blue?',
    },

])

# or access fields directly from the response object
print(response.message.content)
