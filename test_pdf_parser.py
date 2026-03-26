"""
Test script to verify PDF parsing for blood reports.
This will show exactly what data is being extracted from your PDF.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.file_parser import FileParser

def test_pdf_parser(pdf_path):
    """Test the PDF parser and show extracted data"""
    print("=" * 60)
    print("PDF PARSER TEST")
    print("=" * 60)
    print(f"\nTesting file: {pdf_path}\n")
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return
    
    # Parse the PDF
    print("Parsing PDF...")
    print("-" * 60)
    data = FileParser.parse_pdf(pdf_path)
    print("-" * 60)
    
    # Display results
    print("\n" + "=" * 60)
    print("EXTRACTED DATA")
    print("=" * 60)
    
    if data:
        for key, value in data.items():
            print(f"  {key:15s} = {value}")
    else:
        print("  No data extracted!")
    
    print("\n" + "=" * 60)
    print("FIELD CHECK")
    print("=" * 60)
    
    # Check specific fields
    fields_to_check = ['wbc', 'neutrophils', 'lymphocytes', 'monocytes', 
                       'platelets', 'hemoglobin', 'hba', 'age']
    
    for field in fields_to_check:
        status = "✓ FOUND" if field in data else "✗ MISSING"
        value = data.get(field, "N/A")
        print(f"  {field:15s}: {status:12s} Value: {value}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default path - update this to your PDF location
        pdf_path = input("Enter the full path to your blood report PDF: ")
    
    test_pdf_parser(pdf_path)
