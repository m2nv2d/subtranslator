import re

def parse_srt(file_path, chunk_size=40):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    subtitle_pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.*\n)*?)\n')
    subtitles = subtitle_pattern.findall(content)

    # Chunk subtitles
    return [subtitles[i:i + chunk_size] for i in range(0, len(subtitles), chunk_size)]


def extract_text(subtitle_chunk):
    return [subtitle[3].strip() for subtitle in subtitle_chunk]

a = parse_srt('./test/test.srt')
print("Chunks:" + str(len(a)))

entries = 0
for i in a:
    for j in i:
        entries = entries + 1
        print(str(entries) + ":" + j[3])
