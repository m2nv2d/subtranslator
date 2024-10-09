import argparse
import os
import shutil
from app import create_app
from asgiref.wsgi import WsgiToAsgi
from config import Config

def cleanup_uploads():
    upload_folder = Config.UPLOAD_FOLDER
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
    print("All files in the uploads folder have been removed.")

parser = argparse.ArgumentParser(description='Run the Subtitle Translator app')
parser.add_argument('--dry-run', action='store_true', help='Run in dry run mode')
parser.add_argument('--cleanup', action='store_true', help='Clean up the uploads folder before starting')
args = parser.parse_args()

if args.cleanup:
    cleanup_uploads()

app = create_app(dry_run=args.dry_run)
asgi_app = WsgiToAsgi(app)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=5000)