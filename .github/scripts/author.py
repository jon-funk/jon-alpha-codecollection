import json, os, requests, time

HEALTH_ENDPOINT: str = "/health"
START_ENDPOINT: str = "/start"
SUGGEST_ENDPOINT: str = "/suggest"
IMPLEMENT_ENDPOINT: str = "/implement"
API_URL: str = "https://codebundle-builder.sandbox.runwhen.com/api"
ISSUE_FILE_PATH: str = "/tmp/issue_content"
CODEBUNDLE_WRITE_PATH: str = "/tmp/codebundle"

def health():
    print("Checking health...")
    rsp = requests.get(API_URL + HEALTH_ENDPOINT)
    if rsp.status_code < 200 or rsp.status_code >= 300:
        raise Exception(f"Failed health check with {rsp.status_code} from {rsp.text}")
    return rsp.json()

def parse_issue_content():
    print("Parsing issue content...")
    submission: list = []
    with open(ISSUE_FILE_PATH, "r") as f:
        content = f.read()
        content = content.split("\n")
        for line in content:
            if line and not line.startswith("#"):
                submission.append(line)
    print(f"submission: {submission}")
    return submission[0], submission[1], submission[2], submission[3]

def new_codebundle():
    total_retries: int = 0
    print("Creating new codebundle...")
    incident_description, platform, include_auth, diagnostic_only = parse_issue_content()
    health()
    data = {
       "incidentDescription":incident_description,"diagnosticOnly":diagnostic_only,"includeAuth":include_auth,"platform":platform,
    }
    print(f"Starting with data: {data}")
    rsp = requests.post(API_URL + START_ENDPOINT, data=data)
    starting_data = rsp.json()
    time.sleep(2)
    print("////\nReceived metadata: ", starting_data)
    rsp = requests.post(API_URL + SUGGEST_ENDPOINT, data=starting_data)
    time.sleep(2)
    if rsp.status_code < 200 or rsp.status_code >= 300:
        raise Exception(f"Failed to suggest with status code {rsp.status_code} and text {rsp.text}")
    print(f"////\nSuggested: {rsp.json()}")
    codebundle = rsp.json()
    print(f"////\nImplementing tasks for {codebundle}")
    if "tasks" not in codebundle:
        print("No tasks to implement")
        raise Exception("No tasks to implement")
    task_titles = [task["title"] for task in codebundle["tasks"]]
    for task_title in task_titles:
        if not task_title:
            continue
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            rsp = requests.post(API_URL + IMPLEMENT_ENDPOINT, data={
                "implement_task": task_title,
                "codebundle": codebundle
            })
            time.sleep(10)
            print(f"////\nImplementation status for {task_title}: {rsp.status_code} {rsp.text}")
            if rsp.status_code >= 200 and rsp.status_code < 300:
                break
            retry_count += 1
            total_retries += 1
        codebundle = rsp.json()
    print(f"////\nA total of {total_retries} retries were made")
    print(f"////\nFinal codebundle: {codebundle}")
    return codebundle

def write_codebundle(codebundle):
    print("Writing codebundle to file...")
    folder_name = codebundle.get("name", "untitled")
    # assuming codebundle is a dict
    for task in codebundle.get("tasks", []):
        script_code = task.get("scriptCode")
        script_file_name = task.get("scriptFileName")
        if script_code and script_file_name:
            folder_path = os.path.join(CODEBUNDLE_WRITE_PATH, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            script_file_path = os.path.join(folder_path, script_file_name)
            with open(script_file_path, "w") as f:
                f.write(script_code)
    robot_content = codebundle.get("robot")
    if robot_content:
        folder_path = os.path.join(CODEBUNDLE_WRITE_PATH, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        robot_file_path = os.path.join(folder_path, "runbook.robot")
        with open(robot_file_path, "w") as f:
            f.write(robot_content)
    markdown_content = codebundle.get("markdown")
    if markdown_content:
        folder_path = os.path.join(CODEBUNDLE_WRITE_PATH, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        markdown_file_path = os.path.join(folder_path, "README.md")
        with open(markdown_file_path, "w") as f:
            f.write(markdown_content)
