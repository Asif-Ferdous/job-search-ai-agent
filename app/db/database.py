import sqlite3
import os
import json
from pathlib import Path

class JobSearchDatabase:
    """Database handler for job search application."""
    
    def __init__(self, db_path=None):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            # Use default path in the project directory
            root_dir = Path(__file__).parent.parent.parent
            db_path = os.path.join(root_dir, "job_search.db")
            
        self.db_path = db_path
        self.conn = None
        
        # Initialize database
        self.connect()
        self.create_tables()
        
    def connect(self):
        """Establish connection to database."""
        self.conn = sqlite3.connect(self.db_path)
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Return rows as dictionaries
        self.conn.row_factory = sqlite3.Row
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            
    def create_tables(self):
        """Create required tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create jobs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            description TEXT,
            url TEXT,
            date_posted TEXT,
            date_scraped TEXT,
            applied INTEGER DEFAULT 0,
            match_score REAL DEFAULT 0,
            status TEXT DEFAULT 'new',
            notes TEXT
        )
        ''')
        
        # Create resumes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            skills TEXT,
            organizations TEXT,
            file_path TEXT,
            date_parsed TEXT
        )
        ''')
        
        self.conn.commit()
    
    def add_job(self, job_data):
        """Add a new job listing to the database.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            id: ID of the inserted job
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        INSERT INTO jobs (title, company, location, description, url, 
                         date_posted, date_scraped, match_score)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
        ''', (
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data.get('description', ''),
            job_data.get('url', ''),
            job_data.get('date_posted', ''),
            job_data.get('match_score', 0)
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def add_resume(self, resume_data):
        """Add a parsed resume to the database.
        
        Args:
            resume_data: Dictionary containing resume information
            
        Returns:
            id: ID of the inserted resume
        """
        cursor = self.conn.cursor()
        
        # Convert lists/dicts to JSON strings for storage
        skills = json.dumps(resume_data.get('skills', []))
        organizations = json.dumps(resume_data.get('organizations', []))
        
        cursor.execute('''
        INSERT INTO resumes (name, email, phone, skills, organizations, file_path, date_parsed)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            resume_data.get('name', ''),
            resume_data.get('email', ''),
            resume_data.get('phone', ''),
            skills,
            organizations,
            resume_data.get('file_path', '')
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_jobs(self, filters=None, limit=100):
        """Get jobs matching the specified filters.
        
        Args:
            filters: Dictionary of column/value pairs
            limit: Maximum number of results to return
            
        Returns:
            List of job dictionaries
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM jobs"
        params = []
        
        if filters:
            conditions = []
            for column, value in filters.items():
                conditions.append(f"{column} = ?")
                params.append(value)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY date_scraped DESC LIMIT {limit}"
        
        cursor.execute(query, params)
        
        # Convert rows to dictionaries
        return [dict(row) for row in cursor.fetchall()]
    
    def get_resumes(self, limit=10):
        """Get parsed resumes from the database.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of resume dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM resumes ORDER BY date_parsed DESC LIMIT ?", (limit,))
        
        results = []
        for row in cursor.fetchall():
            resume_dict = dict(row)
            # Parse JSON strings back to Python objects
            resume_dict['skills'] = json.loads(resume_dict['skills'])
            resume_dict['organizations'] = json.loads(resume_dict['organizations'])
            results.append(resume_dict)
            
        return results
    
    def update_job_status(self, job_id, status, notes=None):
        """Update the status of a job.
        
        Args:
            job_id: ID of the job to update
            status: New status ('new', 'applied', 'interview', 'rejected', 'offer')
            notes: Optional notes about the status change
        
        Returns:
            bool: Success status
        """
        cursor = self.conn.cursor()
        
        update_fields = ["status = ?"]
        params = [status]
        
        if notes is not None:
            update_fields.append("notes = ?")
            params.append(notes)
            
        # Add the job_id at the end of params
        params.append(job_id)
        
        cursor.execute(
            f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = ?", 
            params
        )
        
        self.conn.commit()
        return cursor.rowcount > 0
        
# Example usage
if __name__ == "__main__":
    db = JobSearchDatabase()
    
    # Add a sample job
    job_id = db.add_job({
        'title': 'Python Developer',
        'company': 'Tech Co',
        'location': 'Remote',
        'description': 'Looking for an experienced Python developer...',
        'url': 'https://example.com/job/123',
        'date_posted': '2023-05-20',
        'match_score': 0.85
    })
    
    print(f"Added job with ID: {job_id}")
    
    # Get all jobs
    jobs = db.get_jobs()
    print(f"Found {len(jobs)} jobs")
    
    # Close connection
    db.close()