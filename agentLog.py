from collections import Counter
from openai import OpenAI
import os


api_key = os.environ.get('OpenAIkey', '')
client = OpenAI(api_key=api_key)

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


def analyze_errors(top_errors):

    text = "\n".join([f"{count}x {msg}" for msg, count in top_errors])

    prompt = f"""
You are a DevOps assistant.

Analyze the most frequent application errors.

Errors:
{text}

Explain:
- most likely root causes
- recommended fixes
- which issue should be fixed first
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text


counter = read_errors(r"C:\Users\sanzh\Downloads\logs260317.txt")

top10 = top_errors(counter, 10)

print("Top errors:\n")

for msg, count in top10:
    print(f"{count}x {msg}")

print("\nAI analysis:\n")

report = analyze_errors(top10)

print(report)