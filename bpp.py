#!/usr/bin/env python3
"""
PDF Text Extraction CLI Application

This application extracts text from PDF files with searchable content.
It separates main content from supplementary elements like tables, figures,
and mirrors, placing supplementary content after the main text.
The extracted text is saved as a TXT file in the current directory.

Requirements:
- pip install PyPDF2
"""

import os
import sys
import re
from pathlib import Path
import argparse
from typing import Optional, Tuple, List

try:
    import PyPDF2
except ImportError as e:
    print(f"Error: Missing required library. Please install dependencies:")
    print("pip install PyPDF2")
    print(f"Missing: {e.name}")
    sys.exit(1)


class PDFTextExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.pdf_name = self.pdf_path.stem
        self.output_path = Path.cwd() / f"{self.pdf_name}.txt"
        
        # Patterns to identify supplementary content
        self.table_patterns = [
            r'(?i)\btable\s+\d+',
            r'(?i)\bfigure\s+\d+',
            r'(?i)\bappendix\s+[a-z\d]+',
            r'(?i)\bsource:',
            r'(?i)\bnote:',
            r'(?i)\blegend:',
        ]
        
        # Patterns for content that should be moved to end
        self.supplementary_patterns = [
            r'(?i)^\s*table\s+\d+.*$',
            r'(?i)^\s*figure\s+\d+.*$',
            r'(?i)^\s*chart\s+\d+.*$',
            r'(?i)^\s*diagram\s+\d+.*$',
            r'(?i)^\s*appendix\s+[a-z\d]+.*$',
            r'(?i)^\s*references?\s*$',
            r'(?i)^\s*bibliography\s*$',
            r'(?i)^\s*index\s*$',
            r'(?i)^\s*glossary\s*$',
        ]
        
    def validate_pdf(self) -> bool:
        """Validate if the PDF file exists and is readable."""
        if not self.pdf_path.exists():
            print(f"Error: PDF file '{self.pdf_path}' not found.")
            return False
            
        if not self.pdf_path.suffix.lower() == '.pdf':
            print(f"Error: '{self.pdf_path}' is not a PDF file.")
            return False
            
        return True
    
    def is_supplementary_content(self, text_block: str) -> bool:
        """Check if a text block contains supplementary content."""
        text_lines = text_block.strip().split('\n')
        
        for line in text_lines[:3]:  # Check first 3 lines
            line = line.strip()
            for pattern in self.supplementary_patterns:
                if re.search(pattern, line):
                    return True
        
        # Check for table-like structures (multiple columns of data)
        numeric_lines = 0
        for line in text_lines:
            # Count lines that seem to be tabular data
            if re.search(r'\d+[\s\t]+\d+', line) or line.count('\t') > 2:
                numeric_lines += 1
        
        # If more than 30% of lines look tabular, consider it supplementary
        if len(text_lines) > 3 and numeric_lines / len(text_lines) > 0.3:
            return True
            
        return False
    
    def clean_text_block(self, text: str) -> str:
        """Clean and normalize a text block."""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove page headers/footers that might be repeated
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip likely headers/footers
            if (len(line) < 3 or 
                re.match(r'^\d+$', line) or  # Page numbers
                re.match(r'^page\s+\d+', line.lower()) or
                line.lower() in ['header', 'footer']):
                continue
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def separate_content(self, text: str) -> Tuple[str, str]:
        """Separate main content from supplementary content."""
        if not text.strip():
            return "", ""
            
        # Split text into blocks (by double newlines or page markers)
        blocks = re.split(r'\n\s*---\s*Page\s+\d+\s*---\s*\n', text)
        
        main_content = []
        supplementary_content = []
        
        for i, block in enumerate(blocks):
            if not block.strip():
                continue
                
            # Add page marker back (except for first block)
            if i > 0:
                page_match = re.search(r'Page\s+(\d+)', text)
                if page_match:
                    block = f"\n--- Page {i} ---\n" + block
            
            cleaned_block = self.clean_text_block(block)
            
            if self.is_supplementary_content(cleaned_block):
                supplementary_content.append(cleaned_block)
            else:
                main_content.append(cleaned_block)
        
        main_text = '\n\n'.join(main_content).strip()
        supplementary_text = '\n\n'.join(supplementary_content).strip()
        
        return main_text, supplementary_text
    
    def extract_text_from_pdf(self) -> Optional[str]:
        """Extract text directly from PDF and organize it."""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                raw_text = ""
                
                print(f"Extracting text from {len(pdf_reader.pages)} pages...")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            raw_text += f"\n--- Page {page_num} ---\n"
                            raw_text += page_text
                    except Exception as e:
                        print(f"Warning: Could not extract text from page {page_num}: {e}")
                        continue
                        
                # Check if we found meaningful text
                if not raw_text.strip():
                    print("✗ No extractable text found in PDF")
                    return None
                
                print(f"✓ Successfully extracted text from PDF")
                
                # Separate main content from supplementary content
                main_content, supplementary_content = self.separate_content(raw_text)
                
                # Combine with supplementary content at the end
                final_text = main_content
                if supplementary_content:
                    final_text += f"\n\n{'='*60}\nSUPPLEMENTARY CONTENT\n{'='*60}\n\n"
                    final_text += supplementary_content
                
                print(f"✓ Content organized: main content and supplementary sections separated")
                return final_text
                    
        except Exception as e:
            print(f"Error reading PDF: {e}")
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
        
        # Extract and organize text
        text = self.extract_text_from_pdf()
            
        if not text:
            print("✗ Failed to extract any text from the PDF")
            print("Note: This tool only works with PDFs that contain searchable text.")
            print("For scanned PDFs, you would need OCR capabilities.")
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
        description="Extract text from PDF files with searchable content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                          # Interactive mode
  python app.py document.pdf             # Process specific file
  python app.py /path/to/document.pdf    # Process file with full path

Note: This tool only works with PDFs containing searchable text.
For scanned PDFs, OCR tools would be required.
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
        version='PDF Text Extractor 2.0.0'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PDF Text Extractor - Searchable Text Only")
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
        print("✓ Main content and supplementary elements have been organized")
    else:
        print("✗ Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()