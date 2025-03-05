from app.database.job_tracker import add_application, get_applications

# First, add the application with the provided details
add_application("Data Analyst", "Google", "London", "https://joblink.com", "2025-03-04", "2025-03-10")
print("Application added successfully!")

# Then, retrieve and display all applications
applications = get_applications()
print("\nAll Job Applications:")
print("-" * 80)
print("ID | Job Title | Company | Location | Job Link | Status | Applied Date | Follow-up Date")
print("-" * 80)
for app in applications:
    print(" | ".join(str(field) for field in app))