# app.py
from flask import Flask, render_template, request, send_file
import os
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400
    
    if not allowed_file(file.filename):
        return 'Invalid file type. Please upload a PDF.', 400
    
    # Save uploaded file
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, 'input.pdf')
    file.save(pdf_path)
    
    try:
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(pdf_path)
        
        # Save extracted text to file
        output_path = os.path.join(temp_dir, 'extracted_text.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        # Return the text file
        return send_file(
            output_path,
            as_attachment=True,
            download_name='extracted_text.txt',
            mimetype='text/plain'
        )
    
    finally:
        # Clean up temporary files
        import shutil
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5030, debug=True)

