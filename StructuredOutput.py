
# inside this file we can write all the possibile Structured Output useful for Topic 3 or 8

from typing_extensions import TypedDict
from typing import Literal, List
from typing import Optional
from langchain_core.pydantic_v1 import BaseModel, Field

class RouteQuery(TypedDict):
            """Route query to destination."""
            destination: Literal["KPI query","KPI trend", "bunny","else"] = Field(description="choose between KPI query construnctor, KPI trend, bunny expert or else if not strictly related to the previous categories")


class KPIRequest(BaseModel):
    name: str = Field(description="The name of the KPI")    
    machine_names: List[str] = Field(description="A list of the machines the KPI is for")  
    operation_names: List[str] = Field(description="A list of possible operations done by the machine. Which are: idle, working, offline and independent")
    aggregation: Literal["mean","min","max","var","std","sum"] = Field(description="The aggregation type of the KPI. If it is not specified, use 'mean' as the default")
    start_date: Optional[str] = Field(description="The start date provided. Write it in the format DD/MM/YY. If it is not a specific day, try to infer it from the request, else use the first day of the month; if it is not a specific month, please use the first day of the year")
    end_date: Optional[str] = Field(description="The end date provided. Write it in the format DD/MM/YY. If it is not a specific day, try to infer it from the request, else use the first day of the month; if it is not a specific month, please use the first day of the year")
    step: int = Field(description="The periodic time step in which the KPI is asked. Translate it in number of days. If it is not specified, use -1 as the default.")

class KPITrend(BaseModel):
    name: str = Field(description="The name of the KPI")
    machine_names: List[str] = Field(description="A list of the machines the KPI is for")
    start_date: Optional[str] = Field(description="The start date provided. Write it in the format DD/MM/YY. If it is not a specific day, try to infer it from the request, else use the first day of the month; if it is not a specific month, please use the first day of the year")
    end_date: Optional[str] = Field(description="Today's date written in the format DD/MM/YY.")