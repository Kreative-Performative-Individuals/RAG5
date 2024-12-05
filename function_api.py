import requests
import json

KPI_ENGINE_URL = "http://kpi-engine:8008"
KB_URL = "http://kb-service:8001"

def ApiRequestCallTopic8(obj):
    data = obj
    response = requests.post(f"{KPI_ENGINE_URL}/kpi/", data=json.dumps(data, default=lambda o: o.__dict__, sort_keys=False, indent=4))
    response = json.loads(response.content)
    print(response)
    result = response["value"]
    return result
    # assert response.json() == {"response": "Mocked response to: Passed message"}

def ApiRequestCallTopic1(obj):
    request = requests.get(f"{KB_URL}/object-properties", params={"label": obj.name})
    print(type(request))
    print("SONO QUI!!!!")
    print(request.text)
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