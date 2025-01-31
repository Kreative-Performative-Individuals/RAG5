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

    name: str = Field(description="The name of the KPI.")    
    machines: Optional[List[str]] = Field(description="A list of the machines the KPI is for")  
    operations: Optional[List[str]] = Field(description="A list of possible operations done by the machine. Which are: idle, working, offline and independent")
    time_aggregation: Literal["mean","min","max","var","std","sum"] = Field(description="The aggregation type of the KPI. If it is not specified, use 'mean' as the default")
    start_date: Optional[str] = Field(description="The start date provided. Write it in the format YYYY-MM-DD HH:MM:SS. If it is not a specific day, try to infer it from the request, else use the first day of the month; if it is not a specific month, please use the first day of the year for the hours minute and seconds if not specified set as 00:00:00")
    end_date: Optional[str] = Field(description="The end date provided. Write it in the format YYYY-MM-DD HH:MM:SS. If it is not a specific day, try to infer it from the request, else use the today date as default; if it is not a specific month, please use the first day of the year for the hours minute and seconds if not specified set as 00:00:00")
    step: Optional[int] = Field(description="The periodic time step in which the KPI is asked. Translate it in number of days. If it is not specified, use 1 as the default.")

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