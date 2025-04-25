#!/bin/bash

INPUT="$1"
OUTPUT="$2"

if [[ -z "$INPUT" || -z "$OUTPUT" ]]; then
    echo "Usage: $0 input_file.srt output_file.srt"
    exit 1
fi

curl -X POST \
     -F "target_lang=Vietnamese" \
     -F "speed_mode=fast" \
     -F "file=@${INPUT}" \
     -o "${OUTPUT}" \
     http://127.0.0.1:5000/translate