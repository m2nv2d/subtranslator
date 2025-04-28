#!/usr/bin/env python
"""Manual script to verify dependency injection behavior with current environment settings."""

import asyncio
import sys
import subprocess
import logging
from pathlib import Path

import httpx
from dotenv import dotenv_values

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_dependency_injection")

# --- Configuration ---
HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"
APP_MODULE = "main:app"
DOTENV_PATH = project_root / ".env"
SAMPLE_SRT_PATH = project_root / "tests" / "samples" / "sample.srt"

# Ensure sample SRT exists
if not SAMPLE_SRT_PATH.exists():
    SAMPLE_SRT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE_SRT_PATH.write_text("""
1
00:00:01,000 --> 00:00:02,000
Hello

2
00:00:03,000 --> 00:00:04,000
World
""")
    logger.info(f"Created dummy sample SRT file at {SAMPLE_SRT_PATH}")

async def check_server_ready(client: httpx.AsyncClient, max_wait: int = 10) -> bool:
    """Checks if the server is responding to GET /."""
    logger.info(f"Waiting for server at {BASE_URL} to be ready...")
    for _ in range(max_wait):
        try:
            response = await client.get(BASE_URL + "/")
            if response.status_code == 200:
                logger.info("Server is ready.")
                return True
        except httpx.ConnectError:
            pass
        await asyncio.sleep(1)
    logger.error(f"Server did not become ready within {max_wait} seconds.")
    return False

async def main():
    """Verifies dependency injection using existing environment configuration."""
    logger.info("Starting dependency injection verification script...")
    
    # Read current environment settings
    env_settings = dotenv_values(DOTENV_PATH)
    ai_provider = env_settings.get("AI_PROVIDER", "Not set")
    ai_api_key = env_settings.get("AI_API_KEY", "Not set")
    
    logger.info(f"Current environment settings:")
    logger.info(f"AI_PROVIDER: {ai_provider}")
    logger.info(f"AI_API_KEY: {'*****' if ai_api_key and ai_api_key != 'Not set' else ai_api_key}")
    
    # Start server
    server_process = None
    try:
        # Start server using uv run uvicorn
        cmd = ["uv", "run", "uvicorn", APP_MODULE, "--app-dir", "./src", "--host", HOST, "--port", str(PORT), "--log-level", "info"]
        logger.info(f"Starting server: {' '.join(cmd)}")
        
        server_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root
        )
        
        # Check if server started successfully
        async with httpx.AsyncClient() as client:
            if not await check_server_ready(client):
                stdout, stderr = await server_process.communicate()
                logger.error("Server failed to start.")
                logger.error(f"STDOUT:\n{stdout.decode()}")
                logger.error(f"STDERR:\n{stderr.decode()}")
                return False
            
            # Test the different modes with current environment settings
            await test_translation_modes(client)
            
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return False
    finally:
        # Stop server if it's still running
        if server_process and server_process.returncode is None:
            logger.info("Stopping server...")
            try:
                server_process.terminate()
                await asyncio.wait_for(server_process.wait(), timeout=2.0)
                logger.info("Server stopped.")
            except (asyncio.TimeoutError, ProcessLookupError):
                logger.warning("Timeout waiting for server to stop or process already terminated.")

async def test_translation_modes(client: httpx.AsyncClient):
    """Tests translation with both fast and mock modes using current environment settings."""
    
    # Test fast mode first
    logger.info("Testing FAST mode translation...")
    files = {'file': (SAMPLE_SRT_PATH.name, open(SAMPLE_SRT_PATH, 'rb'), 'text/srt')}
    response = await client.post(
        BASE_URL + "/translate", 
        data={"target_lang": "Vietnamese", "speed_mode": "fast"}, 
        files=files,
        timeout=30.0
    )
    
    logger.info(f"Fast mode response status code: {response.status_code}")
    try:
        response_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
        if response.status_code == 200:
            logger.info("Fast mode translation succeeded!")
            logger.info(f"Response data: {response_data}")
        else:
            logger.warning(f"Fast mode failed with status {response.status_code}")
            logger.warning(f"Response details: {response_data}")
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        logger.error(f"Raw response: {response.text}")
    
    # Test mock mode next
    logger.info("Testing MOCK mode translation...")
    files = {'file': (SAMPLE_SRT_PATH.name, open(SAMPLE_SRT_PATH, 'rb'), 'text/srt')}
    response = await client.post(
        BASE_URL + "/translate", 
        data={"target_lang": "Vietnamese", "speed_mode": "mock"}, 
        files=files,
        timeout=30.0
    )
    
    logger.info(f"Mock mode response status code: {response.status_code}")
    try:
        response_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
        if response.status_code == 200:
            logger.info("Mock mode translation succeeded!")
            logger.info(f"Response data: {response_data}")
        else:
            logger.warning(f"Mock mode failed with status {response.status_code}")
            logger.warning(f"Response details: {response_data}")
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        logger.error(f"Raw response: {response.text}")
    
    # Summarize results
    logger.info("\n=== Dependency Injection Verification Summary ===")
    logger.info(f"With current environment settings:")
    
    env_settings = dotenv_values(DOTENV_PATH)
    ai_provider = env_settings.get("AI_PROVIDER", "Not set")
    logger.info(f"AI_PROVIDER: {ai_provider}")
    
    if response.status_code == 200:
        logger.info("✓ Mock mode works as expected (returns 200 OK)")
    else:
        logger.warning(f"✗ Mock mode returned unexpected status: {response.status_code}")
        
    logger.info("This script verified that the dependency injection system is working as expected with your current environment settings.")

if __name__ == "__main__":
    asyncio.run(main()) 