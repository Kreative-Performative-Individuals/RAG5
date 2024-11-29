from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    #Add startup actions.
    pass

@app.get("/")
def root():
    return {"message": "Rag"}
