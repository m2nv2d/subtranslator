import os
import asyncio
import json
from litellm import completion
from flask import current_app

class LLMTranslator:
    def __init__(self):
        self.model = None
        self.responses_received = 0
        self.total_chunks = 0
        self._api_key = None
        self._model_name = None
        self._temp = None
        self._system_prompt = None

    @property
    def api_key(self):
        if self._api_key is None:
            self._api_key = current_app.config['LLM_API_KEY']
        return self._api_key

    @property
    def model_name(self):
        if self._model_name is None:
            self._model_name = current_app.config['LLM_MODEL']
        return self._model_name

    @property
    def temp(self):
        if self._temp is None:
            self._temp = current_app.config['LLM_GENERATION_CONFIG']['temperature']
        return self._temp

    @property
    def system_prompt(self):
        if self._system_prompt is None:
            self._system_prompt = current_app.config['LLM_SYSTEM_PROMPT']
        return self._system_prompt

    async def translate_text(self, json_chunks):
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
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json_chunk},
        ]
        for attempt in range(3):
            try:
                print(f"Sending request for chunk {chunk_index + 1}")
                if current_app.config['DRY_RUN']:
                    print(f"Dry run: asyncio.to_thread would run the following for chunk {chunk_index + 1}:")
                    print(f"completion(model='{self.model_name}', messages=[")
                    for msg in messages:
                        print(f"    {{'role': '{msg['role']}', 'content': '{msg['content'][:50]}...'}},")
                    print(f"], temperature={self.temp})")
                    response_text = json.dumps([{"id": entry["id"], "translated_content": f"Dry run translation for entry {entry['id']}"} for entry in json.loads(json_chunk)])
                else:
                    response = await asyncio.to_thread(
                        completion,
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp
                    )
                    response_text = response['choices'][0]['message']['content']
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