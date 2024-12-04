# Authors: Marco Dell'Acqua, Nazifa Mosharrat, Alice Nicoletta 
# 
# The file contains all the classes for constructing any request used by the other groups 
#
from typing_extensions import TypedDict
from typing import Literal, List
from typing import Optional
from pydantic.v1 import BaseModel, Field
import json


class RouteQuery(TypedDict):
            """Route query to destination."""
            destination: Literal["KPI request","KPI trend", "email or reports","else"] = Field(description="choose between KPI request which is about the calculation of the KPI, KPI trend which is about the trend of a particular KPI, 'email or reports' which is about writing an email or a report about a particular KPI or else if not strictly related to the previous categories")


class KPIRequest(BaseModel):
    name: str = Field(description="The name of the KPI.")    
    machines: Optional[List[str]] = Field(description="A list of the machines the KPI is for")  
    operations: Optional[List[str]] = Field(description="A list of possible operations done by the machine. Which are: idle, working, offline and independent")
    time_aggregation: Literal["mean","min","max","var","std","sum"] = Field(description="The aggregation type of the KPI. If it is not specified, use 'mean' as the default")
    start_date: Optional[str] = Field(description="The start date provided. Write it in the format YYYY-MM-DD HH:MM:SS. If it is not a specific day, try to infer it from the request, else use the first day of the month; if it is not a specific month, please use the first day of the year for the hours minute and seconds if not specified set as 00:00:00")
    end_date: Optional[str] = Field(description="The end date provided. Write it in the format YYYY-MM-DD HH:MM:SS. If it is not a specific day, try to infer it from the request, else use the today date as default; if it is not a specific month, please use the first day of the year for the hours minute and seconds if not specified set as 00:00:00")
    step: Optional[int] = Field(description="The periodic time step in which the KPI is asked. Translate it in number of days. If it is not specified, use 1 as the default.")

    def to_json(self):
           return json.dumps(self,default=lambda o: o.__dict__, sort_keys=False, indent=4)

    def to_string(self):
           return "name: " + str(self.name) + "\nmachine_names: " + self.machine_names.__str__() +"\noperation_names: " + self.operation_names.__str__() + "\naggregation: " + str(self.aggregation) + "\nstart date: " + str(self.start_date) + "\nend date: " + str(self.end_date) + "\nstep: " + str(self.step)

class KPITrend(BaseModel):
    name: str = Field(description="The name of the KPI")
    machine_names: List[str] = Field(description="A list of the machines the KPI is for")
    start_date: Optional[str] = Field(description="The start date provided. Write it in the format DD/MM/YY. If it is not a specific day, try to infer it from the request, else use the first day of the month; if it is not a specific month, please use the first day of the year")
    end_date: Optional[str] = Field(description="Today's date written in the format DD/MM/YY.")


#TODO: inside this file we can write all the possibile Structured Output useful for Topic 3
