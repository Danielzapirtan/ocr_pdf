#!/usr/bin/env python3
"""
OCR PDF CLI Application

This application extracts text from PDF files. If the PDF contains searchable text,
it extracts it directly. If not, it uses OCR to convert images to text.
The extracted text is saved as a TXT file in the current directory.

Requirements:
- pip install PyPDF2 pytesseract pdf2image pillow
- Tesseract OCR installed on system
"""

import os
import sys
from pathlib import Path
import argparse
from typing import Optional

try:
    import PyPDF2
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
except ImportError as e:
    print(f"Error: Missing required library. Please install dependencies:")
    print("pip install PyPDF2 pytesseract pdf2image pillow")
    print(f"Missing: {e.name}")
    sys.exit(1)


class PDFTextExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.pdf_name = self.pdf_path.stem
        self.output_path = Path.cwd() / f"{self.pdf_name}.txt"
        
    def validate_pdf(self) -> bool:
        """Validate if the PDF file exists and is readable."""
        if not self.pdf_path.exists():
            print(f"Error: PDF file '{self.pdf_path}' not found.")
            return False
            
        if not self.pdf_path.suffix.lower() == '.pdf':
            print(f"Error: '{self.pdf_path}' is not a PDF file.")
            return False
            
        return True
    
    def extract_text_from_pdf(self) -> Optional[str]:
        """Extract text directly from PDF if it contains searchable text."""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                print(f"Checking {len(pdf_reader.pages)} pages for extractable text...")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n--- Page {page_num} ---\n"
                        text += page_text
                        
                # Check if we found meaningful text (not just whitespace)
                if text.strip():
                    print(f"✓ Found extractable text in PDF")
                    return text
                else:
                    print("✗ No extractable text found in PDF")
                    return None
                    
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None
    
    def ocr_pdf_to_text(self) -> Optional[str]:
        """Convert PDF to images and use OCR to extract text."""
        try:
            print("Converting PDF to images for OCR...")
            
            # Convert PDF to images
            images = convert_from_path(self.pdf_path, dpi=300, fmt='jpeg')
            
            if not images:
                print("Error: Could not convert PDF to images")
                return None
                
            print(f"Processing {len(images)} pages with OCR...")
            
            full_text = ""
            for page_num, image in enumerate(images, 1):
                print(f"Processing page {page_num}/{len(images)}...")
                
                # Use OCR to extract text from image
                page_text = pytesseract.image_to_string(image, lang='eng')
                
                if page_text.strip():
                    full_text += f"\n--- Page {page_num} ---\n"
                    full_text += page_text
                    
            if full_text.strip():
                print("✓ OCR completed successfully")
                return full_text
            else:
                print("✗ No text could be extracted via OCR")
                return None
                
        except Exception as e:
            print(f"Error during OCR processing: {e}")
            if "tesseract" in str(e).lower():
                print("Note: Make sure Tesseract OCR is installed on your system")
                print("Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
                print("macOS: brew install tesseract")
                print("Linux: sudo apt-get install tesseract-ocr")
            return None
    
    def save_text_to_file(self, text: str) -> bool:
        """Save extracted text to a TXT file."""
        try:
            with open(self.output_path, 'w', encoding='utf-8') as file:
                file.write(text)
            
            print(f"✓ Text saved to: {self.output_path}")
            print(f"  File size: {self.output_path.stat().st_size} bytes")
            return True
            
        except Exception as e:
            print(f"Error saving text file: {e}")
            return False
    
    def process(self) -> bool:
        """Main processing method."""
        if not self.validate_pdf():
            return False
            
        print(f"Processing PDF: {self.pdf_path}")
        print(f"Output will be saved as: {self.output_path}")
        print("-" * 50)
        
        # First, try to extract text directly
        text = self.extract_text_from_pdf()
        
        # If no text found, use OCR
        if not text:
            print("\nFalling back to OCR...")
            text = self.ocr_pdf_to_text()
            
        if not text:
            print("✗ Failed to extract any text from the PDF")
            return False
            
        # Save the extracted text
        return self.save_text_to_file(text)


def prompt_for_pdf_path() -> str:
    """Prompt user for PDF file path."""
    while True:
        pdf_path = input("Enter the path to your PDF file: ").strip()
        
        if not pdf_path:
            print("Please enter a valid path.")
            continue
            
        # Remove quotes if present
        pdf_path = pdf_path.strip('"\'')
        
        # Expand user path (~)
        pdf_path = os.path.expanduser(pdf_path)
        
        return pdf_path


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files using direct extraction or OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                          # Interactive mode
  python app.py document.pdf             # Process specific file
  python app.py /path/to/document.pdf    # Process file with full path
        """
    )
    
    parser.add_argument(
        'pdf_path',
        nargs='?',
        help='Path to the PDF file to process'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='OCR PDF CLI 1.0.0'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("OCR PDF CLI - Text Extraction Tool")
    print("=" * 60)
    
    # Get PDF path from argument or prompt user
    if args.pdf_path:
        pdf_path = args.pdf_path
    else:
        pdf_path = prompt_for_pdf_path()
    
    # Process the PDF
    extractor = PDFTextExtractor(pdf_path)
    success = extractor.process()
    
    print("-" * 50)
    if success:
        print("✓ Processing completed successfully!")
    else:
        print("✗ Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()