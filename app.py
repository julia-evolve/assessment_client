import streamlit as st
import pandas as pd
import tempfile
import requests
from pathlib import Path



def process_excel_files(file1, file2):
    """
    Process two Excel files and create JSON payloads for each email.
    
    Args:
        file1: First Excel file (competency matrix)
        file2: Second Excel file (questions and answers)
    
    Returns:
        List of tuples containing (email, json_payload)
    """
    # Save uploaded files to temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save first file (competency matrix)
        file1_path = Path(temp_dir) / file1.name
        with open(file1_path, 'wb') as f:
            f.write(file1.getbuffer())
        
        # Save second file (questions and answers)
        file2_path = Path(temp_dir) / file2.name
        with open(file2_path, 'wb') as f:
            f.write(file2.getbuffer())
        
        # Read Excel files
        df_competency = pd.read_excel(file1_path)
        df_qa = pd.read_excel(file2_path)
        
        # Group data by email
        results = []
        competency_matrix = []

        for _, row in df_competency.iterrows():
            competency_matrix.append({
                "name": str(row['name']),
                "level": "Normal",
                "description": str(row['description'])
            })

        if 'Email' in df_qa.columns:
            emails = df_qa['Email'].unique()
            
            for email in emails:
                one_student = df_qa[df_qa['Email'] == email]
  
                # Build JSON structure
                json_payload = {
                    "competency_matrix": competency_matrix,
                    "questions_and_answers": [],
                    "webhook_url": "https://ntfy.sh/assessment"
                }
                
                for _, row in one_student.iterrows():
                    qa_entry = {}
                    if 'Вопрос' in row:
                        qa_entry['question'] = str(row['Вопрос'])
                    if 'Ответ участника' in row:
                        qa_entry['answer'] = str(row['Ответ участника'])
                    if 'Основная компетенция' in row:
                        qa_entry['competency'] = str(row['Основная компетенция'])
                    
                    if qa_entry:
                        json_payload["questions_and_answers"].append(qa_entry)
                
                
                results.append((email, json_payload))
                break
        
        return results


def send_to_assessment_api(email, payload, api_url):
    """
    Send JSON payload to the assessment API.
    
    Args:
        email: Email address
        payload: JSON payload to send
        api_url: API endpoint URL
    
    Returns:
        Response object or error message
    """
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        return response
    except Exception as e:
        return str(e)


def main():
    st.title("Assessment Client - Excel Upload Service")
    st.write("Upload two Excel files to process assessments and send to the API.")
    
    # Configuration section
    st.sidebar.header("Configuration")
    api_url = st.sidebar.text_input(
        "Assessment API URL",
        value="https://evolveaiserver-production.up.railway.app/evaluate_open_assessments",
        help="Enter the API endpoint URL"
    )
    
    # File upload section
    st.header("Upload Excel Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Competency Matrix")
        st.write("Expected columns:")
        st.write("[name, description]")
        file1 = st.file_uploader(
            "Choose competency matrix Excel file",
            type=['xlsx', 'xls'],
            key="file1"
        )
    
    with col2:
        st.subheader("Questions & Answers")
        st.write("[Email, Вопрос,")
        st.write("Ответ участника, Основная компетенция]")
        file2 = st.file_uploader(
            "Choose Q&A Excel file",
            type=['xlsx', 'xls'],
            key="file2"
        )
    
    # Upload button
    if st.button("Upload and Process", type="primary"):
        if file1 is None or file2 is None:
            st.error("Please upload both Excel files before processing.")
        else:
            with st.spinner("Processing files..."):
                try:
                    # Process the Excel files
                    results = process_excel_files(file1, file2)
                    
                    if not results:
                        st.warning("No data found to process. Please check that your Excel files have an 'email' column.")
                    else:
                        st.success(f"Found {len(results)} email(s) to process")
                        
                        # Send each payload to the API
                        progress_bar = st.progress(0)
                        status_container = st.container()
                        
                        for idx, (email, payload) in enumerate(results):
                            with status_container:
                                st.write(f"Processing email: {email}")
                                
                                # Show JSON payload in expander
                                with st.expander(f"View JSON for {email}"):
                                    st.json(payload)
                                
                                # Send to API
                                response = send_to_assessment_api(email, payload, api_url)
                                
                                if isinstance(response, str):
                                    # Error occurred
                                    st.error(f"Error for {email}: {response}")
                                else:
                                    # Check response status
                                    if response.status_code == 200:
                                        st.success(f"✅ Successfully sent data for {email}")
                                    else:
                                        st.warning(f"⚠️ API returned status {response.status_code} for {email}: {response.text}")
                            
                            # Update progress
                            progress_bar.progress((idx + 1) / len(results))
                        
                        st.balloons()
                        st.success("All emails processed!")
                
                except Exception as e:
                    st.error(f"Error processing files: {str(e)}")
                    st.exception(e)
    
    # Information section
    st.divider()
    st.header("How to Use")
    st.markdown("""
    1. **Prepare your Excel files:**
       - File 1 (Competency Matrix): Should contain columns `name`, `description`
       - File 2 (Questions & Answers): Should contain columns `Email`, `Вопрос`, `Ответ участника`, `Основная компетенция`
    
    2. **Upload files:**
       - Drag and drop or browse to select the Excel files
    
    3. **Configure API URL** (optional):
       - Use the sidebar to change the API endpoint if needed
    
    4. **Click "Upload and Process":**
       - The application will process each email in the first file
       - For each email, it creates a JSON payload combining data from both files
       - JSON payloads are sent to the configured API endpoint
    
    5. **Review results:**
       - Check the status messages for each email
       - Expand the JSON viewers to see the exact data being sent
    """)


if __name__ == "__main__":
    main()
