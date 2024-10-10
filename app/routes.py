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

# Remove the global llm_translator instance
# llm_translator = LLMTranslator()

@bp.route('/')
def index():
    return render_template('index.html')

def get_rate_limit():
    return current_app.config['RATE_LIMIT']

@bp.route('/upload', methods=['POST'])
@limiter.limit(get_rate_limit)
async def upload_file():
    try:
        # Create LLMTranslator instance within the request context
        llm_translator = LLMTranslator()
        
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
            translated_chunks, total_chunks, num_success = await llm_translator.translate_text(json_chunks)
            
            translation_successful = num_success == total_chunks
            
            if translation_successful:
                # Process and save translated chunks
                for i, translated_chunk in enumerate(translated_chunks):
                    # Save request and response JSONs
                    request_filename = f"{os.path.splitext(filename)[0]}_request_{i+1}.json"
                    request_path = os.path.join(current_app.config['UPLOAD_FOLDER'], request_filename)
                    with open(request_path, 'w', encoding='utf-8') as f:
                        f.write(json_chunks[i])

                    response_filename = f"{os.path.splitext(filename)[0]}_response_{i+1}.json"
                    response_path = os.path.join(current_app.config['UPLOAD_FOLDER'], response_filename)
                    with open(response_path, 'w', encoding='utf-8') as f:
                        f.write(translated_chunk)
                    print(f"Received JSON for chunk {i+1}")

                # Merge translations
                translated_chunks = [json.loads(chunk) if isinstance(chunk, str) else chunk for chunk in translated_chunks]
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
                    'total_chunks': total_chunks,
                    'num_success': num_success,
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
    # Create LLMTranslator instance within the request context
    llm_translator = LLMTranslator()
    responses_received, total_chunks = llm_translator.get_translation_status()
    return jsonify({'responses_received': responses_received, 'total_chunks': total_chunks})

@bp.route('/cleanup', methods=['POST'])
def cleanup_uploads():
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        return jsonify({'success': True, 'message': 'All files in the uploads folder have been removed.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500