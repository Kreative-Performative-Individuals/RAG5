import pytest
import requests

BASE_URL = "http://localhost:8000"

def test_message():
    data = {"message": "Passed message"}  # Corrected key to match the model
    response = requests.post(f"{BASE_URL}/chat/", json=data)
    assert response.status_code == 200
    assert response.json() == {"response": "Mocked response to: Passed message"}

