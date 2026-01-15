from flask import Flask, request, send_file, render_template_string
import os
import io
from werkzeug.utils import secure_filename
import PyPDF2
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PDF to Text Converter</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .upload-form {
            margin-top: 30px;
        }
        input[type="file"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 2px dashed #ccc;
            border-radius: 4px;
            cursor: pointer;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
        }
        button:hover {
            background-color: #45a049;
        }
        .info {
            margin-top: 20px;
            padding: 15px;
            background-color: #e7f3ff;
            border-left: 4px solid #2196F3;
            border-radius: 4px;
        }
        .error {
            color: #d32f2f;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 PDF to Text Converter</h1>
        <div class="info">
            <strong>Features:</strong>
            <ul>
                <li>Extract text from searchable PDFs</li>
                <li>OCR for scanned/image-based PDFs</li>
                <li>Max file size: 16MB</li>
            </ul>
        </div>
        <form class="upload-form" method="POST" enctype="multipart/form-data">
            <input type="file" name="pdf" accept=".pdf" required>
            <button type="submit">Convert to Text</button>
        </form>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
'''

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF, using OCR if necessary"""
    text = ""
    
    try:
        # First, try extracting text directly
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        
        # If no text was extracted, use OCR
        if not text.strip():
            print("No text found, using OCR...")
            images = convert_from_bytes(pdf_bytes)
            for i, image in enumerate(images):
                print(f"Processing page {i+1}/{len(images)} with OCR...")
                page_text = pytesseract.image_to_string(image)
                text += f"--- Page {i+1} ---\n{page_text}\n\n"
        
        return text.strip()
    
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'pdf' not in request.files:
            return render_template_string(HTML_TEMPLATE, error="No file uploaded")
        
        file = request.files['pdf']
        
        if file.filename == '':
            return render_template_string(HTML_TEMPLATE, error="No file selected")
        
        if not file.filename.lower().endswith('.pdf'):
            return render_template_string(HTML_TEMPLATE, error="Please upload a PDF file")
        
        try:
            # Read PDF bytes
            pdf_bytes = file.read()
            
            # Extract text
            text = extract_text_from_pdf(pdf_bytes)
            
            if not text:
                return render_template_string(HTML_TEMPLATE, error="No text could be extracted from the PDF")
            
            # Create text file
            filename = secure_filename(file.filename)
            txt_filename = os.path.splitext(filename)[0] + '.txt'
            
            # Send as download
            return send_file(
                io.BytesIO(text.encode('utf-8')),
                mimetype='text/plain',
                as_attachment=True,
                download_name=txt_filename
            )
        
        except Exception as e:
            return render_template_string(HTML_TEMPLATE, error=str(e))
    
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # Run with ngrok integration for Colab
    try:
        from google.colab.output import eval_js
        print("Running in Google Colab - starting with pyngrok...")
        from pyngrok import ngrok
        
        # Set up ngrok tunnel
        public_url = ngrok.connect(5000)
        print(f"\n🌐 Your app is publicly available at: {public_url}\n")
        
        app.run(port=5000)
    except ImportError:
        # Not in Colab, run normally
        print("Running locally at http://127.0.0.1:5000")
        app.run(debug=True, port=5000)
