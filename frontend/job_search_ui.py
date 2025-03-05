import streamlit as st
import pandas as pd
import sys
import io
from datetime import datetime
from pathlib import Path
from io import StringIO
from pdfminer.high_level import extract_text

# Add parent directory to path to allow imports from app directory
sys.path.append(str(Path(__file__).parent.parent))
from app.nlp.resume_parser import parse_resume
from app.nlp.job_matcher import match_jobs
from app.database.job_tracker import add_application, get_applications, update_application_status, delete_application

# Streamlit UI Title
st.title("AI Job-Search Assistant 🚀")

# Sidebar for Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Upload Resume", "Matched Jobs", "Track Applications"])

# Home Page
if page == "Home":
    st.write("### Welcome to the AI Job-Search Assistant!")
    st.write(
        "Use this tool to upload your resume, find job matches, and track your job applications."
    )

# Upload Resume Page
elif page == "Upload Resume":
    st.write("## Upload Your Resume")
    uploaded_file = st.file_uploader("Upload a PDF Resume", type=["pdf"])

    if uploaded_file is not None:
        try:
            # Use pdfminer.six for better text extraction
            pdf_bytes = uploaded_file.getvalue()
            resume_text = extract_text(io.BytesIO(pdf_bytes))
            
            # Display the raw extracted text for debugging (can be removed later)
            with st.expander("View Raw Extracted Text"):
                st.text(resume_text)
            
            # Parse Resume
            parsed_resume = parse_resume(resume_text)

            # Show extracted details
            st.write("### Extracted Information")
            st.write(f"**Name:** {parsed_resume.get('name', 'Not detected')}")
            st.write(f"**Email:** {parsed_resume.get('email', 'Not detected')}")
            st.write(f"**Phone:** {parsed_resume.get('phone', 'Not detected')}")
            
            # Show skills with better formatting
            if 'skills' in parsed_resume and parsed_resume['skills']:
                st.write(f"**Skills:** {', '.join(parsed_resume['skills'])}")
            else:
                st.write("**Skills:** None detected")
            
            # Display experience if available
            if 'experience' in parsed_resume and parsed_resume['experience']:
                st.write("### Professional Experience")
                for exp in parsed_resume['experience']:
                    st.markdown(f"""
                    **{exp.get('title', 'Position')}** at *{exp.get('company', 'Company')}*  
                    {exp.get('duration', '')}  
                    {exp.get('description', '')}
                    """)
            
            # Display education if available
            if 'education' in parsed_resume and parsed_resume['education']:
                st.write("### Education")
                for edu in parsed_resume['education']:
                    st.markdown(f"""
                    **{edu.get('degree', 'Degree')}** - *{edu.get('institution', 'Institution')}*  
                    {edu.get('duration', '')}
                    """)

            # Save parsed skills for job matching
            st.session_state["parsed_resume"] = parsed_resume
            
        except Exception as e:
            st.error(f"Error processing PDF: {e}")
            st.info("Please make sure you're uploading a valid PDF file.")

# Matched Jobs Page
elif page == "Matched Jobs":
    st.write("## Find Matched Jobs")
    if "parsed_resume" not in st.session_state:
        st.write("⚠ Please upload your resume first!")
    else:
        parsed_resume = st.session_state["parsed_resume"]
        matched_jobs = match_jobs(" ".join(parsed_resume["skills"]))

        if not matched_jobs.empty:
            st.write("### Top Matched Jobs")
            st.dataframe(matched_jobs)

            # Apply for jobs
            selected_job = st.selectbox("Select a Job to Apply", matched_jobs["Title"].tolist())
            if st.button("Apply for Selected Job"):
                job_data = matched_jobs[matched_jobs["Title"] == selected_job].iloc[0]
                add_application(
                    job_data["Title"], job_data["Company"], job_data["Location"], job_data["Job Link"]
                )
                st.success(f"Applied for {selected_job} at {job_data['Company']}!")
        else:
            st.write("No matching jobs found.")

# Application Tracker Page
elif page == "Track Applications":
    st.write("## Your Tracked Job Applications")
    applications = get_applications()
    
    if applications:
        df = pd.DataFrame(applications, columns=["ID", "Job Title", "Company", "Location", "Job Link", "Status", "Applied Date", "Follow-Up Date"])
        st.dataframe(df)

        job_id = st.number_input("Enter Job ID to Update/Delete", min_value=1)
        action = st.radio("Select Action", ["Update Status", "Delete Application"])

        if action == "Update Status":
            new_status = st.selectbox("Select New Status", ["Applied", "Interview Scheduled", "Offer", "Rejected"])
            if st.button("Update Status"):
                update_application_status(job_id, new_status)
                st.success(f"Updated Job ID {job_id} to status '{new_status}'")
        
        elif action == "Delete Application":
            if st.button("Delete Application"):
                delete_application(job_id)
                st.warning(f"Deleted Job ID {job_id}")

    else:
        st.write("No applications tracked yet.")
