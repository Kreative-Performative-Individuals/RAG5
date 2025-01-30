# Author: Borghini Davide (DavideB45 on GitHub)
# This file is a heavily modified version of the original file. 
# The original file is located in the main directory of the repository and is called RAG.py.
# This is supposed to be more readable and easier to understand (since there are comments in the code).
# It is also supposed to be more modular and easier to use in the future.
from datetime import datetime
import os
import sys

from pydantic import BaseModel
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from web_searches.smensiamo import get_menu_for
sys.path.append(os.path.abspath(os.path.join('..')))

from langchain_community.document_loaders import WebBaseLoader, TextLoader, UnstructuredXMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from StructuredOutput_simplified import KPIRequest, LunchRequest, RouteQuery ## line that gives error
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
from example_explainability import slowly_print_load
from printer import ListPrinter

class Rag():
    def __init__(self, model):
        """
        During the initializzaiton load the choosen model
        and create the prompts that are going to be used to route the queries
        
        args:
         - model: the model that is going to be used to generate the responses (e.g. llama3.2)
        """
        self.model = ChatOllama(model=model)
        today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self.printer = ListPrinter()


        prompt_1 = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert on constructing queries with specific structures."),
                ("human", "{query}"),
            ]
        )
        prompt_2 = ChatPromptTemplate.from_messages(
            [
                ("system", f"""
                        You are an expert in identifying and analyzing KPI trends. Your task is to understand the query and extract relevant details to construct a structured output. 
                        - Focus on trends, patterns, or historical analysis of KPIs.
                        - Today's date is {today}, which should be considered as the default end date unless another specific date is provided.
                        - The system should intelligently decide on a reasonable start date for trend analysis when the user’s query doesn't explicitly specify a time frame. Assume the start date as the first day of the current month or year, as appropriate.
                        - The structured output should include the KPI name, machine names, start date, and end date.
                        """,),
                ("human", "{query}"),
            ]
        )
        prompt_3 = ChatPromptTemplate.from_messages(
            [ 
                ("system", "You must not answer the human query. Instead, tell them that you are not able to answer it."),
                ("human", "{query}"),
            ]
        )
        prompt_4 = ChatPromptTemplate.from_messages(
            [("system", f"Generate an output in the form day of week (mon, tue, wed, tue, fri, sat) and lunch or dinner; lunch is default if not specified"),
             ("human", "{query}")]
        )
        prompt_5 = ChatPromptTemplate.from_messages(
            [
                ("system", 'Anwer the user query. The actual answer is known ad it is: {context}.'),
                ("human", "{query}")
            ]
        )

        # chain for the lunch request
        self.chain_4 = prompt_4 | self.model.with_structured_output(LunchRequest)
        # explainable chain (use model KPI expert)
        self._chain_1 = prompt_1 | self.model.with_structured_output(KPIRequest)
        # show off chain (tell user what the model can do)
        self._chain_2 = prompt_2 | self.model | StrOutputParser() 
        # unexpected chain (tell the user that the model is not able to answer)
        self._chain_3 = prompt_3 | self.model | StrOutputParser()
        # general direct query
        self.chain_5 = prompt_5 | self.model | StrOutputParser()

        # Class that is going to be used to route the queries
        route_system = "Which one of these choice is the human query about? choose between: \
KPI request (example: what is the average usage of laser cutting machine),\
KPI trend (),\
'email or reports' (example write an email about that),\
food (examples: what is the menu, what is there for lunch),\
capability (example: what can you do, what are your capabilities),\
else if not strictly related to the previous categories."
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
                print(f'dest str = {x}')
                if "kpi" in x['destination'].lower():
                    return "KPI request"
                if "food" in x['destination'].lower() or "menu" in x['destination'].lower() or "lunch" in x['destination'].lower() or "dinner" in x['destination'].lower():
                    return "food"
                if "mail" in x['destination'].lower() or "report" in x['destination'].lower():
                    return "email or reports"
                if "capability" in x['destination'].lower() or ("can" in x['destination'].lower() and "do" in x['destination'].lower()) or "capabilities" in x['destination'].lower():
                    return "capability"
                else:
                    return "none"
            except:
                return "none"
            
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

    def direct_query(self, context:str, query:str):
        return self.chain_5.invoke({
            "context": context,
            "query": query
        })

    def get_destination(self, query) -> str:
        """
        Get the destination of the query
        Args:
            query (str): the query that is going to be used to get the destination
        Returns:
            the destination of the query (e.g. KPI Query Constructor, Bunny Expert)
        """
        for _ in range(3):
            dest = self._get_destination.invoke({"query": query})
            if dest != 'none':
                return  dest
        return 'none'
    
    def explainRag(self, dest:str, query_obj:BaseModel) -> str:
        if query_obj is not None:
            # KPI request or food
            if isinstance(query_obj, KPIRequest) or isinstance(query_obj, LunchRequest):
                return query_obj.explain_rag()
        if dest == "KPI request":
            return 'phrase to explain capability...\n'
        elif dest == "capability":
            return 'Explaining capabilities...\n'
        #TODO: handle general destinations 
        return 'explanation not yet available\n'
    
    def explainableQuery(self, query:str, destination:str=None):
        """
        Generate the response for the query
        args:
         - query: the query that is going to be used to generate the response
         - destination: the destination of the query (e.g. KPI Query Constructor, Bunny Expert)
        return:
            - the response for the query
        """
        request = None
        if destination == "KPI query":
            request:KPIRequest = self._chain_1.invoke({"query": query})
            self.printer.add_string(self.explainRag(destination, request))
            answer = 'to implement'
        elif destination == "food":
            request:LunchRequest = self.chain_4.invoke({"query": query})
            self.printer.add_string(self.explainRag(destination, request))
            answer = get_menu_for(request.day)
            query = f'What is on the menu for {request.day}? Aswer with all the options available.'
            answer = self.direct_query(answer, query)
        elif destination == "capability":
            self.printer.add_string(self.explainRag(destination, None))
            answer = 'I can do a copple of things:\n- I can answer queries about KPIs of the machines\n- I can tell you about mensa\'s menu\n- I can write emails/reports.'
        else:
            return 'unable to answer the query'
        return answer
        if destination == "KPI query constructor":
            print("Working on it...")
            answered = False
            for i in range(5):
                try:
                    
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
            slowly_print_load(answer)
            return "Example answer, from rag"
        elif destination == "Other expert":
            return "Sorry, I am not able to explain this query"
        elif destination == "food":
            print("Working on it...")
            answered = False
            for i in range(5):
                try:
                    answer:LunchRequest = self.chain_4.invoke({"query": query})
                    answered = True
                except:
                    continue
                if answered:
                    break
            if not answered:
                return "Error: The model is broken."
            print(f'Getting menu for {answer.day} {answer.meal}')
            answer = get_menu_for(answer.day, answer.meal == 'dinner')
            return answer

        #print("Destination not found, general routing, destination:", destination)
        return "Sorry, I am not able to answer this query"
