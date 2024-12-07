from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
        self.response

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. You can specify allowed domains like ["http://example.com"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods. You can specify like ["GET", "POST"]
    allow_headers=["*"],  # Allows all headers. You can specify specific headers like ["Content-Type"]
)

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
@app.get("/chat/", response_model=BotResponse)
#If the message is a Message object it returns error 422 but if it is a str it works
def chat_with_bot(message: str, previous_response: str | None = None):
    try:
        bot_reply = interactive_chat(message, previous_response)
        return {"response": bot_reply}
    except Exception as e:
        return {"response": str(e)}

# Aggiungere il ciclo for per gestire gli errori sulla costruzione delle KPI
def interactive_chat(message: str, previous_response: str) -> str:
    destination = "None_str"
    KPI_engine_query = None
    rag = Rag(model="llama3.2")
    actual_answer = ""
    try:
            
        destination = rag.classify_query(message)
        KPI_engine_query = rag.routing(destination, previous_answer=previous_response).invoke({"query": message})
        if destination != "KPI calculation":
            print("RISPOSTA PRECEDENTE: "+previous_response)
            return str(KPI_engine_query)
        # la funzione get_object(destination) controlla la variabile destination ed eventualmente ritorna o KPIRequest o KPITrend o null
        # object = rag.get_object(destination) -> explainableQuery function

        # exp_str = rag.get_explaination(object) -> trasforma in stringa object
        docs, rag.result = rag.compute_query(KPI_engine_query) #-> chiamata API a gruppo x a seconda di che oggetto abbiamo passato
        print(docs)
        actual_answer = rag.direct_query(KPI_engine_query, docs, rag.result, message, previous_response) #-> ritorna final answer che è la risposta data all'utente
        # print(exp_str, "\n\n", actual_answer)
            
    except Exception as e:
        #print("Error: The model is broken.")
        print(e)
    # If the destination is found, generate the response
    response = str(actual_answer)
    print(f"Response:{response}")
    return response
