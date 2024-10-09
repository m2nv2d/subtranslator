import os
import asyncio
import traceback
import json
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from app import limiter
from app.models.subtitle_processor import SubtitleProcessor
from app.models.llm_translator import LLMTranslator
from app.utils.rate_limiter import RateLimiter

bp = Blueprint('main', __name__)

subtitle_processor = SubtitleProcessor()
rate_limiter = RateLimiter()
llm_translator = LLMTranslator()

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
async def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and file.filename.endswith('.srt'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process the file
            master_json = subtitle_processor.parse_srt(file_path)
            
            # Save master JSON
            master_json_filename = f"{os.path.splitext(filename)[0]}_master.json"
            master_json_path = os.path.join(current_app.config['UPLOAD_FOLDER'], master_json_filename)
            with open(master_json_path, 'w', encoding='utf-8') as f:
                json.dump(master_json, f, ensure_ascii=False, indent=2)
            
            json_chunks = subtitle_processor.create_chunks(master_json)
            
            # Save individual chunk JSON files
            for i, chunk in enumerate(json_chunks):
                chunk_filename = f"{os.path.splitext(filename)[0]}_chunk_{i+1}.json"
                chunk_path = os.path.join(current_app.config['UPLOAD_FOLDER'], chunk_filename)
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    f.write(chunk)  # chunk is already a JSON string
            
            # Debug info
            num_chunks = len(json_chunks)
            total_entries = len(master_json)
            
            # Check rate limits
            if not rate_limiter.check_limits(request.remote_addr):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Translate
            translation_successful = True
            translated_chunks = []
            for i, chunk in enumerate(json_chunks):
                try:
                    translated_chunk = await llm_translator.send_translation_request(chunk, i)
                    translated_chunks.append(json.loads(translated_chunk))  # Parse JSON string to Python object
                    
                    # Save request and response JSONs
                    request_filename = f"{os.path.splitext(filename)[0]}_request_{i+1}.json"
                    request_path = os.path.join(current_app.config['UPLOAD_FOLDER'], request_filename)
                    with open(request_path, 'w', encoding='utf-8') as f:
                        f.write(chunk)

                    response_filename = f"{os.path.splitext(filename)[0]}_response_{i+1}.json"
                    response_path = os.path.join(current_app.config['UPLOAD_FOLDER'], response_filename)
                    with open(response_path, 'w', encoding='utf-8') as f:
                        f.write(translated_chunk)
                except Exception as e:
                    current_app.logger.error(f"Error translating chunk {i+1}: {str(e)}")
                    translation_successful = False
                    break

            if translation_successful:
                # Merge translations
                translated_master_json = subtitle_processor.merge_translations(master_json, translated_chunks)
                
                # Update master JSON file with translations
                with open(master_json_path, 'w', encoding='utf-8') as f:
                    json.dump(translated_master_json, f, ensure_ascii=False, indent=2)
                
                # Convert to SRT
                translated_srt = subtitle_processor.json_to_srt(translated_master_json)
                
                # Save translated file
                translated_filename = f"translated_{filename}"
                translated_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], translated_filename)
                with open(translated_file_path, 'w', encoding='utf-8') as f:
                    f.write(translated_srt)
                
                debug_info = {
                    'num_chunks': num_chunks,
                    'total_entries': total_entries,
                    'total_chunks': len(json_chunks),
                    'num_success': len(translated_chunks),
                    'master_json_file': master_json_filename
                }
                
                return jsonify({'success': True, 'file_id': translated_filename, 'debug_info': debug_info if current_app.debug else None})
            else:
                return jsonify({'error': 'Translation failed for one or more chunks'}), 500
        return jsonify({'error': 'Invalid file format'}), 400
    except Exception as e:
        current_app.logger.error(f"Error in upload_file: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@bp.route('/download/<file_id>')
def download_file(file_id):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
    return send_file(file_path, as_attachment=True)

@bp.route('/translation_status')
def translation_status():
    responses_received, total_chunks = llm_translator.get_translation_status()
    return jsonify({'responses_received': responses_received, 'total_chunks': total_chunks})