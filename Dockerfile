# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /code

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies and clean up cache to minimize image size
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the spaCy model during build to bake it into the image
RUN python -m spacy download en_core_web_sm

# Pre-download the Sentence-Transformer model to bake it into the image
# This makes container startup instant on Hugging Face Spaces
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the application code
COPY . .

# Hugging Face Spaces requires the app to listen on port 7860
EXPOSE 7860

# Start uvicorn server binding to port 7860 and all interfaces
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
