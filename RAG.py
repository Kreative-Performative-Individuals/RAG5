# Authors: Marco Dell'Acqua, Nazifa Mosharrat, Alice Nicoletta 
# 
# The file includes a version of the Rag class and all of its methods
#

from langchain_community.document_loaders import WebBaseLoader, TextLoader, UnstructuredXMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from StructuredOutput import KPIRequest, KPITrend, RouteQuery
from pydantic.v1 import Field
from operator import itemgetter
from typing import Literal

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableMap
from langchain_ollama import ChatOllama

from datetime import datetime
import time

class Rag():
    def __init__(self, model):
        self.model = ChatOllama(model=model)
        self.routing_chain: str = ''

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # This function should be changed when we have the possibility to access to the knowledge base

    def load_documents(self,path):
        self.loader = UnstructuredXMLLoader(path)
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
                ("system", "You are an expert on constructing queries with specific structures. {today} is the last possible day to consider."),
                ("human", "{query}"),
            ]
        )
        prompt_2 = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert on bunnies. Remember that today is {today}."),
                ("human", "{query}"),
            ]
        )

        prompt_3 = ChatPromptTemplate.from_messages(
            [ 
                ("system", "You must not answer the human query. Instead, tell them that you are not able to answer it. Remember that today is {today}."),
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


        route_chain = (
            route_prompt
            | self.model.with_structured_output(RouteQuery)
            | itemgetter("destination")
        )

        today_date = (
            RunnablePassthrough()
            | RunnableLambda(lambda x: datetime.today().strftime('%d/%m/%Y'))
        )
        
        chain = RunnableMap({
            "destination": route_chain,  # "KPI query" or "bunny"
            "query": lambda x: x["query"],  # pass through input query
            "today": today_date,
        }) | RunnableLambda(
            # if KPI query, chain_1. otherwise, chain_2...
            lambda x: chain_1 if x["destination"] == "KPI query" else chain_2 if x["destination"] == "bunny" else chain_4 if x["destination"] == "KPI trend" else chain_3,
        )

        return chain
    
    def get_model(self):
        return self.model
    
    # explanation for KPI result
    def explain_kpi_result(self, kpi_name, machine_op_pairs, aggregation, start_date, end_date, result, docs):
        dynamic_explanation_prompt = ChatPromptTemplate.from_template(template="""
        Based on the following inputs, generate a detailed and natural language explanation:
        - KPI Name: {kpi_name}
        - Machines-Operations pairs: {machine_op_pairs}
        - Aggregation: {aggregation}
        - Start date: {start_date}
        - End date: {end_date}
        - KPI Value: {result}
        - Docs: {docs}

        Generate an explanation as if explaining to a user who asked a relevant question. Be clear, concise, and informative. And the response should contain no more than 300 words
        """)
        prompt_data = {
            "kpi_name": kpi_name,
            "machine_op_pairs": machine_op_pairs,
            "aggregation": aggregation,
            "start_date": start_date,
            "end_date": end_date,
            "result": result,
            "docs": docs,
        }

        explanation = dynamic_explanation_prompt | self.model | StrOutputParser()
        return explanation.invoke(prompt_data)
    
    # Function for follow-up discussions
    def follow_up(self, kpi_name, result, machine_op_pairs, aggregation, start_date, end_date, docs, user_input):

        # Prompt template for follow-up query
        follow_up_prompt_template = ChatPromptTemplate.from_template(
            template="""
            The user has requested further discussion about the KPI analysis. Based on the context:
            - KPI Name: {kpi_name}
            - Machines-Operations pairs: {machine_op_pairs}
            - Aggregation: {aggregation}
            - Start date: {start_date}
            - End date: {end_date}
            - KPI Value: {result}
            - Docs: {docs}

            The user said: "{user_input}"

            Generate a detailed follow-up response. Offer actionable insights or ask clarifying questions to continue the discussion. And the response should contain no more than 300 words
            """
        )

        prompt_data = {
            "kpi_name": kpi_name,
            "machine_op_pairs": machine_op_pairs,
            "aggregation": aggregation,
            "start_date": start_date,
            "end_date": end_date,
            "result": result,
            "docs": docs,
            "user_input": user_input,
        }
        follow_up_response = follow_up_prompt_template | self.model | StrOutputParser()
        return follow_up_response.invoke(prompt_data)
    
    def conversation(self, KPI_engine_request, result, docs):
        pairs = list(zip(KPI_engine_request.machine_names, KPI_engine_request.operation_names))
        explanation = self.explain_kpi_result(
            kpi_name=KPI_engine_request.name,
            machine_op_pairs=pairs,
            aggregation=KPI_engine_request.aggregation,
            start_date=KPI_engine_request.start_date,
            end_date=KPI_engine_request.end_date,
            result=result,
            docs=docs
        )
        print(f"\n\n>>>result explanation: {explanation}\n")

        while True:
            user_input = input("\n\n>>>Do you have any further question?\n\n>>>")
            if user_input.lower() in ["no", "end", "stop", "exit", "nah", "nope", "n"]:
                print("Session ended.")
                break

            # Follow-up response
            follow_up_response = self.follow_up(
                kpi_name=KPI_engine_request.name,
                result=result,
                machine_op_pairs=pairs,
                aggregation=KPI_engine_request.aggregation,
                start_date=KPI_engine_request.start_date,
                end_date=KPI_engine_request.end_date,
                docs=docs,
                user_input=user_input
            )
            print(f"{follow_up_response}\n")
            time.sleep(0.5)

    def run(self, query):
        try:
            KPI_engine_query = self.routing().invoke({"query": query})
            #KPI_engine_query is supposed to be sent to the KPI engine here, so we can compute the result
            result = "0.75 kWh" #dummy result
            self.load_documents("./KB_original.owl")
            docs=self.vectorstore.similarity_search(query=query, k=10)
            self.conversation(KPI_engine_query, result, docs)   
        except Exception as e:
            print(e)
            return "Error: The model is broken."
        #TODO: for the next milestone, generalize the run function using only the routing function or integrate the follow_up function into the routing function

if __name__ == "__main__":
    rag = Rag("llama3.2")
    query = input(">>>Enter your query:\n\n>>>")
    rag.run(query)