# Author: Borghini Davide (DavideB45 on GitHub)
# This file is a heavily modified version of the original file. 
# The original file is located in the main directory of the repository and is called RAG.py.
# This is supposed to be more readable and easier to understand (since there are comments in the code).
# It is also supposed to be more modular and easier to use in the future.
import os
import sys
sys.path.append(os.path.abspath(os.path.join('..')))

from langchain_community.document_loaders import WebBaseLoader, TextLoader, UnstructuredXMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from StructuredOutput_simplified import KPIRequest ## line that gives error
from langchain_core.pydantic_v1 import Field
from operator import itemgetter
from typing import Literal
from typing_extensions import TypedDict

# Stuff for the routing
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_ollama import ChatOllama

# Stuff for document loading
from langchain_community.document_loaders import UnstructuredXMLLoader
from example_explainability import slowly_print

class Rag():
    def __init__(self, model):
        """
        During the initializzaiton load the choosen model
        and create the prompts that are going to be used to route the queries
        
        args:
         - model: the model that is going to be used to generate the responses (e.g. llama3.2)
        """
        self.model = ChatOllama(model=model)

        prompt_1 = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert on constructing queries with specific structures."),
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
        # explainable chain (use model KPI expert)
        self._chain_1 = prompt_1 | self.model.with_structured_output(KPIRequest) 
        # bunny chain (use only model knowledge + bunny expert)
        self._chain_2 = prompt_2 | self.model | StrOutputParser()
        # unexpected chain (tell the user that the model is not able to answer)
        self._chain_3 = prompt_3 | self.model | StrOutputParser()

        # Class that is going to be used to route the queries
        class RouteQuery(TypedDict):
            """Route query to destination."""
            destination: Literal["KPI Query Constructor", "Other expert"] = Field(description="choose between KPI query or other expert")
        route_system = "Which one of these experts is best suited to answer the query? the KPI query expert, or another expert? Just tell me the expert."
        route_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", route_system),
                ("human", "{query}"),
            ]
        )
        # The chain that is going to be used to route the queries
        route_chain = (
            route_prompt
            | self.model.with_structured_output(RouteQuery)
            | itemgetter("destination")
        )

        def get_dest(x):
            try:
                if "kpi" in x['destination'].lower():
                    return "KPI query constructor"
                else:
                    return "Other expert"
            except:
                return "Other expert"
            
        self._get_destination = {
            "destination": route_chain,  # "KPI query" or "bunny"
            "query": lambda x: x["query"],  # pass through input query
        } | RunnableLambda(
            # if KPI query, chain_1. otherwise, chain_2.
            lambda x: get_dest(x),
        )


    # This function should be changed when we have the possibility to access to the knowledge base
    def load_documents(self):
        '''
        Load the documents from the knowledge base
        For now we are using a local file that contains the documents

        return:
            - vectorstore: the vectorstore that contains the documents
        '''
        loader = UnstructuredXMLLoader("./kb.owl")
        self.loader = loader
        data = self.loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=0)
        all_splits = text_splitter.split_documents(data)
        local_embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.vectorstore = Chroma.from_documents(documents=all_splits, embedding=local_embeddings)
        return self.vectorstore


    def get_destination(self, query) -> str:
        """
        Get the destination of the query
        args:
         - query: the query that is going to be used to get the destination
        return:
            - the destination of the query (e.g. KPI Query Constructor, Bunny Expert)
        """
        return self._get_destination.invoke({"query": query})
    
    def explainableQuery(self, query:str, destination:str=None):
        """
        Generate the response for the query
        args:
         - query: the query that is going to be used to generate the response
         - destination: the destination of the query (e.g. KPI Query Constructor, Bunny Expert)
        return:
            - the response for the query
        """
        if destination == "KPI query constructor":
            print("Destination: KPI Query Constructor")
            answered = False
            for i in range(5):
                try:
                    answer:KPIRequest = self._chain_1.invoke({"query": query})
                    answered = True
                except:
                    continue
                if answered:
                    break
            if not answered:
                return "Error: The model is broken."
            answer = f"""Retrieving data of {answer.machine_names[0]}\n\
Selecting dates from {answer.start_date} to {answer.end_date}\n\
Using KPI calculation engine to compute {answer.aggregation}\n\
Formulating textual response"""
            slowly_print(answer)
            return "Example answer, from rag"
        print("Destination not found, general routing, destination:", destination)
        return "I am not able to answer this query"
