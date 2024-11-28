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
from pydantic.v1 import BaseModel, Field
from operator import itemgetter
from typing import Literal
from langchain_core.output_parsers import PydanticOutputParser


from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableMap
from langchain_ollama import ChatOllama
import json
import dateutil

from datetime import datetime
import time
from function_api import ApiRequestCallTopic8, ApiRequestCallTopic1

 
import numpy as np
class Rag():
    def __init__(self, model):
        today = datetime.today().strptime(datetime.today().strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
        self.model = ChatOllama(model=model, base_url="ollama:11434")
        self.routing_chain: str = ''
        self.examples = [
                
                {
                    "query": "Can you calculate Machine Utilization Rate of Assembly Machine 1 for yesterday?",
                    "output": json.dumps({
                "name": "utilization_rate",
                "machines": ["Assembly Machine 1"],
                "operations": [],
                "time_aggregation": "mean",
                "start_date": (today - dateutil.relativedelta.relativedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                "end_date": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                "step": 1
                })
                },

                {
                    "query": "Can you calculate the mean of machine usage of all the machines in state idle the previous month to today?",
                    "output": json.dumps({
                        "name": "machine_usage_trend",
                        "machines": [],
                        "operations": ["idle"],
                        "time_aggregation": "mean",
                        "start_date": (today - dateutil.relativedelta.relativedelta(months=1)).strftime('%Y-%m-%d %H:%M:%S'),
                        "end_date": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                        "step": 1
                    })
                },

                {
                    "query": "Calculate the maximum Machine Usage for Laser Welding Machine 1 for today, when idle.",
                    "output": json.dumps({
                "name": "machine_usage_trend",
                "machines": ["Laser Welding Machine 1"],
                "operations": ["idle"],
                "time_aggregation": "max",
                "start_date": (today - dateutil.relativedelta.relativedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                "end_date": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                "step": 1
                    })
                },



                {
                        "query": "Calculate for the last 2 weeks, the total Cost Per Unit of Laser Welding Machine 2",
                        "output": json.dumps({
                    "name": "cost_per_unit",
                    "machines": ["Laser Welding Machine 2"],
                    "operations": [],
                    "time_aggregation": "sum",
                    "start_date": (today - dateutil.relativedelta.relativedelta(weeks=2)).strftime('%Y-%m-%d %H:%M:%S'),
                    "end_date":  datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                    "step": 1
                    })
                },



                {
                    "query": "How much did we spend in the last month?",
                    "output": json.dumps({
                "name": "cost",
                "machines": [],
                "operations": [],
                "time_aggregation": "sum",
                "start_date": (today - dateutil.relativedelta.relativedelta(month=1)).strftime('%Y-%m-%d %H:%M:%S'),
                "end_date": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                "step": 1 
                })
                },


                {
                    "query": "What is the bi-daily standard deviation of all cutting machines consumption in 2023?",
                    "output": json.dumps({
                "name": "energy_consumption",
                "machines": ["Cutting Machine"],
                "operations": [],
                "time_aggregation": "std",
                "start_date": "2023-01-01 00:00:00",
                "end_date": "2023-12-31 00:00:00",
                "step": 2
                    })
                },



                {
                        "query": "What is mean success rate of all medium capacity cutting machines when working, in 2024?",
                        "output": json.dumps({
                    "name": "success_rate",
                    "machines": [
                        "Medium Capacity Cutting Machine 1",
                        "Medium Capacity Cutting Machine 2",
                        "Medium Capacity Cutting Machine 3"
                    ],
                    "operations": [
                        "working",
                        "working",
                        "working"
                    ],
                    "time_aggregation": "mean",
                    "start_date": "2024-01-01 00:00:00",
                    "end_date": "2024-12-31 00:00:00",
                    "step": 1
                        })
                },
                ]
        self.result = None
        
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


    
    def classify_query(self, query):
        
        prompt = ChatPromptTemplate.from_template(template="""
        Classify the user query choosing between the following categories:
        - KPI calculation: if the user explicitly wants to calculate a particular KPI, or asks for consumption or expenditure
        - e-mail or reports: if the user explicitly asks to write an email or a report 
        - else: if not strictly related to the previous categories

        Query: "{query}"

        Your classification (just return the category name):
        """)
        chain = prompt | self.model | StrOutputParser()
        response = chain.invoke({"query": query})
        print(type(response))
        return response


    def routing(self, destination, previous_answer):
        """
        Returns a callable chain that can be directly invoked.
        """
        today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        
        example_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", "{query}"),
                ("ai", "{output}"),
            ]                                         
        )                                             

        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=self.examples,
        )

        parser = PydanticOutputParser(pydantic_object=KPIRequest)

        prompt_1 = ChatPromptTemplate.from_messages(
            [("system", f"You are an expert on constructing queries with specific structures. {today} should be considered as the default end date unless another end date is specified."),
             few_shot_prompt,
             ("human", "{query}")]
        )
        
        prompt_2 = ChatPromptTemplate.from_messages(
            [("system", f"You are an expert on KPIs, machines and possible operations. You are also an expert on write emails and reports if the user explicitly requests it use {previous_answer} as message history to help you to write the email or the report. Remember that today is {today}."),
             ("human", "{query}")]
        )
        prompt_3 = ChatPromptTemplate.from_messages(
            [("system", f"You must not answer the human query. Instead, tell them that you are not able to answer it. Remember that today is {today}."),
             ("human", "{query}")]
        )
        prompt_4 = ChatPromptTemplate.from_messages(
            [("system", f"Generate the output in a tabular format with columns for {{kpi_name}}, {{machine_op_pairs}}, and {{aggregation}}."),
             ("human", "{query}")]
        )
     
        prompt_5 = ChatPromptTemplate.from_messages(
            [
                    (
                        "system",
                        f"""
                        You are an expert in identifying and analyzing KPI trends. Your task is to understand the query and extract relevant details to construct a structured output. 
                        - Focus on trends, patterns, or historical analysis of KPIs.
                        - Today's date is {today}, which should be considered as the default end date unless another specific date is provided.
                        - The system should intelligently decide on a reasonable start date for trend analysis when the user’s query doesn't explicitly specify a time frame. Assume the start date as the first day of the current month or year, as appropriate.
                        - The structured output should include the KPI name, machine names, start date, and end date.
                        """,
                    ),
                    ("human", "{query}")
                ])
        chain_1 = prompt_1 | self.model | parser
        chain_2 = prompt_2 | self.model | StrOutputParser()
        chain_3 = prompt_3 | self.model | StrOutputParser()
        chain_4 = prompt_4 | self.model.with_structured_output(KPITrend)
        chain_5 = prompt_5 | self.model.with_structured_output(KPITrend)

         
        def route_query(destination):
            # category = self.classify_query(query)  # Classify the query
            print("destination",destination)
            if destination == "KPI calculation":
                return chain_1
            elif destination == "e-mail or reports":
                return chain_2
            elif destination == "tabular":
                return chain_4
            elif destination == "KPI trend":
                return chain_5
            else:
                return chain_3

        
        return RunnableLambda(lambda inputs: route_query(destination))
    
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
    
    def explain_reasoning(self, dest:str=None, object:BaseModel=None):
        '''
        This function is used to explain the reasoning behind the model's decision
        Three asterisks (***) are appended to the end of the explanation for easier parsing
        Args:
            dest: The destination of the query (which "category" the query belongs to)
            object: The object that the model created to call an API (KPIRequest, KPITrend, etc.)
        Returns:
            A string showing what the model understood in a human-readable format
        '''
        expl = ""# The explanation string
        if dest == None and object == None:
            expl = "The model is answring based on his knowledge."
        elif object != None:
            if isinstance(object,KPIRequest):
                expl = object.explain_rag()
            elif isinstance(object,KPITrend):
                expl = object.explain_rag()
        elif dest == 'e-mail or reports':
            expl = "The model is generating an email/report\n"
        return expl + "***"

    # Function for follow-up discussions
    def follow_up(self, kpi_name, result, machine_op_pairs, aggregation, start_date, end_date, docs, user_input,history):

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
            Conversation history: {history}
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
            "history": "\n".join(history)
        }
        follow_up_response = follow_up_prompt_template | self.model | StrOutputParser()
        return follow_up_response.invoke(prompt_data)
    
    def conversation(self, KPI_engine_request, result, docs):
        pairs = list(zip(
            getattr(KPI_engine_request, "machine_names", [""]),
            getattr(KPI_engine_request, "operation_names", [""])
        ))
        explanation = self.explain_kpi_result(
            kpi_name=getattr(KPI_engine_request, "name", ""),
            machine_op_pairs=pairs,
            aggregation=getattr(KPI_engine_request, "aggregation", ""),
            start_date=getattr(KPI_engine_request, "start_date", ""),
            end_date=getattr(KPI_engine_request, "end_date", ""),
            result=result,
            docs=docs
        )
        self.history.append(explanation)
        print(f"\n\n>>>result explanation: {explanation}\n")

        while True:
            user_input = input("\n\n>>>Do you have any further question?\n\n>>>")
            if user_input.lower() in ["no", "end", "stop", "exit", "nah", "nope", "n"]:
                print("Session ended.")
                break
            
            self.history.append(f"User Input: {user_input}")
            # Follow-up response
            follow_up_response = self.follow_up(
                kpi_name=getattr(KPI_engine_request, "name", ""),
                result=result,
                machine_op_pairs=pairs,
                aggregation=getattr(KPI_engine_request, "aggregation", ""),
                start_date=getattr(KPI_engine_request, "start_date", ""),
                end_date=getattr(KPI_engine_request, "end_date", ""),
                docs=docs,
                user_input=user_input,
                history=self.history
            )
            self.history.append(follow_up_response)
            print(f"{follow_up_response}\n")
            #time.sleep(0.5)

    def compute_query(self, obj):
        if isinstance(obj,KPIRequest):

            docs, obj = ApiRequestCallTopic1(obj)
            print(obj)
            return docs, ApiRequestCallTopic8(obj)
        else:
            return obj
    

    def direct_query(self, obj, docs, result, query, previous_answer):
        """
        Directly query the model
        """
        print(obj)
        print(result)
        pairs = list(zip(
            getattr(obj, "machines", [""]),
            getattr(obj, "operations", [""])
        ))
        prompt = ChatPromptTemplate.from_template(
            template=f"""
            The user has requested further discussion about the KPI analysis. Based on the context:
            - KPI Name: {obj.name}
            - Machines-Operations pairs: {pairs}
            - Aggregation: {obj.time_aggregation}
            - Start date: {obj.start_date}
            - End date: {obj.end_date}
            - KPI Value: {result}
            - Docs: {docs}

            The user said: "{query}"
            Conversation history: {previous_answer}
            Generate a detailed follow-up response. Offer actionable insights or ask clarifying questions to continue the discussion. And the response should contain no more than 300 words
            """
        )
        chain = prompt | self.model | StrOutputParser()
        return chain.invoke({"query":query})

    def run(self, query):
        try:
            destination = self.classify_query(query)
            KPI_engine_query = self.routing(destination).invoke({"query": query})
            print(KPI_engine_query)
            print(KPI_engine_query)
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