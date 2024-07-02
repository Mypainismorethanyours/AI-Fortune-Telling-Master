from langchain.agents import create_openai_tools_agent,AgentExecutor,tool
from langchain_openai import ChatOpenAI,OpenAI
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_core.output_parsers import JsonOutputParser
import requests
import json

YUANFENJU_API_KEY = ""

@tool
def test():
    """Test tool"""
    return "test"

@tool
def search(query:str):
    """Only use this tool when you need to know real-time information or when you encounter unknown matters."""
    serp = SerpAPIWrapper()
    result = serp.run(query)
    print("Real-time search results are:",result)
    return result

@tool
def get_info_from_local_db(query:str):
    """Only use this tool when answering questions related to the fortune for the year 2024 or the Year of the Dragon, and you must input the user's birth date."""
    client = Qdrant(
        QdrantClient(path=r"C:\Important\AI Fortune-Telling Master\local_qdrand"),
        "local_documents",
        OpenAIEmbeddings(model="text-embedding-3-small"),
    )
    retriever = client.as_retriever(search_type="mmr")
    result = retriever.get_relevant_documents(query)
    return result


@tool
def Four_Pillars_of_Destiny_Analysis(query:str):
    """Only use this tool when doing Ba Zi (Four Pillars of Destiny Analysis) analysis, requiring the user's name and birth date. If the user's name and birth date are missing, the tool cannot be used."""
    url = f"https://api.yuanfenju.com/index.php/v1/Bazi/cesuan"
    prompt = ChatPromptTemplate.from_template(
        """You are a parameter query assistant. Based on the user's input, find the relevant parameters and return them in JSON format. The JSON fields are as follows: -"api_key":"c8fpdqnZFfhgmMO6s2pJrcDkc", - "name":"name", - "sex":"gender, 0 represents male, 1 represents female, determined by name", - "type":"Calendar type, 0 lunar calendar, 1 Gregorian calendar, default to 1", - "year":"Birth year, example: 1998", - "month":"month of birth, example: 8", - "day":"date of birth, example: 8", - "hours":"Birth hour, example: 14", - "minute":"0"，If the relevant parameters are not found, the user needs to be reminded to tell you these contents, only return the data structure, and do not have any other comments. The user inputs:{query}""")
    parser = JsonOutputParser()
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    chain = prompt | ChatOpenAI(temperature=0) | parser
    data = chain.invoke({"query":query})
    print("Four Pillars of Destiny Analysis Result:",data)
    result = requests.post(url,data=data)
    if result.status_code == 200:
        print("====Returned data=====")
        print(result.json())
        try:
            json = result.json()
            returnstring = "Four Pillars of Destiny Analysis are:"+json["data"]["bazi_info"]["bazi"]
            return returnstring
        except Exception as e:
            return "Four Pillars of Destiny Analysis failed, possibly because you forgot to ask for the user's name or birth date."
    else:
        return "Technical error, please tell the user to try again later."
    

@tool
def casting_a_hexagram():
    """Only use this tool when the user wants to draw lots for divination."""
    api_key = YUANFENJU_API_KEY
    url = f"https://api.yuanfenju.com/index.php/v1/Zhanbu/yaogua"
    result = requests.post(url,data={"api_key":api_key})
    if result.status_code == 200:
        print("====Returned data=====")
        print(result.json())
        returnstring = json.loads(result.text)
        image = returnstring["data"]["image"]
        print("Hexagram:",image)
        return  returnstring
    else:
        return "Technical error, please tell the user to try again later."
    
@tool
def dream_interpretation(query:str):
    """Only use this tool when the user wants dream interpretation, requiring the content of the user's dream. If the content of the user's dream is missing, the tool cannot be used."""
    api_key = YUANFENJU_API_KEY
    url =f"https://api.yuanfenju.com/index.php/v1/Gongju/zhougong"
    LLM = OpenAI(temperature=0)
    prompt = PromptTemplate.from_template("Extract one keyword based on the content, only return the keyword (need to be translated into Chinese). The content is:{topic}")
    prompt_value = prompt.invoke({"topic":query})
    keyword = LLM.invoke(prompt_value)
    print("Extracted keywords:",keyword)
    result = requests.post(url,data={"api_key":api_key,"title_zhougong":keyword})
    if result.status_code == 200:
        print("====Returned data=====")
        print(result.json())
        returnstring = json.loads(result.text)
        return [item for item in returnstring['data'][:5]]
    else:
        return "Technical error, please tell the user to try again later."