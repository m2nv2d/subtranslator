import re
import json

class SubtitleProcessor:
    def parse_srt(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        subtitle_pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.*\n)*?)\n')
        subtitles = subtitle_pattern.findall(content)
        
        master_json = []
        for sub in subtitles:
            master_json.append({
                "id": int(sub[0]),
                "start_time": sub[1],
                "end_time": sub[2],
                "original_content": sub[3].strip()
            })
        
        return master_json

    def create_chunks(self, master_json, chunk_size=40):
        chunks = []
        for i in range(0, len(master_json), chunk_size):
            chunk = [{
                "id": entry["id"],
                "original_content": entry["original_content"]
            } for entry in master_json[i:i+chunk_size]]
            chunks.append(json.dumps(chunk))
        return chunks

    def merge_translations(self, master_json, translated_chunks):
        for chunk in translated_chunks:
            # Parse the JSON string if it's not already a dictionary
            if isinstance(chunk, str):
                translated_entries = json.loads(chunk)
            else:
                translated_entries = chunk
            
            for entry in translated_entries:
                index = next(i for i, item in enumerate(master_json) if item["id"] == entry["id"])
                master_json[index]["translated_content"] = entry["translated_content"]
        return master_json

    def json_to_srt(self, master_json):
        srt_content = ""
        for entry in master_json:
            srt_content += f"{entry['id']}\n"
            srt_content += f"{entry['start_time']} --> {entry['end_time']}\n"
            srt_content += f"{entry['translated_content']}\n\n"
        return srt_content.strip()