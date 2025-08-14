import os
import PyPDF2
import docx

def validate_submission(file_path, assignment):
    allowed_extensions = ['.pdf', '.docx']
    _, ext = os.path.splitext(file_path)
    grade = 0
    feedback = ""

    # 1. File format check
    if ext.lower() not in allowed_extensions:
        feedback += "Unsupported file format. Only PDF and DOCX files are allowed. "
    else:
        grade += 1  # Award 1 mark for correct file format

    # Extract text based on file type
    if ext.lower() == '.pdf':
        text = extract_text_pdf(file_path)
    elif ext.lower() == '.docx':
        text = extract_text_docx(file_path)
    else:
        text = ""  # Default to empty string if extraction fails

    # 2. Word count check
    word_count = len(text.split())
    required_word_count = 500
    if word_count >= required_word_count:
        grade += 1  # Award 1 mark for sufficient word count
        feedback += f"Word count is sufficient ({word_count} words). "
    else:
        feedback += f"Word count is below {required_word_count}. Current count: {word_count}. "
        return grade, feedback  # Early exit to allow resubmission

    # 3. Keyword check
    keywords = assignment.get_required_keywords_list()
    keyword_present = all(keyword in text.lower() for keyword in keywords)
    if keyword_present:
        grade += 2  # Award 2 marks if all required keywords are present
        feedback += "All required keywords are present. "
    else:
        missing_keywords = [kw for kw in keywords if kw not in text.lower()]
        feedback += f"Missing keywords: {', '.join(missing_keywords)}. "

    # Final mark for other evaluation criteria (discretionary 1 mark)
    if grade <= 4:
        grade += 1  # Award 1 discretionary mark if other criteria met

    return grade, feedback

def extract_text_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
    return text

def extract_text_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def compare_files(expected_path, uploaded_path):
    """
    Compare the content of the expected solution and uploaded file.
    For simplicity, this checks byte-by-byte equality.
    You can add more sophisticated logic like comparing text content or applying rules for grading.
    """
    try:
        with open(expected_path, 'rb') as expected_file, open(uploaded_path, 'rb') as uploaded_file:
            return expected_file.read() == uploaded_file.read()
    except Exception as e:
        return False
