import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.services.file_parser import FileParser

def test_pdf_parsing():
    test_cases = [
        {
            "name": "Standard Format",
            "text": """
            Patient: John Doe   Age: 45Y
            HEMOGLOBIN ........ 14.5 g/dL
            WBC COUNT ......... 8500 /cmm
            PLATELET COUNT .... 250000 /mcL
            NEUTROPHILS ....... 65 %
            LYMPHOCYTES ....... 25 %
            MONOCYTES ......... 8 %
            """,
            "expected": {
                "age": "45",
                "hba": "14.5",
                "hemoglobin": "14.5",
                "wbc": "8500",
                "platelets": "250000",
                "neutrophils": "65",
                "lymphocytes": "25",
                "monocytes": "8"
            }
        },
        {
            "name": "Variation 1 (Units and Spacing)",
            "text": """
            SEX/AGE: M/32 Y
            Hb: 13.8 gm/dl
            TOTAL WBC: 10200
            PLT: 180 X 10^3
            Neutrophil: 70%
            Lymphocyte: 20%
            Monocyte: 5%
            """,
            "expected": {
                "age": "32",
                "hba": "13.8",
                "hemoglobin": "13.8",
                "wbc": "10200",
                "platelets": "180000",
                "neutrophils": "70",
                "lymphocytes": "20",
                "monocytes": "5"
            }
        }
    ]

    for case in test_cases:
        print(f"Testing: {case['name']}")
        
        # Mock PdfReader to return our test text
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = case['text']
        mock_reader.pages = [mock_page]
        
        with patch('pypdf.PdfReader', return_value=mock_reader):
            result = FileParser.parse_pdf("dummy.pdf")
            
            for key, expected_val in case['expected'].items():
                actual_val = result.get(key)
                if actual_val == expected_val:
                    print(f"  [PASS] {key}: {actual_val}")
                else:
                    print(f"  [FAIL] {key}: Expected {expected_val}, got {actual_val}")
        print("-" * 20)

if __name__ == "__main__":
    test_pdf_parsing()
