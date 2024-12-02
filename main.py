from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from RAG import Rag
import time

class Message(BaseModel):
    message: str
    def set_message(self, message: str):
        return message
    

class BotResponse(BaseModel):
    response: str
    def set_response(self, response: str):
        return response

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Startup tasks (if any)
    pass

@app.get("/")
def root():
    return {"message": "Rag"}

async def calculate_response(user_message: str) -> str:
    # Call whatever needed to calculate the response.
    return interactive_chat(user_message)

# , response_model=BotResponse as second argument of this function
@app.post("/chat/", response_model=BotResponse)
#If the message is a Message object it returns error 422 but if it is a str it works
def chat_with_bot(text: str):
    try:
        bot_reply = interactive_chat(text)
        return {"response": bot_reply}
    except Exception as e:
        return {"response": str(e)}

# Aggiungere il ciclo for per gestire gli errori sulla costruzione delle KPI
def interactive_chat(message: str) -> str:
        destination = "None_str"
        KPI_engine_query = None
        try:
            rag = Rag(model="llama3.2")
            destination = rag.classify_query(message)
            # test solo per la mail or report
            KPI_engine_query = rag.routing(destination).invoke({"query": message})

            # la funzione get_object(destination) controlla la variabile destination ed eventualmente ritorna o KPIRequest o KPITrend o null
            # object = rag.get_object(destination) -> explainableQuery function

            # exp_str = rag.get_explaination(object) -> trasforma in stringa object

            # result = rag.compute_query(object) -> chiamata API a gruppo x a seconda di che oggetto abbiamo passato
            # switch object:
            #   case KPIRequest:
            #       result = ApiRequestCallTopic8(KPIRequest)
            #   case KPITrend:
            #       result = ApiRequestCallTopic3(KPITrend)

            # actual_answer = rag.direct_query(object, result, query, previous_answer) -> ritorna final answer che è la risposta data all'utente
            # rag.set_previous_answer(actual_answer)
            # print(exp_str, "\n\n", actual_answer)
            if destination == "None_str":
                return "Error 2!"  
            elif destination == "e-mail or reports":
                return KPI_engine_query
        except Exception as e:
            #print("Error: The model is broken.")
            print("...\r")
            return str(e)
        # If the destination is found, generate the response
        response = KPI_engine_query
        print(f"Response:{response}")
        return response
