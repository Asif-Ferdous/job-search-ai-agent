import pandas as pd
import sys
import os
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))
from scraper.resume_parser import parse_resume  # Import the resume parser
from db.database import JobSearchDatabase  # Import the database module

def load_jobs(csv_path=None):
    """Load job listings from CSV file or database.
    
    Args:
        csv_path: Path to CSV file with job listings. If None, loads from database.
    
    Returns:
        DataFrame: Pandas DataFrame with job listings
    """
    if csv_path:
        return pd.read_csv(csv_path)
    else:
        # Load from database
        db = JobSearchDatabase()
        jobs = db.get_jobs()
        db.close()
        
        if jobs:
            return pd.DataFrame(jobs)
        else:
            print("No jobs found in database. Please import jobs first.")
            return pd.DataFrame()

def preprocess_job_data(jobs_df):
    """Combine relevant job details into a single text field for better matching."""
    # Check for database vs CSV column names
    title_col = "title" if "title" in jobs_df.columns else "Title"
    desc_col = "description" if "description" in jobs_df.columns else "Description"
    
    jobs_df["job_text"] = jobs_df[title_col] + " " + jobs_df[desc_col].fillna("")
    return jobs_df

def compute_similarity(resume_skills, job_descriptions):
    """Compute similarity between resume skills and job descriptions using TF-IDF."""
    vectorizer = TfidfVectorizer()

    # Convert resume skills list into a text format
    resume_text = " ".join(resume_skills)

    # Combine resume skills with job descriptions
    corpus = [resume_text] + job_descriptions.tolist()

    # Convert to TF-IDF vectors
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Compute cosine similarity (Resume is compared to all jobs)
    similarity_scores = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:]).flatten()

    return similarity_scores

def match_jobs(resume_text=None, resume_id=None, csv_path=None, top_n=5):
    """Match resume with top job postings.
    
    Args:
        resume_text: Raw resume text to parse and match
        resume_id: ID of resume already in database
        csv_path: Path to CSV file with job listings
        top_n: Number of top matches to return
    
    Returns:
        DataFrame: Top job matches with scores
    """
    # Load jobs from CSV or database
    jobs_df = load_jobs(csv_path)
    if jobs_df.empty:
        return pd.DataFrame()
        
    jobs_df = preprocess_job_data(jobs_df)

    # Get resume data from text or database
    if resume_text:
        parsed_resume = parse_resume(resume_text)
    elif resume_id:
        db = JobSearchDatabase()
        resumes = db.get_resumes(limit=1)
        db.close()
        if resumes and len(resumes) > 0:
            parsed_resume = resumes[0]
        else:
            print(f"No resume found with ID {resume_id}")
            return pd.DataFrame()
    else:
        print("Either resume_text or resume_id must be provided")
        return pd.DataFrame()

    resume_skills = parsed_resume["skills"]

    if not resume_skills:
        print("No skills found in resume. Please check the resume content.")
        return pd.DataFrame()  # Return an empty DataFrame if no skills found

    # Compute similarity scores
    similarity_scores = compute_similarity(resume_skills, jobs_df["job_text"])

    # Rank jobs based on similarity scores
    jobs_df["match_score"] = similarity_scores
    
    # Get top jobs
    top_jobs = jobs_df.sort_values(by="match_score", ascending=False).head(top_n)
    
    # Update match scores in database if jobs were loaded from database
    if "id" in jobs_df.columns and csv_path is None:
        db = JobSearchDatabase()
        for idx, job in top_jobs.iterrows():
            db.update_job_status(job["id"], job.get("status", "new"), 
                              f"Match score: {job['match_score']:.2f}")
        db.close()
    
    # Format output based on data source
    if "Title" in top_jobs.columns:
        return top_jobs[["Title", "Company", "Location", "Job Link", "match_score"]]
    else:
        return top_jobs[["title", "company", "location", "url", "match_score"]]

def save_matched_jobs(resume_id, job_ids_with_scores):
    """Save job matches to database.
    
    Args:
        resume_id: ID of the resume
        job_ids_with_scores: Dictionary mapping job IDs to match scores
    
    Returns:
        bool: Success status
    """
    db = JobSearchDatabase()
    success = True
    
    for job_id, score in job_ids_with_scores.items():
        # Update the job with the match score
        success = success and db.update_job_status(
            job_id, 
            "matched", 
            f"Matched with resume {resume_id}. Score: {score:.2f}"
        )
    
    db.close()
    return success

if __name__ == "__main__":
    # Sample resume text (Replace this with real parsed resume text)
    sample_resume = """
    John Doe
    Email: johndoe@example.com
    Phone: (123) 456-7890
    
    EXPERIENCE
    NLP Engineer, 2019-2022
    
    SKILLS
    Data Analysis, Python, Machine Learning, SQL, Cloud Computing, Git, Docker, AWS
    """

    print("Matching resume with jobs...")
    # First, parse and save the resume to the database
    try:
        from scraper.resume_parser import parse_and_save_resume
        parsed_resume, resume_id = parse_and_save_resume(sample_resume)
        print(f"Resume saved with ID: {resume_id}")
        
        # Try to load jobs from database first
        matched_jobs = match_jobs(resume_id=resume_id)
        
        # If no jobs in database, try using CSV
        if matched_jobs.empty:
            csv_path = str(Path(__file__).parent.parent.parent / "indeed_jobs.csv")
            if os.path.exists(csv_path):
                print(f"Using jobs from CSV: {csv_path}")
                matched_jobs = match_jobs(resume_text=sample_resume, csv_path=csv_path)
            else:
                print(f"CSV file not found: {csv_path}")
    except Exception as e:
        print(f"Error: {e}")
        # Fall back to basic matching without database
        matched_jobs = match_jobs(resume_text=sample_resume, 
                               csv_path=str(Path(__file__).parent.parent.parent / "indeed_jobs.csv"))

    if not matched_jobs.empty:
        print("\nTop Matched Jobs:")
        print(matched_jobs.to_string(index=False))
    else:
        print("\nNo relevant job matches found.")
