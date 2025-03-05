import spacy
import re
import sys
import os
import datetime
from pathlib import Path

# Add parent directory to path to import database module
sys.path.append(str(Path(__file__).parent.parent))
try:
    from db.database import JobSearchDatabase
except ImportError:
    print("Database module not found. Creating directory structure...")
    os.makedirs(Path(__file__).parent.parent / "db", exist_ok=True)
    print("Please run the script again after database.py is created")
    sys.exit(1)

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Predefined list of common skills (extendable)
SKILL_KEYWORDS = {
    "Python", "SQL", "Power BI", "Machine Learning", "Excel", "Data Analysis",
    "Deep Learning", "TensorFlow", "NLP", "Cloud Computing", "Java",
    "C++", "Tableau", "Git", "Django", "Flask", "Angular", "React", "AWS", "Azure",
    "Hadoop", "Big Data", "Keras", "Pandas", "NumPy", "R", "SPSS", "Jupyter",
    "Docker", "Kubernetes", "REST API", "ETL", "Data Engineering", "Statistics",
    "Computer Vision", "FastAPI", "Scikit-learn"
}

def extract_email(text):
    """Extract email from resume text."""
    email_pattern = r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else "Not Found"

def extract_phone(text):
    """Extract phone number from resume text."""
    phone_pattern = r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else "Not Found"

def extract_entities(text):
    """Extract key entities like Name, Organizations, and Skills."""
    doc = nlp(text)
    extracted_info = {
        "name": "Not Found",
        "organizations": [],
        "skills": set()  # Use a set to avoid duplicate skills
    }

    for ent in doc.ents:
        if ent.label_ == "PERSON" and extracted_info["name"] == "Not Found":
            extracted_info["name"] = ent.text
        elif ent.label_ == "ORG":
            extracted_info["organizations"].append(ent.text)

    return extracted_info

def extract_skills(text):
    """Extract skills from resume using keyword matching."""
    detected_skills = set()
    
    for word in SKILL_KEYWORDS:
        # Escape special regex characters
        escaped_word = re.escape(word)
        if re.search(r"\b" + escaped_word + r"\b", text, re.IGNORECASE):
            detected_skills.add(word)
    
    return list(detected_skills)

def parse_resume(resume_text, file_path=None):
    """Parse resume text and extract key information.
    
    Args:
        resume_text (str): The text content of a resume
        file_path (str, optional): Path to the original resume file
        
    Returns:
        dict: Dictionary containing extracted resume information
    """
    result = {}
    
    # Extract basic contact information
    result["email"] = extract_email(resume_text)
    result["phone"] = extract_phone(resume_text)
    
    # Extract name and organizations
    entities = extract_entities(resume_text)
    result["name"] = entities["name"]
    result["organizations"] = entities["organizations"]
    
    # Extract skills
    result["skills"] = extract_skills(resume_text)
    
    # Store the file path if provided
    if file_path:
        result["file_path"] = file_path
        
    return result

def save_resume_to_db(resume_data):
    """Save parsed resume data to the database.
    
    Args:
        resume_data (dict): Dictionary containing parsed resume information
        
    Returns:
        int: ID of the inserted resume record
    """
    db = JobSearchDatabase()
    resume_id = db.add_resume(resume_data)
    db.close()
    return resume_id

def parse_and_save_resume(resume_text, file_path=None):
    """Parse a resume and save it to the database.
    
    Args:
        resume_text (str): Text content of the resume
        file_path (str, optional): Path to the original resume file
        
    Returns:
        tuple: (parsed_resume, resume_id)
    """
    parsed_resume = parse_resume(resume_text, file_path)
    resume_id = save_resume_to_db(parsed_resume)
    return parsed_resume, resume_id

# Example usage for testing
if __name__ == "__main__":
    sample_resume = """
    John Doe
    Email: johndoe@example.com
    Phone: (123) 456-7890
    
    EXPERIENCE
    NLP Engineer, 2019-2022
    
    SKILLS
    Data Analysis, Python
    """
    
    # Simple parsing (just return the parsed data)
    parsed_resume = parse_resume(sample_resume)
    print("Parsed Resume:")
    print(parsed_resume)
    
    # Parse and save to database
    try:
        parsed_resume, resume_id = parse_and_save_resume(sample_resume)
        print(f"\nResume saved to database with ID: {resume_id}")
    except Exception as e:
        print(f"\nError saving to database: {e}")
