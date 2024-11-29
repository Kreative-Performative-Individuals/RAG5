from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class Message(BaseModel):
    message: str

class BotResponse(BaseModel):
    response: str

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
    return f"Mocked response to: {user_message}"

@app.post("/chat/", response_model=BotResponse)
async def chat_with_bot(user_message: Message) -> BotResponse:
    bot_reply = await calculate_response(user_message.message)
    return BotResponse(response=bot_reply)

