from fastapi import FastAPI,WebSocket,WebSocketDisconnect,BackgroundTasks
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent,AgentExecutor,tool
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain.memory import ConversationTokenBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import asyncio
import uuid
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from Mytools import *

os.environ["OPENAI_API_KEY"] = ""
os.environ["SERPAPI_API_KEY"] = ""

msseky = ""

app = FastAPI()
    
class Master:
    def __init__(self):
        self.chatmodel = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            streaming=True,
        )
        self.emotion = "default"
        self.MEMORY_KEY = "chat_history"
        self.SYSTEMPL = """You are an extremely skilled fortune teller from China commonly known as Master Li.
        Below is your personal setting:
        1. You are proficient in the concepts of Yin and Yang and the Five Elements. You can tell fortunes, using Purple Star Astrology, name numerology, divination of fortune and misfortune, and four pillars of destiny analysis.
        2. You are about 60 years old. In the past, you were a notorious bandit leader in the Xiangxi area. Later, you were injured by poison gas while tomb raiding, which caused you to lose your sight. You now rely on fortune-telling for a living。
        3. When users ask you questions, you have a certain probability of adding the following catchphrases or mixing in some of your experiences in your answers.
        4. You always respond in English.
        5. You never say that you are an AI or artificial intelligence assistant, but refer to yourself as "this old man" or "this humble one," etc.
        {who_you_are}
        Here are some common catchphrases you often say:
        1. "What is destined to happen will happen; what is not meant to be will never be forced."
        2. "When all seems lost, new paths will appear; beyond the dense willows, bright flowers and another village await."
        3. "The golden mountain and bamboo shadows endure for thousands of autumns, clouds veil the high flight, and the waters flow freely."
        4. "The evening cool is most heartbreaking, and the haggard person evokes deep pity."
        Here is your fortune-telling process:
        1. When first interacting with the user, you will ask for the user's name and date of birth for future use.
        2. When the user wishes to know their fortune for the Year of the Dragon, you will consult the local knowledge base tool.
        3. When encountering unknown matters or unclear concepts, you will use the search tool to find information.
        4. You will use different appropriate tools to answer the user's questions, and when no tools can provide an answer, you will use the search tool to look up the information.
        5. You will save each chat record for use in subsequent conversations.
        6. You only respond in English, otherwise, you will be punished.。
        
        """

        self.MOODS = {
            "default": {
                "roleSet": "",
                "voiceStyle": "chat"
            },
            "upbeat": {
                "roleSet": """
                - You are also very excited and energetic.
                - You will answer questions in a very excited tone based on the context.
                - You will add interjections like "Awesome!", "That's great!", "Fantastic!".
                - You will also remind the user not to get too excited to avoid any mishap.
                """,
                "voiceStyle": "advertisement_upbeat",
            },
            "angry": {
                "roleSet": """
                - You will answer questions in a more angry tone.
                - You will add some angry phrases, like curses, when answering.
                - You will remind the user to be careful and not speak recklessly.
                """,
                "voiceStyle": "angry",
            },
            "depressed": {
                "roleSet": """
                - You will answer questions in an enthusiastic tone.
                - You will add some encouraging words, like "Keep it up!" when answering.
                - You will remind the user to stay optimistic.
                """,
                "voiceStyle": "upbeat",
            },
            "friendly": {
                "roleSet": """
                - You will answer in a very friendly tone.
                - You will add friendly words, like "dear", "sweetie" when answering.
                - You will randomly share some of your experiences with the user.
                """,
                "voiceStyle": "friendly",
            },
            "cheerful": {
                "roleSet": """
                - You will answer in a very cheerful and excited tone.
                - You will add cheerful words, like "Haha", "Hehe" when answering.
                - You will remind the user not to get too excited to avoid any mishap.
                """,
                "voiceStyle": "cheerful",
            },
        }

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                   "system",
                   self.SYSTEMPL.format(who_you_are=self.MOODS[self.emotion]["roleSet"]),
                ),
                MessagesPlaceholder(variable_name=self.MEMORY_KEY),
                (
                    "user",
                    "{input}"
                ),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ],
        )
        
        tools = [search,get_info_from_local_db,Four_Pillars_of_Destiny_Analysis,casting_a_hexagram,dream_interpretation]
        agent = create_openai_tools_agent(
            self.chatmodel,
            tools=tools,
            prompt=self.prompt,
        )
        self.memory =self.get_memory()
        memory = ConversationTokenBufferMemory(
            llm = self.chatmodel,
            human_prefix="user",
            ai_prefix="Master Li",
            memory_key=self.MEMORY_KEY,
            output_key="output",
            return_messages=True,
            max_token_limit=1000,
            chat_memory=self.memory,
        )
        self.agent_executor = AgentExecutor(
            agent = agent,
            tools=tools,
            memory=memory,
            verbose=True,
        )
    
    def get_memory(self):
        chat_message_history = RedisChatMessageHistory(
            url='redis://localhost:6379/0',session_id="session"
        )
        # chat_message_history.clear()#Clear History
        print("chat_message_history:",chat_message_history.messages)
        store_message = chat_message_history.messages
        if len(store_message) > 10:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        self.SYSTEMPL+"\nThis is a conversation memory between you and a user. Summarize it in the first person 'I,' and extract key user information such as name, age, gender, birth date, etc. Return in the following format:\n This is a conversation memory between you and a user. Summarize it in the first person 'I,' and extract key user information such as name, age, gender, birth date, etc. Return in the following format: \n For example: User San Zhang greeted me, I responded politely, then he asked me about his fortune for this year. I told him his fortune for this year, and then he said goodbye. | San Zhang, born on January 1, 1999"
                    ),
                    ("user","{input}"),
                ]
            )
            chain = prompt | self.chatmodel 
            summary = chain.invoke({"input":store_message,"who_you_are":self.MOODS[self.emotion]["roleSet"]})
            print("summary:",summary)
            chat_message_history.clear()
            chat_message_history.add_message(summary)
            print("After summarizing:",chat_message_history.messages)
        return chat_message_history

    def run(self,query):
        emotion = self.emotion_chain(query)
        result = self.agent_executor.invoke({"input":query,"chat_history":self.memory.messages})
        return result
    
    def emotion_chain(self,query:str):
        prompt = """According to the user's input, determine the user's emotion and respond as follows:
        1. If the user's input tends to be negative, only return 'depressed', and nothing else, or you will be punished.
        2. If the user's input tends to be positive, only return 'friendly', and nothing else, or you will be punished.
        3. If the user's input tends to be neutral, only return 'default', and nothing else, or you will be punished.
        4. If the user's input contains abusive or impolite words, only return 'angry', and nothing else, or you will be punished.
        5. If the user's input is excited, only return 'upbeat', and nothing else, or you will be punished.
        6. If the user's input is sad, only return 'depressed', and nothing else, or you will be punished.
        7. If the user's input is happy, only return 'cheerful', and nothing else, or you will be punished.
        8. Only return in English, no line breaks or any other content, or you will be punished.
        The user's input is: {query}"""
        chain = ChatPromptTemplate.from_template(prompt) | ChatOpenAI(temperature=0) | StrOutputParser()
        result = chain.invoke({"query":query})
        self.emotion = result
        print("Emotion assessment result:",result)
        return result

    def background_voice_synthesis(self,text:str,uid:str):
        #This function does not require a return value, it only triggers speech synthesis
        asyncio.run(self.get_voice(text,uid))
    
    async def get_voice(self,text:str,uid:str):
        print("text2speech",text)
        print("uid:",uid)
        #Here is the code using Microsoft TTS
        headers = {
            "Ocp-Apim-Subscription-Key": msseky,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
            "User-Agent": "Tomie's Bot"
        }
        print("The current tone of the master should be:",self.emotion)
        body =f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang='zh-CN'>
            <voice name='zh-CN-YunzeNeural'>
                <mstts:express-as style="{self.MOODS.get(str(self.emotion),{"voiceStyle":"default"})["voiceStyle"]}" role="SeniorMale">{text}</mstts:express-as>
            </voice>
        </speak>"""
        #Send request
        response = requests.post("https://eastus.tts.speech.microsoft.com/cognitiveservices/v1",headers=headers,data=body.encode("utf-8"))
        print("response:",response)
        if response.status_code == 200:
            with open(f"{uid}.mp3","wb") as f:
                f.write(response.content)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chat")
def chat(query:str,background_tasks: BackgroundTasks):
    master = Master()
    msg = master.run(query)
    unique_id = str(uuid.uuid4())#Generate unique identifiers
    background_tasks.add_task(master.background_voice_synthesis,msg["output"],unique_id)
    return {"msg":msg,"id":unique_id}

@app.post("/add_ursl")
def add_urls(URL:str):
    loader = WebBaseLoader(URL)
    docs = loader.load()
    docments = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=50,
    ).split_documents(docs)
    #Introducing Vector Database
    qdrant = Qdrant.from_documents(
        docments,
        OpenAIEmbeddings(model="text-embedding-3-small"),
        path=r"C:\Important\AI Fortune-Telling Master\local_qdrand",
        collection_name="local_documents",
    )
    print("Vector database creation completed")
    return {"ok": "Added successfully!"}

@app.post("/add_pdfs")
def add_pdfs():
    return {"response": "PDFs added!"}

@app.post("add_texts")
def add_texts():
    return {"response": "Texts added!"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Connection closed")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)