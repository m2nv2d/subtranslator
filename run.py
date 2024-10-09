import argparse
from app import create_app
from asgiref.wsgi import WsgiToAsgi

parser = argparse.ArgumentParser(description='Run the Subtitle Translator app')
parser.add_argument('--dry-run', action='store_true', help='Run in dry run mode')
args = parser.parse_args()

app = create_app(dry_run=args.dry_run)
asgi_app = WsgiToAsgi(app)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=5000)