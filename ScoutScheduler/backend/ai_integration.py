import os
import requests
from dotenv import load_dotenv
load_dotenv()


WRITER_API_KEY = os.getenv("WRITER_API_KEY")  # Ensure this environment variable is set
API_URL = "https://api.writer.com/v1/completions"

def get_ai_suggestions(prompt_text):
    headers = {
        "Authorization": f"Bearer {WRITER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "palmyra-x-004",  # Replace with your desired model
        "prompt": prompt_text,
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        print("Raw response:", response.text)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['text'].strip()
    except Exception as e:
        import traceback
        traceback.print_exc()


def test_writer_api():
    api_key = os.getenv("WRITER_API_KEY")
    if not api_key:
        print("API key not found. Please set the WRITER_API_KEY environment variable.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "palmyra-x-003-instruct",
        #"prompt": "Suggest a 20min session for 10-year-olds with 3 meetings left.",
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        response = requests.post("https://api.writer.com/v1/completions", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        print("AI Suggestion:", result['choices'][0]['text'].strip())
    except Exception as e:
        print(f"Error: {e}")
print("Testing Writer API...")
test_writer_api()
