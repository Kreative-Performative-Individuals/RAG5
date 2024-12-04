import requests
import json

BASE_URL = "http://kpi-engine:8008"

def ApiRequestCallTopic8(obj):
    data = obj
    response = requests.get(f"{BASE_URL}/kpi/", data=json.dumps(data, default=lambda o: o.__dict__, sort_keys=False, indent=4))
    response = json.loads(response.content)
    print(response)
    result = response["value"]
    return result
    # assert response.json() == {"response": "Mocked response to: Passed message"}