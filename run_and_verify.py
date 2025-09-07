import subprocess
import time
import requests
import sys
import os

# --- Configuration ---
STREAMLIT_APP_FILE = "main.py"
APP_URL = "http://localhost:8501"
STARTUP_WAIT_SECONDS = 15  # Wait time for server to be ready
VENV_PYTHON = os.path.join("venv", "Scripts", "python") if sys.platform == "win32" else os.path.join("venv", "bin", "python")

def run_and_verify():
    """
    Starts the Streamlit app in the background,
    verifies it's active, and then shuts it down.
    """
    streamlit_process = None
    try:
        # Start Streamlit server in the background
        print(f"Starting Streamlit server with '{STREAMLIT_APP_FILE}'...")
        command = ["streamlit", "run", STREAMLIT_APP_FILE, "--server.headless", "true"]
        
        # Use subprocess.Popen to run the process in the background
        streamlit_process = subprocess.Popen(command)

        # Wait for the server to be fully ready
        print(f"Waiting {STARTUP_WAIT_SECONDS} seconds for server to be ready...")
        time.sleep(STARTUP_WAIT_SECONDS)

        # Check if the process is still running
        if streamlit_process.poll() is not None:
            print("ERROR: Streamlit server stopped unexpectedly. Check error messages.")
            return

        # Health check
        print(f"Sending health check request to '{APP_URL}'...")
        
        response = requests.get(APP_URL, timeout=10)  # 10 second timeout

        if response.status_code == 200:
            print("\n✅ SUCCESS: Application started successfully and is responding.")
        else:
            print(f"\n❌ ERROR: Application is not responding. Status Code: {response.status_code}")

    except requests.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to '{APP_URL}'. Server may not have started.")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
    finally:
        # Regardless of the outcome, terminate the Streamlit process
        if streamlit_process:
            print("\nTerminating Streamlit server...")
            streamlit_process.terminate()  # Gracefully terminate the process
            streamlit_process.wait()       # Wait for the process to fully terminate
            print("Server terminated.")

if __name__ == "__main__":
    run_and_verify()