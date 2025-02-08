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

from langchain_community.document_loaders import UnstructuredXMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
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
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
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
        self.model = ChatOllama(model=model, temperature=0.8)
        self.today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self.printer = ListPrinter()
        vectorstore = Chroma(persist_directory="/home/d.borghini/Documents/GitHub/RAG5/Explainability/vectorstore",
                     embedding_function=OllamaEmbeddings(model="llama3.1:8b"))

        self.retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 7, 'fetch_k': 19}
        )
        self.past_answer = ''
        self.past_query = ''
        self.past_conversation = []


        prompt_1 = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert in identifying and analyzing KPIs. Your task is to understand the query and extract relevant details to construct a structured output. Focus on the KPI name, machine names, and time frame."),
                ("human", "{query}"),
            ]
        )
        prompt_2 = ChatPromptTemplate.from_messages(
            [
                ("system", f"""You are an ai assistant asked to generate an email or a report based on the following conversation""",),
                ("human", "{past_query}"),
                ("ai", "{past_answer}"),
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
        prompt_6 = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a knowledgeable AI assistant. You are asked to translate the last answer in another language."),
                ("human", "{past_query}"),
                ("ai", "{past_answer}"),
                ("human", "{query}")
            ]
        )

        # chain for the lunch request
        self.chain_4 = prompt_4 | self.model.with_structured_output(LunchRequest)
        # explainable chain (use model KPI expert)
        self._chain_1 = prompt_1 | self.model.with_structured_output(KPIRequest)
        # mail/report chain (use model mail/report and the past conversation)
        self._chain_2 = prompt_2 | self.model | StrOutputParser() 
        # unexpected chain (tell the user that the model is not able to answer)
        self._chain_3 = prompt_3 | self.model | StrOutputParser()
        # general direct query
        self.chain_5 = prompt_5 | self.model | StrOutputParser()
        # translation chain
        self.chain_6 = prompt_6 | self.model | StrOutputParser()

        # Class that is going to be used to route the queries
        route_system = "Which one of these choice is the human query about? choose between: \n\
KPI request (example: average usage of laser cutting machine, give me the max cost of X machine from Y),\n\
aplication (example: how do I get a KPI, what are the system requirements, what is a x machine, what is a finantial KPI, ai featues...),\n\
plot (where can I found the plot of X, plot the average of Y),\n\
'email or reports' (example write an email about that),\n\
translation (example: translate the last answer),\n\
food (examples: what is the menu, what is there for lunch),\n\
capability (pick this only if question is very similar to: what can you do),\n\
greetings (example: hello, who are you,),\n\
else if not strictly related to the previous categories or you don't know which one is correct.\n\
Tell just the destination of the query."
        route_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", 'You are an AI assistant inside a web application for industry 5.0 that uses various AI technologies. The app mainly allow the user to keep track of important KPI, machine usage etc. You are asked to route the query to the correct topic.'),
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
                #print(f'dest str = {x}')
                if "kpi" in x['destination'].lower():
                    return "KPI request"
                if "food" in x['destination'].lower() or "menu" in x['destination'].lower() or "lunch" in x['destination'].lower() or "dinner" in x['destination'].lower():
                    return "food"
                if "mail" in x['destination'].lower() or "report" in x['destination'].lower():
                    return "email or reports"
                if "capability" in x['destination'].lower() or ("can" in x['destination'].lower() and "do" in x['destination'].lower()) or "capabilities" in x['destination'].lower():
                    return "capability"
                if "application" in x['destination'].lower() or "find" in x['destination'].lower():
                    return "application"
                if "plot" in x['destination'].lower() or "graph" in x['destination'].lower():
                    return "plot"
                if "transl" in x['destination'].lower() or "tradu" in x['destination'].lower():
                    return "translation"
                else:
                    return "general"
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

    def reset(self):
        self.past_answer = ''
        self.past_query = ''
        self.past_conversation = []

    def direct_query(self, context:str, query:str):
        answer = ''
        for chunk in self.chain_5.stream({"context": context, "query": query}):
            answer += chunk
            self.printer.print_chunk(chunk=chunk)
        return answer

    def get_destination(self, query) -> str:
        """
        Get the destination of the query
        Args:
            query (str): the query that is going to be used to get the destination
        Returns:
            the destination of the query (e.g. KPI Query Constructor, Bunny Expert)
        """
        self.printer.add_string("Understanding subject of the message...")
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
        elif dest == "capability":
            explanation = 'Explaining capabilities...\n'
        elif dest == "plot" or dest == "application":
            explanation = 'Retrieving Documents...\nSearching in documentation...\nFormulating answer...\n'
        elif dest == "email or reports":
            explanation = 'Understanding context...\nGenerating email or report...\nFormulating answer...\n'
        elif dest == "translation":
            explanation = 'Analyzing past answer...\nTranslating conversation...\nFormulating answer...\n'
        elif dest == "general":
            explanation = 'Analyzing query...\nFormulating answer...\n'
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
        answer = ''
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
            query = f'What is on the menu for {request.day}? Aswer with all the options available. (Be short but use emoji)'
            answer = self.direct_query(answer, query)
        elif destination == "capability":
            explanation = self.explainRag(destination, None)
            answer = 'I can do a coupple of things:\n- I can answer queries about KPIs of the machines\n- I can tell you about mensa\'s menu\n- I can write emails/reports.\n- I can answer queries about the general system\n'
            self.printer.add_and_wait(answer)
        elif destination == "application":
            explanation = self.explainRag(destination, None)
            answer = self.knowledge_based_query(query)
        elif destination == "plot":
            explanation = self.explainRag(destination, None)
            answer = 'I need to implement a RAG'
        elif destination == "email or reports":
            explanation = self.explainRag(destination, None)
            #answer = self._chain_2.invoke({"query": query, "past_query": self.past_query, "past_answer": self.past_answer})
            answer = self.chat_based_query(query)
        elif destination == "translation":
            explanation = self.explainRag(destination, None)
            #answer = self.chain_6.invoke({"query": query, "past_query": self.past_query, "past_answer": self.past_answer})
            for chunk in self.chain_6.stream({"query": query, "past_query": self.past_query, "past_answer": self.past_answer}):
                #self.printer.add_and_wait(chunk)
                answer += chunk
                self.printer.print_chunk(chunk=chunk)
        elif destination == "general":
            explanation = self.explainRag(destination, None)
            answer = self.chat_based_query(query)
        else:
            answer = 'I\'m sorry, I can\'t answer that.'
        
        self.past_answer = answer
        self.past_query = query
        self.past_conversation.append(("human", query))
        self.past_conversation.append(("ai", answer))
        return answer
    
    def knowledge_based_query(self, query:str) -> str:
        """
        Generate the response for the query
        args:
         - query: the query that is going to be used to generate the response
        return:
            - the response for the query based on documents available to the user
        """
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=(
                "You are a knowledgeable AI assistant. Use the provided context to answer the question. (be short)\n\n"
                "Context:\n{context}\n\n"
                "Question: {question}\n\n"
                "Answer:"
            )
        )
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Retrieve documents separately
        retrieved_docs = self.retriever.invoke(query)
        context = format_docs(retrieved_docs)

        rag_chain = (
            {"context": lambda _:context, "question": RunnablePassthrough()}  # Use the retrieved context
            | prompt
            | self.model
            | StrOutputParser()
        )

        "What are the system requirements?"
        answer = ''
        for chunk in rag_chain.stream({"question": query.capitalize()}):
            answer += chunk
            self.printer.print_chunk(chunk=chunk)
        return answer
    
    def chat_based_query(self, query:str) -> str:
        """
        Generate the response for the query based on the conversation with the user
        args:
         - query: the query that is going to be used to generate the response
        return:
            - the response for the query based on the conversation with the user
        """
        context_based_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an AI assistant (a chatbot) inside a web application for industry 5.0 that uses various AI technologies. The app mainly allow the user to keep track of important KPI, machine usage etc..."),
                ("system", f"Your name is FabbriBot from 'fabbrica' and 'robot' and today is {self.today}"),
                ("system", "You are asked to continue the conversation with the user. Answer to the last message. (don't be too long)"),
                *self.past_conversation,
                ("human", "{query}"),
            ]
        )
        context_based_chain = context_based_prompt | self.model | StrOutputParser()
        answer = ''
        for chunk in context_based_chain.stream({"query": query}):
            answer += chunk
            self.printer.print_chunk(chunk=chunk)
        return answer