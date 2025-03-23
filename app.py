import gradio as gr
import os
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def extract_text_from_pdf(pdf_path):
    text = []
    
    # First try PyPDF2 for text extraction
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text.strip():
                text.append(page_text)
    
    # If no text was extracted, use OCR
    if not any(text):
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        
        # Perform OCR on each image
        for image in images:
            text.append(pytesseract.image_to_string(image))
    
    return '\n'.join(text)

def process_pdf(file):
    if not allowed_file(file.name):
        return 'Invalid file type. Please upload a PDF.'
    
    # Save uploaded file
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, 'input.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(file.read())
    
    try:
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(pdf_path)
        
        # Save extracted text to file
        output_path = os.path.join(temp_dir, 'extracted_text.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        # Return the text file
        return output_path
    
    finally:
        # Clean up temporary files
        import shutil
        shutil.rmtree(temp_dir)

# Gradio Interface
iface = gr.Interface(
    fn=process_pdf,
    inputs=gr.File(label="Upload PDF"),  # Use gr.File for file upload
    outputs=gr.File(label="Download Extracted Text"),  # Use gr.File for file download
    title="PDF Text Extractor",
    description="Upload a PDF file to extract text from it. The extracted text will be available for download as a .txt file."
)

# Launch the Gradio app
iface.launch(debug=True)