from app.database.job_tracker import get_applications

def main():
    """Get all job applications and display them"""
    applications = get_applications()
    
    # Print header
    print(f"{'ID':<5} {'Job Title':<30} {'Company':<20} {'Location':<20} {'Status':<15} {'Applied Date':<15}")
    print("-" * 105)
    
    # Print each application
    for app in applications:
        app_id, job_title, company, location, job_link, status, applied_date, follow_up_date = app
        print(f"{app_id:<5} {job_title[:28]:<30} {company[:18]:<20} {location[:18]:<20} {status:<15} {applied_date:<15}")
    
    print(f"\nTotal Applications: {len(applications)}")

if __name__ == "__main__":
    main()