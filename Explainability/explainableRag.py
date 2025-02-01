# Author: Borghini Davide (DavideB45 on GitHub)
# This file is a heavily modified version of the original file. 
# The original file is located in the main directory of the repository and is called RAG.py.
# This is supposed to be more readable and easier to understand (since there are comments in the code).
# It is also supposed to be more modular and easier to use in the future.
from datetime import datetime, timedelta
import os
import sys
import time

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
from StructuredOutput_simplified import ApiRequestCallTopic1, ApiRequestCallTopic8
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
                ("system", "You are an expert in identifying and analyzing KPIs. Your task is to understand the query and extract relevant details to construct a structured output. Focus on the KPI name, machine names, and time frame."),
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
        route_system = "Which one of these choice is the human query about? choose between: \n\
KPI request (example: what is the average usage of laser cutting machine, give me the max cost of X machine from Y, get X of all the machines),\n\
aplication (example: how do I get a KPI, how is implemented J),\n\
plot (where can I found the plot of X, plot the average of Y),\n\
'email or reports' (example write an email about that),\n\
food (examples: what is the menu, what is there for lunch),\n\
capability (example: what can you do, what are your capabilities),\n\
greetings (example: hello, who are you),\n\
else if not strictly related to the previous categories.\n\
Tell just the destination of the query."
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
                if "application" in x['destination'].lower() or "find" in x['destination'].lower() or "plot" in x['destination'].lower():
                    return "application"
                if "plot" in x['destination'].lower() or "graph" in x['destination'].lower():
                    return "plot"
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

    def close(self):
        self.printer.stop()

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
        explanation = 'explanation not yet available\n'
        if dest == "KPI request":
            explanation =  query_obj.explain_rag()
        elif dest == "food":
            explanation =  query_obj.explain_rag()
        elif dest == "application":
            explanation =  'Searching documents...\nFormulating answer...\n'
        elif dest == "capability":
            explanation = 'Explaining capabilities...\n'
        elif dest == "plot":
            explanation = 'Searching in documentation...\nFormulating answer...\n'
        elif dest == "email or reports":
            explanation = 'Understanding context...\nGenerating email or a report...\n'
        #TODO: handle general destinations 
        self.printer.add_string(explanation)
        return explanation
    
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
        if destination == "KPI request":
            self.printer.add_string("Generating KPI request...")
            for i in range(3):
                try:
                    request = self._chain_1.invoke({"query": query})
                    break
                except Exception as e:
                    if i == 2:
                        self.printer.add_and_wait("Unable to generate KPI request.")
                        return "..."
                    self.printer.add_string("...")
                    print(e)
                    continue
            explanation = self.explainRag(destination, request)
            api_response1, request = ApiRequestCallTopic1(request)
            api_response8 = ApiRequestCallTopic8(request)
            answer = self.direct_query(f"Answer the user query, be concise. The answer is {(api_response8*10):.2f} {api_response1.split("unit of measure: ")[1].split()[0]}. Format it as an answer", query)
        elif destination == "food":
            request:LunchRequest = self.chain_4.invoke({"query": query})
            if request.day.lower() == "today":
                request.day = datetime.today().strftime('%A').lower()
            elif request.day.lower() == "tomorrow":
                request.day = (datetime.today() + timedelta(days=1)).strftime('%A').lower()
            explanation = self.explainRag(destination, request)
            answer = get_menu_for(request.day.lower())
            query = f'What is on the menu for {request.day}? Aswer with all the options available.'
            answer = self.direct_query(answer, query)
        elif destination == "capability":
            explanation = self.explainRag(destination, None)
            answer = 'I can do a coupple of things:\n- I can answer queries about KPIs of the machines\n- I can tell you about mensa\'s menu\n- I can write emails/reports.\n I can answer queries about the general system\n'
        elif destination == "application":
            explanation = self.explainRag(destination, None)
            answer = 'I need to implement a RAG'
        elif destination == "plot":
            explanation = self.explainRag(destination, None)
            answer = 'I need to implement a RAG'
        elif destination == "email or reports":
            explanatino = self.explainRag(destination, None)
            answer = 'I need to implement a RAG'
        elif destination == "greetings":
            answer = 'Hello! I am the explainable chat.\nI am here to help you with your queries.'
        else:
            answer = 'I\'m sorry, I can\'t answer that.'
        
        time.sleep(0.1)
        self.printer.add_and_wait(answer)
        return answer