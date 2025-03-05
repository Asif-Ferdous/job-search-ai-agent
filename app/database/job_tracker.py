import sqlite3

DB_NAME = "job_applications.db"

def create_database():
    """Create the job applications database if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            company TEXT,
            location TEXT,
            job_link TEXT,
            status TEXT DEFAULT 'Applied',  -- Status: Applied, Interview, Offer, Rejected
            applied_date TEXT,
            follow_up_date TEXT
        )
    ''')

    conn.commit()
    conn.close()

def add_application(job_title, company, location, job_link, applied_date, follow_up_date):
    """Add a new job application to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO applications (job_title, company, location, job_link, applied_date, follow_up_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (job_title, company, location, job_link, applied_date, follow_up_date))

    conn.commit()
    conn.close()

def get_applications():
    """Retrieve all job applications."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM applications")
    jobs = cursor.fetchall()

    conn.close()
    return jobs

def update_application_status(job_id, new_status):
    """Update the status of a job application."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, job_id))

    conn.commit()
    conn.close()

def delete_application(job_id):
    """Delete a job application from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM applications WHERE id = ?", (job_id,))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()  # Ensure the database is created
    print("Job Application Database is ready!")
