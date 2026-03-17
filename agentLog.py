from collections import Counter
from openai import OpenAI
from github import Github, Auth
import os
import time

# === Настройки ===
OPENAI_API_KEY = os.environ.get('OpenAIkey', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
REPO_NAME = "sanzhar73ismailov/CacheLis"  # формат username/repo
LOG_FILE = r"logs\logs260317.txt"
TARGET_FILE = "mac/restClient.xml"  # файл, который будем изменять

client = OpenAI(api_key=OPENAI_API_KEY)


# === Чтение логов и подсчёт ошибок ===
def read_errors(file):
    counter = Counter()
    with open(file, "r", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        message_index = header.index("Message")
        event_index = header.index("EventType")

        for line in f:
            cols = line.split("\t")
            if len(cols) <= message_index:
                continue
            if cols[event_index] == "ERROR":
                message = cols[message_index]
                if "Email Support Error" not in message:
                    counter[message] += 1
    return counter


def top_errors(counter, n=10):
    return counter.most_common(n)


# === Генерация исправления через OpenAI ===
def generate_fix(error_message, context="Python code"):
    prompt = f"""
You are a senior developer.

Project: Cache Object Script (Intersystems, ver. 2014).

There is a recurring error in the code:

Error: {error_message}

Generate a code snippet that fixes this error.
Provide only the code changes, ready to be applied in a pull request.
"""
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )
    return response.output_text.strip()


# === Создание ветки и пулл-реквеста на GitHub ===
def create_pr(repo_name, branch_name, pr_title, pr_body, github_token, fix_code, target_file):
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)


    # создаём ветку от main
    source = repo.get_branch("main")
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)

    # получаем файл и добавляем исправление
    file_content = repo.get_contents(target_file, ref=branch_name)
    new_content = file_content.decoded_content.decode() + "\n\n# Fix for: " + pr_title + "\n" + fix_code
    repo.update_file(target_file, pr_title, new_content, file_content.sha, branch=branch_name)

    # создаём PR
    pr = repo.create_pull(title=pr_title, body=pr_body, head=branch_name, base="main")
    return pr.html_url


# === Основная логика ===
counter = read_errors(LOG_FILE)
top10 = top_errors(counter, 10)

if not top10:
    print("No errors found in log.")
    exit()

# самая частая ошибка
most_common_error, count = top10[0]

print(f"Most common error ({count}x): {most_common_error}")

json_string = '''
{
  "Arguments": "",
  "ClassName": "unknown ip",
  "ClientIPAddress": "ERROR",
  "EventType": "Exception, наименование ошибки:ОШИБКА #6059: Не удалось открыть TCP/IP сокет к серверу armed.biostat.kz:80<br>, код: CodeNum, локализация: данные: Rest.RestHttpClient:GetOrders",
  "Message": "",
  "MethodName": "ProcessOrdersFromRest+18^restClient +1",
  "Source": "2026-02-17 09:26:12",
  "TimeStamp": "UserWithoutSession",
  "UserName": ""
}
'''

# генерация исправления
#fix_code = generate_fix(most_common_error, context="Python application")
fix_code = generate_fix(json_string, context="Python application")
print("\nSuggested fix:\n")
print(fix_code)

# создание PR
branch_name = f"fix-error-{int(time.time())}"
pr_title = f"Fix: {most_common_error}"
pr_body = f"This PR fixes the most frequent error: {most_common_error}\n\nSuggested fix:\n{fix_code}"

pr_url = create_pr(REPO_NAME, branch_name, pr_title, pr_body, GITHUB_TOKEN, fix_code, TARGET_FILE)

print(f"\nPull request created: {pr_url}")