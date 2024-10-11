import re
import json
from flask import current_app

class SubtitleProcessor:
    def parse_srt(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            subtitle_pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.*\n)*?)\n')
            subtitles = subtitle_pattern.findall(content)
            
            if not subtitles:
                raise ValueError("No valid subtitles found. Please ensure your SRT file follows the standard format.")
            
            master_json = []
            for sub in subtitles:
                master_json.append({
                    "id": int(sub[0]),
                    "start_time": sub[1],
                    "end_time": sub[2],
                    "original_content": sub[3].strip()
                })
            
            return master_json
        except UnicodeDecodeError:
            raise ValueError("Unable to decode the SRT file. Please ensure it's in UTF-8 encoding.")
        except re.error:
            raise ValueError("Malformed SRT file. Unable to parse subtitles. Please check the file format.")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while parsing the SRT file: {str(e)}")

    def create_chunks(self, master_json):
        chunk_size = current_app.config['SUBTITLE_CHUNK_SIZE']
        chunks = []
        for i in range(0, len(master_json), chunk_size):
            chunk = [{
                "id": entry["id"],
                "original_content": entry["original_content"]
            } for entry in master_json[i:i+chunk_size]]
            chunks.append(json.dumps(chunk))
        return chunks

    def merge_translations(self, master_json, translated_chunks):
        try:
            for chunk in translated_chunks:
                # Parse the JSON string if it's not already a dictionary
                if isinstance(chunk, str):
                    try:
                        translated_entries = json.loads(chunk)
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON: {chunk}")
                        continue
                else:
                    translated_entries = chunk
            
                for entry in translated_entries:
                    try:
                        index = next(i for i, item in enumerate(master_json) if item["id"] == entry["id"])
                        # Check if 'translated_content' exists, otherwise use 'content' or keep original
                        if "translated_content" in entry:
                            master_json[index]["translated_content"] = entry["translated_content"]
                        elif "content" in entry:
                            master_json[index]["translated_content"] = entry["content"]
                        else:
                            print(f"Warning: No translation found for entry {entry['id']}")
                            master_json[index]["translated_content"] = master_json[index]["original_content"]
                    except StopIteration:
                        print(f"Warning: No matching ID found for entry {entry['id']}")
                    except KeyError as e:
                        print(f"KeyError in entry: {entry}. Error: {str(e)}")
            return master_json
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in translated chunks")
        except KeyError as e:
            raise ValueError(f"Missing key in JSON structure: {str(e)}")

    def json_to_srt(self, master_json):
        srt_content = ""
        for entry in master_json:
            srt_content += f"{entry['id']}\n"
            srt_content += f"{entry['start_time']} --> {entry['end_time']}\n"
            srt_content += f"{entry['translated_content']}\n\n"
        return srt_content.strip()