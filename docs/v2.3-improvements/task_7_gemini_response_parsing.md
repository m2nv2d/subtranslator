# Task 7: Robust Gemini Response Parsing

## Project Context
In `src/translator/chunk_translator.py`, the `_translate_single_chunk` function parses the JSON response from the Gemini API. The current parsing logic manually iterates through expected keys (`translated_line_1`, `translated_line_2`, etc.) which can be brittle if the API response structure changes slightly or contains unexpected variations.

## Goal
Improve the robustness of the Gemini API response parsing by defining a Pydantic model that represents the expected structure and using it to validate and parse the response.

## Prerequisites
- Access to `src/translator/chunk_translator.py`.
- Understanding of the expected JSON structure returned by the Gemini API based on the system prompt used.
- Pydantic library.

## Subtask 1: Define Pydantic Model for Gemini Response
- Based on the system prompt and expected output described in `translate_all_chunks`, define Pydantic models to represent the structure.
The prompt asks for: `[{ "index": original_index, "translated_line_1": ..., "translated_line_2": ... }, ...]`. This structure is slightly ambiguous regarding how many `translated_line_N` fields might exist.

- **Option A (Flexible with `Extra`):** Define a model for a single translated block allowing extra fields prefixed with `translated_line_`.
  ```python
  from pydantic import BaseModel, Field, RootModel
  from typing import List, Dict, Any
  
  class TranslatedBlock(BaseModel):
      index: int = Field(..., description="Original index of the subtitle block")
      # Use model_extra to capture all other fields dynamically
      # Or define explicit fields if the max number of lines is known/small
      # For dynamic capture:
      model_config = {"extra": "allow"}
  
      def get_translated_content(self) -> str:
          lines = []
          i = 1
          while True:
              line_key = f"translated_line_{i}"
              if line_key in self.model_extra:
                  lines.append(str(self.model_extra[line_key])) # Ensure string conversion
                  i += 1
              else:
                  break
          return "\n".join(lines)
          
  # The overall response is a list of these blocks
  class GeminiTranslationResponse(RootModel[List[TranslatedBlock]]):
      root: List[TranslatedBlock]
  ```

- **Option B (Fixed fields + List):** Change the prompt to ask for a list of lines: `[{ "index": original_index, "translated_lines": ["line 1", "line 2"] }, ...]`. This is generally more robust.
  ```python
  from pydantic import BaseModel, Field, RootModel
  from typing import List
  
  class TranslatedBlock(BaseModel):
      index: int = Field(..., description="Original index of the subtitle block")
      translated_lines: List[str] = Field(..., description="List of translated lines for the block")
  
  class GeminiTranslationResponse(RootModel[List[TranslatedBlock]]):
      root: List[TranslatedBlock]
  ```
  *(Choosing Option B requires updating the system prompt in `translate_all_chunks`)*

- Place these models either in `src/translator/models.py` or directly in `src/translator/chunk_translator.py` if preferred.

## Subtask 2: Update System Prompt (If using Option B)
- If Option B from Subtask 1 is chosen, modify the `system_prompt` string in `translate_all_chunks` to instruct Gemini to return the translation as a list of strings under the key `"translated_lines"`.

## Subtask 3: Refactor Parsing Logic in `_translate_single_chunk`
- Inside the `else` block (non-mock mode) of `_translate_single_chunk`:
    - After receiving the `response.text` from Gemini:
    - Use the defined Pydantic model to parse and validate the JSON string:
      ```python
      from pydantic import ValidationError
      import json
      
      try:
          # Assuming GeminiTranslationResponse and TranslatedBlock models are imported
          # response_text = response.text
          # parsed_response = GeminiTranslationResponse.model_validate_json(response_text)
          
          # Iterate through the validated data
          # for translated_block in parsed_response.root:
          #     block_index = translated_block.index
          #     
          #     # Option A logic:
          #     # translated_content = translated_block.get_translated_content()
          #     
          #     # Option B logic:
          #     # translated_content = "\n".join(translated_block.translated_lines)
          #     
          #     if 0 <= block_index < len(chunk):
          #         chunk[block_index].translated_content = translated_content
          #     else:
          #          logger.warning(f"Received invalid block index {block_index} from Gemini for chunk {chunk_index}")
      
      except json.JSONDecodeError as e:
          logger.error(f"Failed to decode JSON response from Gemini for chunk {chunk_index}: {e}\nResponse Text: {response.text[:500]}...")
          raise ChunkTranslationError(f"Failed to parse JSON response for chunk {chunk_index}") from e
      except ValidationError as e:
          logger.error(f"Gemini response validation failed for chunk {chunk_index}: {e}\nResponse Text: {response.text[:500]}...")
          raise ChunkTranslationError(f"Invalid response structure received from Gemini for chunk {chunk_index}") from e
      ```
    - Replace the old manual loop (`for block in translated_json: ... while f'translated_line_{i}' in block: ...`) with logic that uses the fields from the parsed Pydantic model (`translated_block.index`, `translated_block.translated_lines` or `translated_block.get_translated_content()`).
    - Add error handling for `pydantic.ValidationError` alongside the existing `json.JSONDecodeError`.
    - Add a check to ensure the `block_index` received from Gemini is valid for the current `chunk`.

## Testing
- Unit tests for the parsing logic:
    - Provide mock Gemini responses (valid JSON strings) that match the expected Pydantic model structure and verify successful parsing.
    - Provide invalid JSON strings and verify `ChunkTranslationError` (due to `JSONDecodeError`) is raised.
    - Provide JSON strings that are valid JSON but do *not* match the Pydantic model structure (e.g., missing fields, wrong types) and verify `ChunkTranslationError` (due to `ValidationError`) is raised.
    - Provide valid responses with out-of-bounds `index` values and verify they are handled gracefully (e.g., logged warning).
- Integration tests (mocking the Gemini client): Configure the mock to return different response structures (valid, invalid JSON, invalid structure) and verify the behavior of `_translate_single_chunk` and `translate_all_chunks`. 