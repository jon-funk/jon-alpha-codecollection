import json, os, requests, time

HEALTH_ENDPOINT: str = "/health"
START_ENDPOINT: str = "/start"
SUGGEST_ENDPOINT: str = "/suggest"
IMPLEMENT_ENDPOINT: str = "/implement"
API_URL: str = "https://codebundle-builder.sandbox.runwhen.com/api"
ISSUE_FILE_PATH: str = "/tmp/issue_content"

def health():
    print("Checking health...")
    r = requests.get(API_URL + HEALTH_ENDPOINT)
    return r.json()

def parse_issue_content():
    print("Parsing issue content...")
    submission: list = []
    with open(ISSUE_FILE_PATH, "r") as f:
        content = f.read()
        content.split("\n")
        for line in content:
            if line and not line.startswith("#"):
                submission.append(line)
    print(f"submission: {submission}")
    return submission[0], submission[1], submission[2], submission[3]

def new_codebundle():
    print("Creating new codebundle...")
    parse_issue_content()
    health()
    data = {
       "incidentDescription":"redis is down","diagnosticOnly":True,"includeAuth":True,"platform":"Kubernetes"
    }
    rsp = requests.post(API_URL + START_ENDPOINT, data=json.dumps(data))
    print("Received metadata: ", rsp.json())
    rsp = requests.post(API_URL + SUGGEST_ENDPOINT, data=json.dumps(rsp.json()))
    codebundle = rsp.json()
    print(f"Implementing tasks for {codebundle}")
    for task in data["tasks"]:
        rsp = requests.post(API_URL + SUGGEST_ENDPOINT, data={
            "implement_task": task["title"],
            "codebundle": codebundle
        })
        time.sleep(5)
        codebundle = rsp.json()
        print(f"Implemented task: {task['title']}")
    return codebundle
