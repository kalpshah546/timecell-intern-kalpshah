import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

url = "https://api.deepseek.com/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

data = {
    "model": "deepseek-chat",  # correct model name
    "messages": [
        {"role": "user", "content": "Say hello in one sentence."}
    ],
    "temperature": 0.7,
}

response = requests.post(url, headers=headers, json=data)

print("Status Code:", response.status_code)
print("Response:", response.text)