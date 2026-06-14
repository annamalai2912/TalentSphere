import unittest
import os
import sys

# Append the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.nlp_engine import NLPEngine

class TestNLPEngine(unittest.TestCase):
    def setUp(self):
        self.engine = NLPEngine()
        self.sample_jd = (
            "Looking for a Machine Learning Engineer with experience in Python and PyTorch. "
            "Should know NLP and Transformers. Requires M.Tech degree and 3+ years of experience."
        )

    def test_skills_extraction(self):
        print("Testing skills extraction...")
        text = "I have experience with Python, PyTorch, Docker, Git and React. I also use spaCy."
        skills = self.engine.extract_skills(text)
        
        # Verify specific skills are found
        self.assertIn("python", skills)
        self.assertIn("pytorch", skills)
        self.assertIn("docker", skills)
        self.assertIn("git", skills)
        self.assertIn("react", skills)
        self.assertIn("spacy", skills)
        self.assertNotIn("java", skills) # Should not match java
        print("Skills extraction: PASSED")

    def test_education_extraction(self):
        print("Testing education extraction...")
        text1 = "Completed B.Tech in CSE from IIT."
        text2 = "Received my Ph.D. in AI and an M.Tech degree."
        
        edu1 = self.engine.extract_education(text1)
        edu2 = self.engine.extract_education(text2)
        
        self.assertIn("B.Tech", edu1)
        self.assertIn("M.Tech", edu2)
        self.assertIn("Ph.D.", edu2)
        print("Education extraction: PASSED")

    def test_experience_estimation(self):
        print("Testing experience estimation...")
        text1 = "I have 5 years of experience in data science."
        text2 = "Developer with 3+ yrs of experience."
        text3 = "Worked from 2018 - 2022 at Google." # 4 years duration
        
        exp1 = self.engine.estimate_experience(text1)
        exp2 = self.engine.estimate_experience(text2)
        exp3 = self.engine.estimate_experience(text3)
        
        self.assertEqual(exp1, 5.0)
        self.assertEqual(exp2, 3.0)
        self.assertEqual(exp3, 4.0)
        print("Experience estimation: PASSED")

    def test_semantic_similarity(self):
        print("Testing semantic similarity...")
        text = "Looking for a Machine Learning Engineer with experience in PyTorch."
        match_text = "I am an ML engineer working with PyTorch."
        mismatch_text = "I build UI components using React and Tailwind CSS."
        
        score_match = self.engine.compute_semantic_similarity(text, match_text)
        score_mismatch = self.engine.compute_semantic_similarity(text, mismatch_text)
        
        # High similarity for matching text, lower for mismatching text
        self.assertGreater(score_match, score_mismatch)
        print(f"Similarity scores: Match={score_match:.1f}%, Mismatch={score_mismatch:.1f}%")
        print("Semantic similarity: PASSED")

    def test_full_analysis(self):
        print("Testing full candidate analysis...")
        resume_text = (
            "Alice Sharma\n"
            "M.Tech in Computer Science from IIT Bombay.\n"
            "3 years of experience as a machine learning engineer.\n"
            "Expert in Python, PyTorch, and NLP."
        )
        
        analysis = self.engine.analyze_resume(resume_text, self.sample_jd, "alice_resume.txt")
        
        self.assertEqual(analysis["candidate_name"], "Alice Sharma")
        self.assertIn("python", analysis["skills_found"])
        self.assertIn("pytorch", analysis["skills_found"])
        self.assertIn("M.Tech", analysis["education_extracted"])
        self.assertEqual(analysis["experience_years"], 3.0)
        
        # Check that scores are computed
        self.assertGreater(analysis["overall_score"], 50.0)
        self.assertGreater(analysis["semantic_score"], 50.0)
        self.assertEqual(analysis["education_score"], 100.0) # Matches M.Tech
        self.assertEqual(analysis["experience_score"], 100.0) # Matches 3 years
        
        print(f"Overall analysis score: {analysis['overall_score']}%")
        print("Full analysis: PASSED")

if __name__ == "__main__":
    unittest.main()
