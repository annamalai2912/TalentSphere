from pydantic import BaseModel, Field
from typing import List, Optional

class SkillMatch(BaseModel):
    name: str
    matched: bool

class CandidateAnalysis(BaseModel):
    candidate_name: str = Field(..., description="Extracted candidate name")
    filename: str = Field(..., description="Original filename of the resume")
    email: Optional[str] = Field(None, description="Extracted candidate email")
    phone: Optional[str] = Field(None, description="Extracted candidate phone number")
    
    # Detailed match scores (0 to 100)
    overall_score: float = Field(..., description="Weighted average match score")
    semantic_score: float = Field(..., description="BERT semantic similarity score")
    skill_score: float = Field(..., description="Keyword & context skill overlap score")
    education_score: float = Field(..., description="Education criteria match score")
    experience_score: float = Field(..., description="Years of experience match score")
    
    # Extracted metadata
    skills_found: List[str] = Field(default_factory=list, description="Skills present in the resume")
    skills_missing: List[str] = Field(default_factory=list, description="Required skills missing from the resume")
    education_extracted: List[str] = Field(default_factory=list, description="Degrees and education details found")
    experience_years: float = Field(0.0, description="Estimated years of experience")
    key_highlights: List[str] = Field(default_factory=list, description="Key resume summary highlights or matching sentences")

class ScreeningResultResponse(BaseModel):
    job_title_detected: str
    required_skills_detected: List[str]
    candidates: List[CandidateAnalysis]
