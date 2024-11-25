from langchain_community.document_loaders import WebBaseLoader, TextLoader, UnstructuredXMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from StructuredOutput import KPIRequest, KPITrend
from langchain_core.pydantic_v1 import Field
from operator import itemgetter
from typing import Literal
from typing_extensions import TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_ollama import ChatOllama

from datetime import datetime

class Rag():
    def __init__(self, model):
        self.model = ChatOllama(model=model)


    # This function should be changed when we have the possibility to access to the knowledge base

    def load_documents(self, loader):
        self.loader = loader
        data = self.loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=0)
        all_splits = text_splitter.split_documents(data)
        local_embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.vectorstore = Chroma.from_documents(documents=all_splits, embedding=local_embeddings)
        return self.vectorstore


    def routing(self):
        
        today = datetime.today().strftime('%d/%m/%Y')
        prompt_1 = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert on constructing queries with specific structures. Remember that today is {today}."),
                ("human", "{query}"),
            ]
        )
        prompt_2 = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert on bunnies."),
                ("human", "{query}"),
            ]
        )

        prompt_3 = ChatPromptTemplate.from_messages(
            [ 
                ("system", "You must not answer the human query. Instead, tell them that you are not able to answer it."),
                ("human", "{query}"),
            ]
        )

        
        chain_1 =  prompt_1 | self.model.with_structured_output(KPIRequest) 
        chain_2 = prompt_2 | self.model | StrOutputParser()
        chain_3= prompt_3 | self.model | StrOutputParser()
        chain_4 = prompt_1 | self.model.with_structured_output(KPITrend)

        route_system = "Route the user's query to one of these: the KPI query constructor, the bunny expert, or 'else' if not strictly related to them."
        route_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", route_system),
                ("human", "{query}"),
            ]
        )


        class RouteQuery(TypedDict):
            """Route query to destination."""
            destination: Literal["KPI query","KPI trend", "bunny","else"] = Field(description="choose between KPI query construnctor, KPI trend, bunny expert or else if not strictly related to the previous categories")


        route_chain = (
            route_prompt
            | self.model.with_structured_output(RouteQuery)
            | itemgetter("destination")
        )

        chain = {
            "destination": route_chain,  # "KPI query" or "bunny"
            "query": lambda x: x["query"],  # pass through input query
        } | RunnableLambda(
            # if KPI query, chain_1. otherwise, chain_2...
            lambda x: chain_1 if x["destination"] == "KPI query" else chain_2 if x["destination"] == "bunny" else chain_4 if x["destination"] == "KPI trend" else chain_3,
        )

        return chain
    
    def get_model(self):
        return self.model
