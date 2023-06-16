import requests
import asyncio
from EdgeGPT import Query, Chatbot, ConversationStyle
from threading import Thread

class AIManager:
    def __init__(self):
        self.message = None
        self.on_response = None

        self.chatbot = None

    def chat(self, message, on_response):
        #return requests.post(self.llm_url, json={"message": message}).text
        self.message = message
        self.on_response = on_response
        t = Thread(target=self.chat_threaded)
        t.start()


    def chat_threaded(self):
        print("chat")
        asyncio.run(self.chat_async())

    async def chat_async(self):
        if not self.chatbot:
            self.chatbot = await Chatbot.create()
        if self.message and self.on_response:
            response = await self.chatbot.ask(prompt=self.message, conversation_style=ConversationStyle.creative)
            self.on_response(response["item"]["messages"][1]["text"])
