import sys
import subprocess
import importlib.util

def check_and_install_spacy_model():
    print("Checking spaCy language model...")
    # Check if spacy is installed
    if importlib.util.find_spec("spacy") is None:
        print("Error: spaCy is not installed. Please install requirements first: pip install -r requirements.txt")
        sys.exit(1)
        
    import spacy
    try:
        spacy.load("en_core_web_sm")
        print("spaCy model 'en_core_web_sm' is already installed.")
    except IOError:
        print("spaCy model 'en_core_web_sm' not found. Downloading...")
        try:
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
            print("spaCy model 'en_core_web_sm' downloaded successfully.")
        except Exception as e:
            print(f"Error downloading spaCy model: {e}")
            print("Please try running manually: python -m spacy download en_core_web_sm")
            sys.exit(1)

def start_server():
    print("Starting TalentSphere AI Server...")
    # Check if uvicorn is installed
    if importlib.util.find_spec("uvicorn") is None:
        print("Error: uvicorn is not installed. Please install requirements first: pip install -r requirements.txt")
        sys.exit(1)
        
    import uvicorn
    # Start uvicorn server
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    check_and_install_spacy_model()
    start_server()
