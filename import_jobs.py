import pandas as pd
import os
from pathlib import Path

# Add the parent directory to the path to allow imports
import sys
sys.path.append(str(Path(__file__).parent))

# Import the database class
from app.db.database import JobSearchDatabase

def import_jobs_from_csv(csv_path):
    """Import job listings from a CSV file into the database.
    
    Args:
        csv_path: Path to the CSV file containing job listings
        
    Returns:
        int: Number of jobs imported
    """
    print(f"Importing jobs from {csv_path}...")
    
    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        return 0
    
    try:
        # Read the CSV file
        jobs_df = pd.read_csv(csv_path)
        print(f"Found {len(jobs_df)} job listings in CSV file")
        
        # Check required columns
        required_columns = ["Title", "Company", "Location", "Job Link", "Description"]
        for col in required_columns:
            if col not in jobs_df.columns:
                print(f"Error: Missing required column: {col}")
                return 0
                
        # Connect to the database
        db = JobSearchDatabase()
        
        # Import each job
        count = 0
        for _, job in jobs_df.iterrows():
            # Convert the job to a dictionary format expected by the database
            job_data = {
                "title": job["Title"],
                "company": job["Company"],
                "location": job["Location"],
                "url": job["Job Link"],
                "description": job["Description"],
                "date_posted": job.get("Posted", ""),
                "match_score": 0
            }
            
            # Add the job to the database
            job_id = db.add_job(job_data)
            if job_id:
                count += 1
                
        # Close the connection
        db.close()
        
        print(f"Successfully imported {count} jobs into the database")
        return count
        
    except Exception as e:
        print(f"Error importing jobs: {e}")
        return 0

if __name__ == "__main__":
    # Path to the CSV file (in the same directory as this script)
    csv_path = os.path.join(os.path.dirname(__file__), "indeed_jobs.csv")
    
    # Import the jobs
    import_jobs_from_csv(csv_path)