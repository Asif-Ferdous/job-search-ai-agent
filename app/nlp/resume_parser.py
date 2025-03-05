import spacy
import re

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Expanded list of common skills
SKILL_KEYWORDS = {
    "Python", "SQL", "Power BI", "Machine Learning", "Excel", "Data Analysis",
    "Deep Learning", "TensorFlow", "NLP", "Cloud Computing", "Java",
    "C++", "Tableau", "Git", "Django", "Flask", "Angular", "React", "AWS", "Azure",
    "Hadoop", "Big Data", "Keras", "Pandas", "NumPy", "R", "SPSS", "Jupyter",
    "Docker", "Kubernetes", "REST API", "ETL", "Data Engineering", "Statistics",
    "Computer Vision", "FastAPI", "Scikit-learn", "JavaScript", "TypeScript",
    "Node.js", "Express", "MongoDB", "PostgreSQL", "MySQL", "PHP", "Laravel",
    "Vue.js", "Redux", "HTML", "CSS", "SASS", "LESS", "Bootstrap", "Tailwind",
    "DevOps", "CI/CD", "Jenkins", "GitHub", "BitBucket", "Jira", "Confluence",
    "Agile", "Scrum", "Kanban", "UI/UX", "Figma", "Adobe XD", "Illustrator",
    "Photoshop", "Mobile Development", "Android", "iOS", "Flutter", "React Native",
    "GraphQL", "Apollo", "Redux", "Next.js", "Gatsby", "Web Development",
    "Frontend", "Backend", "Full Stack", "Microservices", "API Design",
    "Database Design", "OOP", "Functional Programming", "Software Architecture"
}

def extract_email(text):
    """Extract email from resume text."""
    # More comprehensive email pattern to ensure we get the complete email
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[a-zA-Z]*"
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else "Not Found"

def extract_phone(text):
    """Extract phone number from resume text with international format support."""
    # More comprehensive phone pattern that handles international formats
    phone_patterns = [
        r"\+\d{1,3}\s*\d{1,4}\s*\d{1,4}\s*\d{1,4}",  # +XX XXXX XXXX XXX
        r"\+\d{1,3}\s*\(\d{1,4}\)\s*\d{1,4}\s*\d{1,4}",  # +XX (XXXX) XXXX XXXX
        r"\+\d{9,15}",  # +XXXXXXXXXXX (simple international)
        r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",  # XXX-XXX-XXXX
        r"\(\d{3}\)\s*\d{3}[-.\s]?\d{4}",  # (XXX) XXX-XXXX
        r"\d{5,6}[-.\s]?\d{5,6}"  # XXXXX-XXXXX (some countries)
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
    
    return "Not Found"

def extract_name(text):
    """Extract full name from resume text using multiple strategies."""
    # Strategy 1: Look for name at the top of the resume
    lines = text.split('\n')
    first_lines = [line.strip() for line in lines[:10] if line.strip()]
    
    # Try to find full name (usually at the top of resume)
    for line in first_lines:
        # Skip lines that look like email, phone, or website
        if '@' in line or 'www' in line or 'http' in line or any(char.isdigit() for char in line):
            continue
        
        # If line is short and doesn't contain common non-name words
        non_name_words = ['resume', 'curriculum', 'vitae', 'cv', 'address', 'phone', 'email']
        if (2 <= len(line.split()) <= 5 and 
            all(word.lower() not in non_name_words for word in line.split()) and
            not any(char.isdigit() for char in line)):
            return line.strip()
    
    # Strategy 2: Use spaCy NER as fallback
    doc = nlp(text[:1000])  # Only look at first 1000 chars for efficiency
    person_entities = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    if person_entities:
        # Return the longest person entity found (likely the full name)
        return max(person_entities, key=len)
    
    return "Not Found"

def extract_education(text):
    """Extract education information from resume text."""
    education_info = []
    
    # Look for education section
    education_patterns = [
        r"EDUCATION(.*?)(?:\n\n|\Z)",
        r"Education(.*?)(?:\n\n|\Z)",
        r"ACADEMIC BACKGROUND(.*?)(?:\n\n|\Z)",
        r"Academic Background(.*?)(?:\n\n|\Z)",
        r"QUALIFICATION(.*?)(?:\n\n|\Z)"
    ]
    
    education_text = ""
    for pattern in education_patterns:
        matches = re.search(pattern, text, re.DOTALL)
        if matches:
            education_text = matches.group(1).strip()
            break
    
    if not education_text:
        return []
    
    # Common degree keywords
    degree_keywords = [
        "Bachelor", "Master", "PhD", "Doctorate", "B.Tech", "M.Tech", "BSc", "MSc", 
        "B.E.", "M.E.", "B.A.", "M.A.", "B.Com", "M.Com", "B.B.A", "M.B.A", "Diploma"
    ]
    
    # Try to extract individual education entries
    entries = re.split(r'\n(?=\d{4}|\w+ \d{4}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\w+\'s)', education_text)
    
    for entry in entries:
        if not entry.strip():
            continue
        
        education_entry = {
            "degree": "Not specified",
            "institution": "Not specified",
            "duration": "Not specified"
        }
        
        # Extract degree
        for keyword in degree_keywords:
            if keyword in entry:
                # Try to capture full degree name
                degree_match = re.search(rf"{keyword}\s*(\w+\s*in\s*[\w\s,]+|\w+)", entry)
                if degree_match:
                    education_entry["degree"] = f"{keyword} {degree_match.group(1)}"
                else:
                    education_entry["degree"] = keyword
                break
        
        # Extract institution
        doc = nlp(entry)
        for ent in doc.ents:
            if ent.label_ == "ORG" and ent.text not in education_entry["degree"]:
                education_entry["institution"] = ent.text
                break
        
        # Extract duration
        year_pattern = r"(?:19|20)\d{2}\s*[-–]\s*(?:19|20)\d{2}|(?:19|20)\d{2}\s*[-–]\s*Present|(?:19|20)\d{2}\s*[-–]\s*Now"
        year_matches = re.search(year_pattern, entry)
        if year_matches:
            education_entry["duration"] = year_matches.group(0)
        
        education_info.append(education_entry)
    
    return education_info

def extract_experience(text):
    """Extract work experience information from resume text."""
    experience_info = []
    
    # First look for a job title and company near the beginning of the resume
    # This is common in modern resume formats where the title/role is prominently displayed
    job_title_patterns = [
        r"(Software Engineer|Software Developer|Web Developer|Full Stack Developer|Frontend Developer|Backend Developer|Senior Developer|IT Specialist|DevOps Engineer|Data Engineer|Data Scientist|Data Analyst)",
        r"(Sr\.|Senior|Junior|Jr\.|Lead) (Engineer|Developer|Programmer|Analyst)",
        r"(Engineer|Developer|Programmer|Analyst|Specialist|Consultant)"
    ]
    
    # Try to find a prominent job title at the beginning of the resume
    top_section = text[:1000]  # First 1000 characters
    found_title = None
    for pattern in job_title_patterns:
        matches = re.search(pattern, top_section, re.IGNORECASE)
        if matches:
            found_title = matches.group(0)
            break
    
    # Look for experience section
    experience_patterns = [
        r"EXPERIENCE(.*?)(?:EDUCATION|SKILLS|PROJECT|CERTIF|ACHIEV|\Z)",
        r"Experience(.*?)(?:Education|Skills|Project|Certif|Achiev|\Z)",
        r"WORK EXPERIENCE(.*?)(?:EDUCATION|SKILLS|PROJECT|CERTIF|ACHIEV|\Z)",
        r"Work Experience(.*?)(?:Education|Skills|Project|Certif|Achiev|\Z)",
        r"EMPLOYMENT(.*?)(?:EDUCATION|SKILLS|PROJECT|CERTIF|ACHIEV|\Z)",
        r"Employment(.*?)(?:Education|Skills|Project|Certif|Achiev|\Z)",
        r"PROFESSIONAL EXPERIENCE(.*?)(?:EDUCATION|SKILLS|PROJECT|CERTIF|ACHIEV|\Z)",
        r"Professional Experience(.*?)(?:Education|Skills|Project|Certif|Achiev|\Z)"
    ]
    
    experience_text = ""
    for pattern in experience_patterns:
        matches = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            experience_text = matches.group(1).strip()
            break
    
    # If we found a title but no standard experience section, create a default entry
    if found_title and not experience_text:
        experience_entry = {
            "title": found_title,
            "company": "Not specified", 
            "duration": "Not specified",
            "description": "Details not found in standard format."
        }
        experience_info.append(experience_entry)
        return experience_info
    
    if not experience_text:
        # If no formal experience section, try to extract professional summary
        summary_patterns = [
            r"(SUMMARY|Summary|PROFILE|Profile|PROFESSIONAL SUMMARY|Professional Summary)(.*?)(?:EXPERIENCE|EDUCATION|SKILLS|\Z)",
            r"(ABOUT ME|About Me|PROFESSIONAL PROFILE|Professional Profile)(.*?)(?:EXPERIENCE|EDUCATION|SKILLS|\Z)"
        ]
        
        summary_text = ""
        for pattern in summary_patterns:
            matches = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                summary_text = matches.group(2).strip()
                break
        
        if summary_text and found_title:
            experience_entry = {
                "title": found_title,
                "company": "Not specified", 
                "duration": "Not specified",
                "description": summary_text
            }
            experience_info.append(experience_entry)
            return experience_info
        elif found_title:
            # Just use the title we found with no description
            experience_entry = {
                "title": found_title,
                "company": "Not specified", 
                "duration": "Not specified",
                "description": ""
            }
            experience_info.append(experience_entry)
            return experience_info
        
        return []
    
    # Split into individual job entries (looking for dates, company names, or job titles as separators)
    job_splits = re.split(r'\n(?=\d{4}|\w+ \d{4}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', experience_text)
    
    for job in job_splits:
        if not job.strip():
            continue
            
        experience_entry = {
            "title": "Not specified",
            "company": "Not specified", 
            "duration": "Not specified",
            "description": ""
        }
        
        lines = job.strip().split('\n')
        
        # First line might contain job title and company
        if lines:
            first_line = lines[0].strip()
            
            # Try to separate title and company if they're on the same line
            if '|' in first_line:
                parts = first_line.split('|')
                experience_entry["title"] = parts[0].strip()
                experience_entry["company"] = parts[1].strip()
            elif ',' in first_line or '-' in first_line or 'at' in first_line.lower():
                separators = [',', '-', ' at ']
                for sep in separators:
                    if sep in first_line:
                        parts = first_line.split(sep, 1)
                        experience_entry["title"] = parts[0].strip()
                        experience_entry["company"] = parts[1].strip()
                        break
            else:
                # Just use the first line as title
                experience_entry["title"] = first_line
            
            # Look for organizations using spaCy
            doc = nlp(job)
            for ent in doc.ents:
                if ent.label_ == "ORG" and experience_entry["company"] == "Not specified":
                    experience_entry["company"] = ent.text
                    break
        
        # Extract duration
        date_pattern = r"(?:19|20)\d{2}\s*[-–]\s*(?:19|20)\d{2}|(?:19|20)\d{2}\s*[-–]\s*Present|(?:19|20)\d{2}\s*[-–]\s*Now"
        date_matches = re.search(date_pattern, job)
        if date_matches:
            experience_entry["duration"] = date_matches.group(0)
        
        # Description is what's left after the first line
        if len(lines) > 1:
            description = "\n".join(lines[1:])
            # Remove any found duration from description
            if experience_entry["duration"] != "Not specified":
                description = description.replace(experience_entry["duration"], "")
            experience_entry["description"] = description.strip()
        
        experience_info.append(experience_entry)
    
    # If no experience entries were found but we did find a title earlier, create a default entry
    if not experience_info and found_title:
        experience_entry = {
            "title": found_title,
            "company": "Not specified", 
            "duration": "Not specified",
            "description": ""
        }
        experience_info.append(experience_entry)
    
    return experience_info

def extract_skills(text):
    """Extract skills from resume using keyword matching."""
    detected_skills = set()
    
    # First use keyword matching
    for skill in SKILL_KEYWORDS:
        # Escape special regex characters
        escaped_skill = re.escape(skill)
        if re.search(r"\b" + escaped_skill + r"\b", text, re.IGNORECASE):
            detected_skills.add(skill)
    
    # Then look for a skills section which might contain skills not in our predefined list
    skills_section_patterns = [
        r"SKILLS(.*?)(?:\n\n|\Z)",
        r"Skills(.*?)(?:\n\n|\Z)",
        r"TECHNICAL SKILLS(.*?)(?:\n\n|\Z)",
        r"Technical Skills(.*?)(?:\n\n|\Z)",
        r"TECHNOLOGIES(.*?)(?:\n\n|\Z)",
        r"Technologies(.*?)(?:\n\n|\Z)",
        r"CORE COMPETENCIES(.*?)(?:\n\n|\Z)",
        r"Core Competencies(.*?)(?:\n\n|\Z)"
    ]
    
    skills_text = ""
    for pattern in skills_section_patterns:
        matches = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            skills_text = matches.group(1).strip()
            break
    
    if skills_text:
        # Skills are often separated by commas, bullets, or new lines
        skill_items = re.split(r',|\n|•|\*|\|', skills_text)
        for item in skill_items:
            clean_item = item.strip()
            if clean_item and len(clean_item) > 2 and not any(char.isdigit() for char in clean_item):
                detected_skills.add(clean_item)
    
    return sorted(list(detected_skills))

def parse_resume(resume_text):
    """Parse resume text and extract key information.
    
    Args:
        resume_text (str): The text content of a resume
        
    Returns:
        dict: Dictionary containing extracted resume information
    """
    result = {}
    
    # Extract basic contact information
    result["email"] = extract_email(resume_text)
    result["phone"] = extract_phone(resume_text)
    
    # Extract name
    result["name"] = extract_name(resume_text)
    
    # Extract work experience
    result["experience"] = extract_experience(resume_text)
    
    # Extract education
    result["education"] = extract_education(resume_text)
    
    # Extract skills
    result["skills"] = extract_skills(resume_text)
    
    return result

# Example usage for testing
if __name__ == "__main__":
    sample_resume = """
    John Doe
    Email: johndoe@example.com
    Phone: (123) 456-7890
    
    EXPERIENCE
    Senior Software Engineer, ABC Technologies
    2019-2022
    - Developed full-stack web applications using React and Node.js
    - Led a team of 5 developers on a major product rewrite
    
    EDUCATION
    Master of Science, Computer Science
    University of Technology, 2016-2018
    
    SKILLS
    Data Analysis, Python, React, JavaScript, Node.js
    """
    
    parsed_resume = parse_resume(sample_resume)
    print(parsed_resume)
