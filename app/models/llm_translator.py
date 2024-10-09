import os
import asyncio
import json
import google.generativeai as genai
from flask import current_app

class LLMTranslator:
    def __init__(self):
        self.model = None
        self.responses_received = 0
        self.total_chunks = 0

    def _initialize_model(self):
        if self.model is None and not current_app.config['DRY_RUN']:
            api_key = current_app.config['LLM_API_KEY']
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name=current_app.config['LLM_MODEL'],
                generation_config=current_app.config['LLM_GENERATION_CONFIG'],
                system_instruction=current_app.config['LLM_SYSTEM_PROMPT']
            )

    async def translate_text(self, json_chunks):
        self._initialize_model()
        self.total_chunks = len(json_chunks)
        self.responses_received = 0
        tasks = [self.send_translation_request(chunk, i) for i, chunk in enumerate(json_chunks)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        translated_chunks = []
        num_success = 0
        
        for result in results:
            if isinstance(result, Exception):
                translated_chunks.append(json.dumps([{"id": -1, "translated_content": "Translation failed"}]))
            else:
                translated_chunks.append(result)
                num_success += 1
        
        return translated_chunks, self.total_chunks, num_success

    async def send_translation_request(self, json_chunk, chunk_index):
        self._initialize_model()
        for attempt in range(3):
            try:
                print(f"Sending request for chunk {chunk_index + 1}")
                if current_app.config['DRY_RUN']:
                    print(f"Dry run: generate_content arguments for chunk {chunk_index + 1}:")
                    print(f"System prompt: {current_app.config['LLM_SYSTEM_PROMPT']}")
                    print(f"User input: {json_chunk}")
                    response_text = json.dumps([{"id": entry["id"], "translated_content": f"Dry run translation for entry {entry['id']}"} for entry in json.loads(json_chunk)])
                else:
                    response = await asyncio.to_thread(
                        self.model.generate_content,
                        f"{json_chunk}",
                        safety_settings=current_app.config['LLM_SAFETY_SETTINGS']
                    )
                    response_text = response.text
                    # Ensure the response is valid JSON
                    try:
                        json.loads(response_text)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON response for chunk {chunk_index + 1}: {response_text}")
                        raise ValueError("Invalid JSON response from LLM")
                self.responses_received += 1
                return response_text
            except Exception as e:
                print(f"Error in translation attempt {attempt + 1} for chunk {chunk_index + 1}: {str(e)}")
                if attempt == 2:
                    raise e
                await asyncio.sleep([3, 15, 45][attempt])

    def get_translation_status(self):
        return self.responses_received, self.total_chunks