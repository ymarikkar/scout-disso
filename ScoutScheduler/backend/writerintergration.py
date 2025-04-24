import os
import json
from typing import List, Dict
import requests
from writer import Client

# Initialize Writer client using environment variable
WRITER_API_KEY = os.getenv("WRITER_API_KEY")
client = Client(api_key=WRITER_API_KEY)

# Define function schema for badge info tool-calling
tool_functions = [
    {
        "name": "get_badge_info",
        "description": "Fetch the URL and description for a Cub badge by name.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Exact badge name"}
            },
            "required": ["name"]
        }
    }
]

# Wrapper for the FastAPI badge_info endpoint
BADGE_INFO_URL = os.getenv("BADGE_INFO_URL")  # e.g. "https://your-domain.com/badge_info"

def get_badge_info(name: str) -> Dict:
    """
    Call the badge_info service and return its JSON payload.
    """
    resp = requests.get(BADGE_INFO_URL, params={"name": name})
    resp.raise_for_status()
    return resp.json()


def suggest_next_badges(user_id: str = "default", top_k: int = 3) -> List[str]:
    """
    Use the Writer API (palmyra-x-004) with function calling to recommend next badges.
    """
    # Prepare messages
    completed = client.chat.completions  # placeholder for completion of completed badges
    # Build conversation
    messages = [
        {"role": "system", "content": 
            "You are ScoutAI, an assistant for Scout leaders. Suggest the top badges to pursue."},
        {"role": "user", "content": f"Recommend next {top_k} badges for user {user_id}."}
    ]

    # Request with function definitions
    response = client.chat.completions.create(
        model="palmyra-x-004",
        messages=messages,
        functions=tool_functions,
        function_call="auto"
    )

    message = response.choices[0].message
    if message.function_call:
        args = json.loads(message.function_call.arguments)
        result = get_badge_info(**args)
        # Feed function result back to model
        follow_up = client.chat.completions.create(
            model="palmyra-x-004",
            messages=[
                *messages,
                {"role": "assistant", "content": None, "function_call": message.function_call.model_dump()},
                {"role": "function", "name": message.function_call.name, "content": json.dumps(result)}
            ]
        )
        # Parse the suggestions from the final content (e.g., comma-separated)
        suggestion_text = follow_up.choices[0].message.content
        return [b.strip() for b in suggestion_text.split(",")[:top_k]]

    # Fallback: return empty list
    return []

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
