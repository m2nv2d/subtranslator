import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

LLM_SYSTEM_PROMPT = """Help me translate the subtitle of a cooking course of mine into Vietnamese. Don't translate line by line or word by word; make sure take into account the context, what the speaker is trying to teach, what they're trying to convey, especially sentence they're talking at the time; then convert them into natural Vietnamese (how natives actually talk in the same context and style). When in doubt, choose options that are mostly related to the context. I'll provide a json content representing the subtitle, which contains the id of each item and its original content. Your ouput json should have same structure but with the translated content for each item instead. Don't keep original_content in your ouput json. Remember to break long lines into two approximately: not too abrupt, using the flow of the target language (Vietnamese), not using the original line breaks in the original language. It must start as [{"id"."""

CHUNK = [{"id": 1, "original_content": "Now."}, {"id": 2, "original_content": "Alaskan king salmon"}]

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"
}
data = {
    "model": "google/gemini-pro-1.5",
    "messages": [
        {"role": "system", "content": LLM_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(CHUNK)}
    ],
    "top_p": 0.9,
    "temperature": 0.8,
    "provider": {
        "order": [
            "Google",
            "Google AI Studio"
        ]
    },

}

response = requests.post(url, headers=headers, data=json.dumps(data))