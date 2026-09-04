import fitz  # PyMuPDF
from docx import Document

def read_pdf(uploaded_file):
    """
    Extracts plain text from an uploaded PDF file stream.
    """
    text = ""
    try:
        # Open PDF from stream
        pdf_doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in pdf_doc:
            text += page.get_text()
        pdf_doc.close()
    except Exception as e:
        text = f"Error reading PDF: {str(e)}"
    return text


def read_docx(uploaded_file):
    """
    Extracts plain text from an uploaded DOCX file stream.
    """
    text = ""
    try:
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        text = f"Error reading DOCX: {str(e)}"
    return text
