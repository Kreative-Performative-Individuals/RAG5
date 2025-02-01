# Author: Borghini Davide (DavideB45 on GitHub)
# A copy of the file contained in the main directory
# The file include a simplified version of the KPIRequest class 
# in order to be easier to use for a RAG model
# Since the class is simplified, it is not possible to use it to make API calls
import json
from typing_extensions import TypedDict
from typing import Literal, List
from typing import Optional
from langchain_core.pydantic_v1 import BaseModel, Field
from datetime import datetime


class RouteQuery(TypedDict):
    """Route query to destination."""
    destination: Literal[
         "KPI request",
         "KPI trend", 
         "email or reports", 
         "food",
         "capability",
         "else"] = Field(
         description="choose between: \
KPI request (example: what is the average usage of laser cutting machine),\
KPI trend (),\
'email or reports' (example write an email about that),\
food (examples: what is the menu, what is there for lunch),\
capability (example: what can you do, what are your capabilities),\
else if not strictly related to the previous categories"
)



class KPIRequest(BaseModel):
    """
    KPIRequest class. Used to generate a request to the KPI engine, based on the user query,
    through langchain_ollama.with_structured_output() method.

    Attributes:
        - name: str 
        - machines: Optional[List[str]]
        - time_aggregation: Literal["mean","min","max","var","std","sum"]
        - start_date: Optional[str] 
        - end_date: Optional[str]
        - step: Optional[int]
    Methods:
        - to_json
        - explain_rag: returns a string that explains the KPI request inferred by the model.

    """

    name: str = Field(description="The name of the KPI. (example: energy consumption, temperature, etc.)")    
    machines: Optional[str] = Field(description="A list of the machines if no machine is specified use the empty list (example: [Laser Machine, Cutting Machine], [Laser machine], etc.)")  
    operations: Optional[List[str]] = Field(description="A list of possible operations done by the machine. Which are: idle, working, offline and independent. if not specified use [idle, working, offline].)")
    time_aggregation: Literal["mean","min","max","var","std","sum"] = Field(description="The aggregation type of the KPI. If it is not specified, use 'mean' as the default")
    start_date: Optional[str] = Field(description="The start date provided. Write it in the format YYYY-MM-DD HH:MM:SS. If it is not a specific day, try to infer it from the request, else use the first day of the month; if it is not a specific month, please use the first day of the year for the hours minute and seconds if not specified set as 00:00:00")
    end_date: Optional[str] = Field(description="The end date provided. Write it in the format YYYY-MM-DD HH:MM:SS. If it is not a specific day, try to infer it from the request, else use the today date as default; if it is not a specific month, please use the first day of the year for the hours minute and seconds if not specified set as 00:00:00")

    def to_json(self):
           return json.dumps(self,default=lambda o: o.__dict__, sort_keys=False, indent=4)

    def explain_rag(self):
        '''
        This function returns a string that explains the KPI request.
        It can be used as an explanation for the user of what the model is doing
        and what the model understands from the input.
        returns: a string that explains the KPI request in a human-readable way
        '''
        return f"Retrieving data of {'All machines' if len(self.machines) == 0 else self.machines}\n\
Searching for KPI: {self.name}\n\
Selecting dates from {self.start_date} to {self.end_date}\n\
Using KPI calculation engine to compute {self.time_aggregation}\n\
Formulating textual response\n"
    
class LunchRequest(BaseModel):
    today = datetime.today().strftime('%A').lower()
    
    #day: str = Field(description=f"The day of the week. (mon,tue,wed,thu,fri,sat), today is ({today})")
    day: Literal["mon","tue","wed","thu","fri","sat"] = Field(description=f"The day of the week. (mon,tue,wed,thu,fri,sat), today is ({today})")

    def explain_rag(self):
        '''
        return a string explaining the query
        '''
        return f'Downloading the menu...\nSearching for {self.day}...\nGetting lunch informations...\n'

################################################################################
################################ API CALLS #####################################
################################################################################
import requests
import json
import random

KPI_ENGINE_URL = "http://kpi-engine:8008"
KB_URL = "http://kb-service:8001"

def ApiRequestCallTopic8(obj:KPIRequest, random_response:bool=True):
    """
    Function used to call the KPI engine and receive a response, which contain the query's desired result.
    obj is an object of the class KPIRequest, while the result is a numerical value.
    """
    if random_response:
        return random.random()
    data = obj
    response = requests.post(f"{KPI_ENGINE_URL}/kpi/", data=json.dumps(data, default=lambda o: o.__dict__, sort_keys=False, indent=4))
    response = json.loads(response.content)
    result = response["value"]
    return result

def ApiRequestCallTopic1(obj:KPIRequest, random_response:bool=True):
    """
    Function used to call the Knowledge Base and receive a couple response, obj. 
    The input obj is an instance of the class KPIRequest, while the output obj is an adjusted version
    by exploiting the informations in the KB. Response is a string of informations about the 
    query's KPIs and machines, which are useful for the RAG to generate a full response.
    """
    if random_response:
        unit_of_measure = ""
        description = "description not available"
        if obj.name == "energy consumption":
            unit_of_measure = "kWh"
            description = "The energy consumption is the amount of energy consumed by the machine in a specific time frame."
        elif obj.name == "temperature":
            unit_of_measure = "°C"
            description = "The temperature is the measure of the heat of the machine in a specific time frame."
        elif obj.name == "pressure":
            unit_of_measure = "Pa"
            description = "The pressure is the force applied to the machine in a specific time frame."
        elif "good" in obj.name.lower():
            unit_of_measure = obj.name.lower()
            description = f"The good parts are the number of {unit_of_measure} produced by the machine in a specific time frame."
        response = "kpi label: " + obj.name + "\n" + "kpi description: " + description + "\n" + "kpi unit of measure: " + unit_of_measure + "\n"
        for i in range(len(obj.machines)):
            response = response + "machine label: " + obj.machines[i] + "\n" + "machine description: description not available\n"
        return response, obj
    ## WORKING CODE:
    request = requests.get(f"{KB_URL}/object-properties", params={"label": obj.name})
    request = json.loads(request.text)
    obj.name = request["properties"]["label"]
    response = "kpi label: " + request["properties"]["label"] + "\n" + "kpi description: " + request["properties"]["description"]
    try:
        response = response + "\nkpi unit of measure: " + request["properties"]["unit_of_measure"] +"\n"
    except Exception as e:
        print(e)
    
    try:
        for i in range(len(obj.machines)):
            request = requests.get(f"{KB_URL}/object-properties", params={"label": obj.machines[i]})
            request = json.loads(request.content)
            obj.machines[i] = request["properties"]["label"]
            response = response + "machine label: " + request["properties"]["label"] + "\n" + "machine description: " + request["properties"]["description"]
    except Exception as e:
        print(e)
    
    return response, obj