from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import os
import shutil

from app.models import ScreeningResultResponse, CandidateAnalysis
from app.nlp_engine import NLPEngine

app = FastAPI(
    title="Intelligent NLP-Driven Candidate Screening and Resume Ranking Framework",
    description="Automated resume screening & ranking using Sentence-Transformers (BERT) and SpaCy NER.",
    version="1.0.0"
)

# Initialize NLP Engine
nlp_engine = NLPEngine()

# Ensure static directories exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("data/resumes", exist_ok=True)
os.makedirs("data/job_descriptions", exist_ok=True)

# Mount static directory for JS and CSS files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    """Serves the main recruiter dashboard index.html."""
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h2>UI Index file not found. Please create static/index.html</h2>", status_code=404)

@app.post("/api/rank", response_model=ScreeningResultResponse)
async def rank_candidates(
    job_description: str = Form(..., description="The job description to rank resumes against"),
    resumes: List[UploadFile] = File(..., description="List of candidate resumes (PDF, DOCX, TXT)")
):
    """
    Ranks candidate resumes against a job description.
    Parses each resume, extracts keywords/entities using spaCy, computes semantic similarity using BERT,
    and returns a ranked candidate list.
    """
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    if not resumes or len(resumes) == 0:
        raise HTTPException(status_code=400, detail="At least one resume file must be uploaded.")

    # Auto-detect job title from job description (first line or short noun phrases)
    first_line = job_description.strip().split('\n')[0]
    job_title = first_line[:50] if len(first_line) > 5 else "AI / Software Engineering Role"

    # Extract required skills from Job Description to show on UI
    required_skills = nlp_engine.extract_skills(job_description)

    candidates_analysis = []
    
    for resume_file in resumes:
        try:
            # Read file bytes
            content = await resume_file.read()
            filename = resume_file.filename
            
            # Extract text
            resume_text = nlp_engine.extract_text(filename, content)
            
            if not resume_text.strip():
                # Append blank analysis for files we couldn't parse
                candidates_analysis.append(CandidateAnalysis(
                    candidate_name=os.path.splitext(filename)[0],
                    filename=filename,
                    overall_score=0.0,
                    semantic_score=0.0,
                    skill_score=0.0,
                    education_score=0.0,
                    experience_score=0.0,
                    skills_found=[],
                    skills_missing=required_skills,
                    education_extracted=[],
                    experience_years=0.0,
                    key_highlights=["Failed to extract text from file."]
                ))
                continue
                
            # Perform NLP ranking analysis
            analysis = nlp_engine.analyze_resume(resume_text, job_description, filename)
            
            candidates_analysis.append(CandidateAnalysis(**analysis))
            
        except Exception as e:
            # Handle individual resume parsing failures gracefully
            print(f"Error parsing resume {resume_file.filename}: {e}")
            candidates_analysis.append(CandidateAnalysis(
                candidate_name=os.path.splitext(resume_file.filename)[0],
                filename=resume_file.filename,
                overall_score=0.0,
                semantic_score=0.0,
                skill_score=0.0,
                education_score=0.0,
                experience_score=0.0,
                skills_found=[],
                skills_missing=required_skills,
                education_extracted=[],
                experience_years=0.0,
                key_highlights=[f"Error occurred: {str(e)}"]
            ))

    # Sort candidates by overall score descending
    candidates_analysis.sort(key=lambda x: x.overall_score, reverse=True)

    return ScreeningResultResponse(
        job_title_detected=job_title,
        required_skills_detected=required_skills,
        candidates=candidates_analysis
    )

@app.get("/api/samples")
async def get_samples():
    """
    Returns pre-loaded sample data for demonstration.
    Allows testing the framework without uploading files.
    """
    # Sample Job Description
    sample_jd = (
        "Machine Learning Engineer / Data Scientist\n\n"
        "Requirements:\n"
        "- Strong proficiency in Python, PyTorch, or TensorFlow.\n"
        "- Experience in Natural Language Processing (NLP), BERT, and Transformers.\n"
        "- Solid understanding of Machine Learning concepts and statistics.\n"
        "- Familiarity with Git, Docker, and FastAPI for API deployment.\n"
        "- Academic background: B.Tech or M.Tech in Computer Science or related fields.\n"
        "- Minimum 2+ years of experience in data science or ML."
    )
    
    # Mock Candidates (represented as mock text files that will be parsed as if uploaded)
    mock_candidates = [
        {
            "name": "Alice Sharma",
            "filename": "Alice_Sharma_ML_Engineer.pdf",
            "text": (
                "Alice Sharma\n"
                "Email: alice.sharma@email.com | Phone: +91 9876543210\n"
                "Education: M.Tech in Computer Science - IIT Bombay (2023)\n"
                "Summary:\n"
                "Passionate Machine Learning Engineer with 3 years of hands-on experience in building AI solutions. "
                "Proficient in deep learning and NLP architectures.\n"
                "Skills: Python, PyTorch, Natural Language Processing, BERT, Transformers, SpaCy, Git, Docker, FastAPI, NumPy, Pandas.\n"
                "Experience:\n"
                "- ML Research Intern (1 year) at AI Labs: Researched BERT embeddings and semantic retrieval pipelines.\n"
                "- Associate ML Engineer (2 years) at TechCorp: Developed and deployed NLP classifiers using PyTorch and FastAPI."
            )
        },
        {
            "name": "Bob Smith",
            "filename": "Bob_Smith_Frontend_Developer.docx",
            "text": (
                "Bob Smith\n"
                "Email: bob.smith@email.com | Phone: +1 (555) 123-4567\n"
                "Education: Bachelor of Computer Applications (BCA) - State University (2021)\n"
                "Summary:\n"
                "Creative Frontend Developer with 4 years of experience building responsive and dynamic web interfaces.\n"
                "Skills: JavaScript, TypeScript, React, HTML5, CSS3, Vue.js, Node.js, Git, MongoDB.\n"
                "Experience:\n"
                "- Senior UI Engineer (2 years) at WebStudio: Developed reusable React components and improved page performance.\n"
                "- Web Developer (2 years) at DevShop: Built custom client websites using HTML, CSS, and Vue.js."
            )
        },
        {
            "name": "Charlie Verma",
            "filename": "Charlie_Verma_Data_Scientist.txt",
            "text": (
                "Charlie Verma\n"
                "Email: charlie.v@email.com\n"
                "Education: B.Tech in Information Technology - NIT Trichy (2024)\n"
                "Summary:\n"
                "Fresh B.Tech graduate eager to start a career in data science. Strong foundations in data analysis and Python programming.\n"
                "Skills: Python, SQL, Pandas, NumPy, Scikit-learn, Machine Learning, Git.\n"
                "Projects:\n"
                "- Movie Recommendation System: Used scikit-learn cosine similarity to recommend movies.\n"
                "- Customer Segmentation: Clustered sales data using K-Means in Python."
            )
        }
    ]
    
    return {
        "job_description": sample_jd,
        "candidates": mock_candidates
    }

if __name__ == "__main__":
    import uvicorn
    # Start server locally
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
