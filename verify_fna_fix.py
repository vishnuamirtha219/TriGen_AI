from app.services.file_parser import FileParser
import os

# Create a sample FNA file with clinical markers in the header
sample_content = """>Seq1 HbA: 95.5, HbS: 0.5, HbF: 4.0
ATGCGATCGATCGATCGATCGGTGATCGATCGATCG
"""

test_file = "test_clinical.fna"
with open(test_file, "w") as f:
    f.write(sample_content)

print(f"Testing {test_file}...")
seq, clinical_data = FileParser.parse_fasta(test_file)

print(f"Extracted Sequence: {seq}")
print(f"Extracted Clinical Data: {clinical_data}")

# Cleanup
os.remove(test_file)

if clinical_data.get('hba') == '95.5' and clinical_data.get('hbs') == '0.5' and clinical_data.get('hbf') == '4.0':
    print("\nSUCCESS: Clinical markers extracted correctly from FNA header.")
else:
    print("\nFAILURE: Clinical markers not extracted correctly.")
