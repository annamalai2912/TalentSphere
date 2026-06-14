import re
import os
import io
import docx
from pypdf import PdfReader
import spacy
import numpy as np

# We'll import sentence_transformers lazily in the class, or globally with error handling 
# to ensure the app doesn't crash on start if installation is still taking place.
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Comprehensive tech skills taxonomy
SKILLS_TAXONOMY = {
    # Languages
    "python": ["python", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "java": ["java"],
    "c++": ["c\\+\\+", "cpp"],
    "c#": ["c#", "c-sharp"],
    "go": ["go", "golang"],
    "rust": ["rust"],
    "ruby": ["ruby"],
    "php": ["php"],
    "scala": ["scala"],
    "r": ["\\br\\b"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "sql": ["sql", "mysql", "postgresql", "sqlite"],
    
    # AI / ML / Data Science
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "natural language processing": ["natural language processing", "nlp"],
    "computer vision": ["computer vision", "cv"],
    "artificial intelligence": ["artificial intelligence", "ai"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch", "torch"],
    "keras": ["keras"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "spacy": ["spacy"],
    "nltk": ["nltk"],
    "transformers": ["transformers", "huggingface", "hugging face"],
    "bert": ["bert"],
    "gpt": ["gpt", "chatgpt", "llm", "large language models"],
    "langchain": ["langchain"],
    "llamaindex": ["llamaindex"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "opencv": ["opencv"],
    "data science": ["data science"],
    "information retrieval": ["information retrieval", "ir"],
    
    # Web Frameworks & Libraries
    "react": ["react", "reactjs", "react.js"],
    "next.js": ["next.js", "nextjs"],
    "angular": ["angular", "angularjs"],
    "vue.js": ["vue.js", "vue", "vuejs"],
    "node.js": ["node.js", "nodejs", "node"],
    "express": ["express", "expressjs"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "django": ["django"],
    
    # Cloud & DevOps
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git", "github", "gitlab"],
    "ci/cd": ["ci/cd", "jenkins", "github actions"],
    "terraform": ["terraform"],
    
    # Databases & Big Data
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "elasticsearch": ["elasticsearch"],
    "spark": ["spark", "pyspark"],
    "hadoop": ["hadoop"],
    "kafka": ["kafka"]
}

class NLPEngine:
    def __init__(self):
        # Load spaCy English model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            # Fallback if spaCy model is not downloaded yet
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], capture_output=True)
            self.nlp = spacy.load("en_core_web_sm")
            
        # Load Sentence-Transformer model
        self.model = None
        self.load_transformer()

    def load_transformer(self):
        global SENTENCE_TRANSFORMERS_AVAILABLE
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                import sentence_transformers
                SENTENCE_TRANSFORMERS_AVAILABLE = True
            except ImportError:
                return
        
        if SENTENCE_TRANSFORMERS_AVAILABLE and self.model is None:
            try:
                import sentence_transformers
                # Using a highly popular, small, and fast model (~80MB)
                self.model = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                print(f"Error loading SentenceTransformer: {e}. Semantic similarity will fall back to TF-IDF logic.")

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        text = ""
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
        return text

    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        text = ""
        try:
            doc_file = io.BytesIO(file_bytes)
            doc = docx.Document(doc_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
        return text

    def extract_text(self, filename: str, file_bytes: bytes) -> str:
        ext = os.path.splitext(filename.lower())[1]
        if ext == '.pdf':
            return self.extract_text_from_pdf(file_bytes)
        elif ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_bytes)
        else:
            # Fallback to plain text
            try:
                return file_bytes.decode('utf-8', errors='ignore')
            except Exception:
                return ""

    def extract_contact_info(self, text: str):
        email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_regex = r'\+?\d[\d\s\(\)\.-]{7,15}\d'
        
        email_match = re.search(email_regex, text)
        phone_match = re.search(phone_regex, text)
        
        email = email_match.group(0) if email_match else None
        phone = phone_match.group(0) if phone_match else None
        
        return email, phone

    def extract_candidate_name(self, text: str, filename: str) -> str:
        # 1. Clean filename as fallback
        base_name = os.path.splitext(filename)[0]
        cleaned_filename = base_name.replace("_", " ").replace("-", " ")
        cleaned_filename = re.sub(r'(?i)resume|cv|screen|rank', '', cleaned_filename).strip()
        
        # 2. Try spaCy NER on the first 300 characters of the resume (where names are typically located)
        head_text = text[:300]
        doc = self.nlp(head_text)
        
        person_entities = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
        
        # Clean extracted names
        valid_names = []
        for name in person_entities:
            # Names usually have 2-3 words and only letters/spaces
            name_clean = re.sub(r'[^a-zA-Z\s]', '', name).strip()
            word_count = len(name_clean.split())
            if 1 < word_count <= 4 and not any(w.lower() in ["curriculum", "vitae", "resume", "page", "summary"] for w in name_clean.split()):
                valid_names.append(name_clean)
                
        if valid_names:
            return valid_names[0]
            
        # 3. Fallback to lines matching standard name patterns in first 3 lines
        lines = [line.strip() for line in text.split("\n") if line.strip()][:3]
        for line in lines:
            if 1 < len(line.split()) <= 3 and re.match(r'^[a-zA-Z\s]+$', line):
                return line
                
        return cleaned_filename if cleaned_filename else "Unknown Candidate"

    def extract_skills(self, text: str) -> list:
        found_skills = []
        text_lower = text.lower()
        
        # Search for each skill in taxonomy
        for skill_name, patterns in SKILLS_TAXONOMY.items():
            for pattern in patterns:
                # Add word boundary flags to avoid matching inside larger words (e.g. 'c' in 'candidate')
                if '\\b' in pattern or '^' in pattern or '\\' in pattern:
                    regex = pattern
                else:
                    regex = rf'\b{re.escape(pattern)}\b'
                    
                if re.search(regex, text_lower):
                    found_skills.append(skill_name)
                    break # Matches this skill, move to the next skill
                    
        return sorted(list(set(found_skills)))

    def extract_education(self, text: str) -> list:
        education_levels = []
        text_lower = text.lower()
        
        edu_mappings = {
            "Ph.D.": [r'\bph\.?d\b', r'\bdoctor of philosophy\b', r'\bdoctorate\b'],
            "M.Tech": [r'\bm\.?tech\b', r'\bmaster of technology\b'],
            "B.Tech": [r'\bb\.?tech\b', r'\bbachelor of technology\b'],
            "M.S. / M.Sc": [r'\bm\.?s\.?\b', r'\bm\.?sc\b', r'\bmaster of science\b'],
            "B.S. / B.Sc / B.E.": [r'\bb\.?s\.?\b', r'\bb\.?sc\b', r'\bb\.?e\.?\b', r'\bbachelor of science\b', r'\bbachelor of engineering\b'],
            "MBA": [r'\bmba\b', r'\bmaster of business administration\b'],
            "BCA / MCA": [r'\bbca\b', r'\bmca\b', r'\bbachelor of computer applications\b', r'\bmaster of computer applications\b'],
        }
        
        for edu_name, patterns in edu_mappings.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    education_levels.append(edu_name)
                    break
                    
        return education_levels

    def estimate_experience(self, text: str) -> float:
        text_lower = text.lower()
        
        # 1. Match phrases like "5 years of experience", "3+ yrs experience", "10+ years"
        exp_patterns = [
            r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience',
            r'experience\s*:\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)',
            r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+(?:in\s+)?(?:industry|software|it|field|work|development)',
            r'worked\s+for\s+(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)'
        ]
        
        years = []
        for pattern in exp_patterns:
            matches = re.findall(pattern, text_lower)
            for m in matches:
                try:
                    years.append(float(m))
                except ValueError:
                    pass
                    
        if years:
            return max(years)
            
        # 2. Fallback: Parse date intervals e.g. "2018 - 2022" or "June 2019 to Present"
        # and accumulate years.
        year_ranges = re.findall(r'\b(20\d{2})\s*-\s*(20\d{2}|present|current)\b', text_lower)
        total_exp = 0.0
        for start, end in year_ranges:
            start_yr = int(start)
            end_yr = 2026 if end in ['present', 'current'] else int(end) # Default current year to 2026 as per metadata
            duration = end_yr - start_yr
            if 0 < duration < 15: # Filter out anomalies
                total_exp += duration
                
        if total_exp > 0:
            return min(total_exp, 20.0) # Cap estimated experience at 20 years
            
        return 0.0

    def compute_semantic_similarity(self, text1: str, text2: str) -> float:
        if not text1.strip() or not text2.strip():
            return 0.0
            
        self.load_transformer()
        
        # If Sentence Transformers is loaded successfully
        if self.model is not None:
            try:
                embeddings = self.model.encode([text1, text2])
                emb1 = embeddings[0]
                emb2 = embeddings[1]
                
                # Cosine similarity
                cos_sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                # Map to percentage (0 - 100), bounded. Cosine similarity can be negative but is usually >0 for texts.
                score = float(max(0.0, cos_sim) * 100)
                return score
            except Exception as e:
                print(f"Embedding error: {e}")
                
        # Fallback to a simple TF-IDF-like token overlap if BERT fails
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return float(len(intersection) / len(union) * 100)

    def extract_highlights(self, resume_text: str, jd_text: str, top_n: int = 3) -> list:
        # Split resume into sentences
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', resume_text) if len(s.strip()) > 15]
        if not sentences:
            return []
            
        # Clean job description into simple key terms or match sentences
        jd_sentences = [s.strip() for s in re.split(r'[.!?\n]+', jd_text) if len(s.strip()) > 15]
        if not jd_sentences:
            # Fallback if JD is very short
            jd_sentences = [jd_text]
            
        self.load_transformer()
        if self.model is not None:
            try:
                # Encode sentences
                sentence_embs = self.model.encode(sentences)
                jd_embs = self.model.encode(jd_sentences)
                
                # Find maximum similarity for each resume sentence against any JD sentence
                scores = []
                for i, s_emb in enumerate(sentence_embs):
                    max_sim = 0.0
                    for j_emb in jd_embs:
                        sim = np.dot(s_emb, j_emb) / (np.linalg.norm(s_emb) * np.linalg.norm(j_emb))
                        if sim > max_sim:
                            max_sim = sim
                    scores.append((max_sim, sentences[i]))
                    
                # Sort descending
                scores.sort(key=lambda x: x[0], reverse=True)
                
                # Return top N unique sentences
                seen = set()
                top_sentences = []
                for score, sent in scores:
                    sent_clean = sent.replace('\xa0', ' ').strip()
                    if sent_clean.lower() not in seen and len(top_sentences) < top_n:
                        seen.add(sent_clean.lower())
                        top_sentences.append(sent_clean)
                return top_sentences
            except Exception as e:
                print(f"Error extracting highlights with BERT: {e}")
                
        # Fallback keyword match
        jd_words = set(re.findall(r'\w+', jd_text.lower()))
        scored_sentences = []
        for s in sentences:
            s_words = set(re.findall(r'\w+', s.lower()))
            overlap = len(s_words.intersection(jd_words))
            scored_sentences.append((overlap, s))
            
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored_sentences[:top_n]]

    def analyze_resume(self, resume_text: str, jd_text: str, filename: str) -> dict:
        # 1. Extracted info
        email, phone = self.extract_contact_info(resume_text)
        candidate_name = self.extract_candidate_name(resume_text, filename)
        candidate_skills = self.extract_skills(resume_text)
        candidate_edu = self.extract_education(resume_text)
        candidate_exp = self.estimate_experience(resume_text)
        
        # 2. Extracted Job Description requirements
        jd_skills = self.extract_skills(jd_text)
        jd_edu = self.extract_education(jd_text)
        
        # Extract JD experience requirement if any (e.g. "3+ years", "5 yrs")
        exp_req_matches = re.findall(r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\b', jd_text.lower())
        jd_exp_req = float(exp_req_matches[0]) if exp_req_matches else 0.0
        
        # 3. Compute Sub-scores (0-100)
        # 3a. Semantic similarity
        semantic_score = self.compute_semantic_similarity(resume_text, jd_text)
        
        # 3b. Skill Score: Match JD skills
        skills_matched = [s for s in jd_skills if s in candidate_skills]
        skills_missing = [s for s in jd_skills if s not in candidate_skills]
        
        if jd_skills:
            skill_score = (len(skills_matched) / len(jd_skills)) * 100
        else:
            # If no skills are detected in the JD, compute overlap based on candidate skills found in general
            skill_score = 50.0 if not candidate_skills else min(100.0, 50.0 + len(candidate_skills) * 5)
            
        # 3c. Education Score
        # Match degrees. E.g. if JD specifies "M.Tech", check if candidate has it.
        education_score = 100.0
        if jd_edu:
            # We rank degree requirements loosely: Ph.D. > M.Tech / MS > B.Tech / BE > Others
            # Find the highest degree required in the JD
            degree_weights = {"Ph.D.": 5, "M.Tech": 4, "M.S. / M.Sc": 4, "B.Tech": 3, "B.S. / B.Sc / B.E.": 3, "MBA": 3, "BCA / MCA": 2}
            highest_jd_weight = max([degree_weights.get(e, 1) for e in jd_edu])
            highest_candidate_weight = max([degree_weights.get(e, 0) for e in candidate_edu]) if candidate_edu else 1
            
            if highest_candidate_weight >= highest_jd_weight:
                education_score = 100.0
            elif highest_candidate_weight == highest_jd_weight - 1:
                education_score = 70.0 # Just one level lower
            else:
                education_score = 40.0 # Significantly lower or missing
        else:
            # No specific education requirements mentioned in JD, check if candidate has any higher education
            education_score = 80.0 if candidate_edu else 50.0
            
        # 3d. Experience Score
        experience_score = 100.0
        if jd_exp_req > 0.0:
            if candidate_exp >= jd_exp_req:
                experience_score = 100.0
            elif candidate_exp > 0.0:
                experience_score = (candidate_exp / jd_exp_req) * 100.0
            else:
                experience_score = 30.0
        else:
            # No experience requirement in JD, give points based on candidate experience
            experience_score = min(100.0, 50.0 + candidate_exp * 10.0)
            
        # 4. Overall Weighted Score
        # Semantic Score: 50%, Skill Score: 30%, Education Score: 10%, Experience Score: 10%
        overall_score = (
            (semantic_score * 0.50) + 
            (skill_score * 0.30) + 
            (education_score * 0.10) + 
            (experience_score * 0.10)
        )
        # Bound scores to 0-100
        overall_score = round(max(0.0, min(100.0, overall_score)), 1)
        semantic_score = round(semantic_score, 1)
        skill_score = round(skill_score, 1)
        education_score = round(education_score, 1)
        experience_score = round(experience_score, 1)
        
        # 5. Extract Highlights
        highlights = self.extract_highlights(resume_text, jd_text, top_n=3)
        
        return {
            "candidate_name": candidate_name,
            "filename": filename,
            "email": email,
            "phone": phone,
            "overall_score": overall_score,
            "semantic_score": semantic_score,
            "skill_score": skill_score,
            "education_score": education_score,
            "experience_score": experience_score,
            "skills_found": candidate_skills,
            "skills_missing": skills_missing,
            "education_extracted": candidate_edu,
            "experience_years": candidate_exp,
            "key_highlights": highlights
        }
