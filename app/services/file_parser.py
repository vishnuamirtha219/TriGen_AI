import os
import csv
# from pypdf import PdfReader # Uncomment when installed
import re
import sys

def safe_print(*args, **kwargs):
    """Print safely, replacing any characters the console can't encode (e.g. Greek letters from PDFs)."""
    text = ' '.join(str(a) for a in args)
    safe_text = text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace')
    print(safe_text, **kwargs)

class FileParser:
    @staticmethod
    def extract_clinical_markers(text):
        """
        Generic helper to extract blood markers from raw text using regex.
        Supports: HbA, HbS, HbF, WBC, etc.
        """
        data = {}
        # Strategy: Look for the label then find the nearest number
        markers = {
            'hba': [r'HB\s*A\s*(?:\(%\))?\s*[:=-]?\s*(\d{1,3}(?:\.\d{1,2})?)', r'HEMOGLOBIN\s*A\s*(?:\(%\))?\s*[:=-]?\s*(\d{1,3}(?:\.\d{1,2})?)'],
            'hbs': [r'HB\s*S\s*(?:\(%\))?\s*[:=-]?\s*(\d{1,3}(?:\.\d{1,2})?)', r'HEMOGLOBIN\s*S\s*(?:\(%\))?\s*[:=-]?\s*(\d{1,3}(?:\.\d{1,2})?)'],
            'hbf': [r'HB\s*F\s*(?:\(%\))?\s*[:=-]?\s*(\d{1,3}(?:\.\d{1,2})?)', r'HEMOGLOBIN\s*F\s*(?:\(%\))?\s*[:=-]?\s*(\d{1,3}(?:\.\d{1,2})?)']
        }
        
        for key, patterns in markers.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data[key] = match.group(1)
                    break
                
        return data

    @staticmethod
    def parse_fasta(file_path):
        """
        Robustly parses a FASTA/FNA file using Biopython.
        Ignore headers (>), merge multi-line sequences, validate DNA characters.
        Also attempts to extract clinical markers from headers.
        """
        sequence = ""
        clinical_data = {}
        try:
            from Bio import SeqIO
            with open(file_path, 'r') as f:
                content = f.read()
                # Extract any clinical markers from the entire text first
                clinical_data = FileParser.extract_clinical_markers(content)
                
                # Reset and parse with Biopython
                f.seek(0)
                records = list(SeqIO.parse(f, "fasta"))
                if records:
                    # Take the first record for sequence
                    sequence = str(records[0].seq).upper()
                    # Clean sequence to keep only ATCG
                    sequence = "".join(c for c in sequence if c in 'ATCG')
                    
                    # If we didn't get clinical data from the raw search, try the first record's description
                    if not clinical_data:
                        clinical_data = FileParser.extract_clinical_markers(records[0].description)
        except ImportError:
            # Fallback to manual parsing if Biopython is missing (though it should be present)
            print("Biopython not found, falling back to manual parsing.")
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    clinical_data = FileParser.extract_clinical_markers(content)
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith('>'):
                            continue
                        clean_line = "".join(c for c in line.upper() if c in 'ATCG')
                        sequence += clean_line
            except Exception as e:
                print(f"Error in manual fallback: {e}")
        except Exception as e:
            print(f"Error parsing FASTA: {e}")
        
        return sequence, clinical_data

    @staticmethod
    def parse_csv(file_path):
        """
        Parses a CSV Lab Report and returns a dict of parameters.
        Expects columns like: Parameter, Value (or Test, Result)
        Maps various parameter name aliases to standardized field names.
        """
        # Alias map: various CSV parameter names → standardized field names
        alias_map = {
            # Immunity
            'wbc': 'wbc', 'wbc_count': 'wbc', 'total_wbc': 'wbc', 'white_blood_cells': 'wbc',
            'neutrophils': 'neutrophils', 'neutrophil': 'neutrophils', 'neutrophils_%': 'neutrophils',
            'lymphocytes': 'lymphocytes', 'lymphocyte': 'lymphocytes', 'lymphocytes_%': 'lymphocytes',
            'monocytes': 'monocytes', 'monocyte': 'monocytes', 'monocytes_%': 'monocytes',
            'platelets': 'platelets', 'platelet_count': 'platelets', 'plt': 'platelets',
            'hemoglobin': 'hemoglobin', 'hb': 'hemoglobin', 'hgb': 'hemoglobin',
            'igg': 'igg', 'immunoglobulin_g': 'igg',
            'age': 'age', 'patient_age': 'age',
            # Sickle Cell
            'hba': 'hba', 'hb_a': 'hba', 'hemoglobin_a': 'hba',
            'hbs': 'hbs', 'hb_s': 'hbs', 'hemoglobin_s': 'hbs',
            'hbf': 'hbf', 'hb_f': 'hbf', 'hemoglobin_f': 'hbf',
            # LSD parameters
            'beta_glucosidase': 'b_glucosidase', 'b_glucosidase': 'b_glucosidase',
            'β_glucosidase': 'b_glucosidase', 'beta-glucosidase': 'b_glucosidase',
            'β-glucosidase': 'b_glucosidase', 'glucocerebrosidase': 'b_glucosidase',
            'alpha_galactosidase': 'a_galactosidase', 'a_galactosidase': 'a_galactosidase',
            'α_galactosidase': 'a_galactosidase', 'alpha-galactosidase': 'a_galactosidase',
            'α-galactosidase': 'a_galactosidase', 'gla': 'a_galactosidase',
            'liver_size': 'liver_size', 'liver_span': 'liver_size', 'hepatomegaly': 'liver_size',
            'spleen_size': 'spleen_size', 'spleen_length': 'spleen_size', 'splenomegaly': 'spleen_size',
        }

        data = {}
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = [h.strip().lower() for h in reader.fieldnames] if reader.fieldnames else []

                # Detect parameter/value column names
                param_col = None
                val_col = None
                for h in reader.fieldnames or []:
                    hl = h.strip().lower()
                    if hl in ('parameter', 'test', 'test_name', 'marker', 'analyte', 'name'):
                        param_col = h
                    if hl in ('value', 'result', 'observed_value', 'observed', 'level'):
                        val_col = h

                if param_col and val_col:
                    for row in reader:
                        raw_key = row.get(param_col, '').strip().lower().replace(' ', '_').replace('-', '_')
                        raw_key = re.sub(r'[^a-z0-9_]', '', raw_key)
                        val = row.get(val_col, '').strip()
                        if raw_key and val:
                            mapped = alias_map.get(raw_key, raw_key)
                            data[mapped] = val
                else:
                    # Fallback: use first two columns
                    f.seek(0)
                    reader = csv.reader(f)
                    next(reader, None)  # skip header
                    for row in reader:
                        if len(row) >= 2:
                            raw_key = row[0].strip().lower().replace(' ', '_').replace('-', '_')
                            raw_key = re.sub(r'[^a-z0-9_]', '', raw_key)
                            val = row[1].strip()
                            if raw_key and val:
                                mapped = alias_map.get(raw_key, raw_key)
                                data[mapped] = val
        except Exception as e:
            print(f"Error parsing CSV: {e}")
        return data

    @staticmethod
    def parse_pdf(file_path):
        """
        Advanced PDF parser with table structure recognition.
        Uses multiple strategies to accurately extract blood test values.
        """
        data = {}
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            safe_print(f"=== PDF Text Extracted ===\n{text[:500]}...\n")
            
            # Split into lines for structured parsing
            lines = text.split('\n')
            
            # Strategy 1: Line-by-line table parsing
            # Look for lines containing test names and extract the result value
            for i, line in enumerate(lines):
                line_upper = line.upper()
                
                # WBC Count - Look for the line with "WBC COUNT" or "WBC"
                if 'WBC COUNT' in line_upper or 'TOTAL WBC' in line_upper:
                    # Extract numbers from this line, avoiding ranges
                    numbers = re.findall(r'\b(\d{4,6})\b', line)
                    if numbers:
                        # Take the first 4-6 digit number (likely the result)
                        # Skip if it's part of a range pattern
                        for num in numbers:
                            if int(num) >= 1000 and int(num) <= 50000:  # Valid WBC range
                                # Check if this is not part of a range (like "4000 - 10000")
                                if not re.search(rf'{num}\s*-\s*\d+', line):
                                    data['wbc'] = num
                                    safe_print(f"WBC found: {num} from line: {line.strip()}")
                                    break
                
                
                # Neutrophils - Look for percentage or absolute value
                if 'NEUTROPHIL' in line_upper and 'WBC' not in line_upper and 'neutrophils' not in data:
                    # Try multiple patterns
                    # Pattern 1: "73 %"
                    percent_match = re.search(r'\b(\d{1,2})\s*%', line)
                    if percent_match:
                        val = percent_match.group(1)
                        if 20 <= int(val) <= 90:
                            data['neutrophils'] = val
                            safe_print(f"Neutrophils found: {val}% from line: {line.strip()}")
                    else:
                        # Pattern 2: Just the number (like "73" before "40 - 80")
                        # Extract first 1-2 digit number that's not part of a range
                        numbers = re.findall(r'\b(\d{1,2})\b', line)
                        for num in numbers:
                            if 20 <= int(num) <= 90:
                                # Make sure it's not part of a range
                                if not re.search(rf'{num}\s*-\s*\d+', line):
                                    data['neutrophils'] = num
                                    safe_print(f"Neutrophils found: {num} from line: {line.strip()}")
                                    break
                
                # Lymphocytes - Look for percentage or absolute value
                if 'LYMPHOCYTE' in line_upper and 'WBC' not in line_upper and 'lymphocytes' not in data:
                    # Try multiple patterns
                    percent_match = re.search(r'\b(\d{1,2})\s*%', line)
                    if percent_match:
                        val = percent_match.group(1)
                        if 10 <= int(val) <= 50:
                            data['lymphocytes'] = val
                            safe_print(f"Lymphocytes found: {val}% from line: {line.strip()}")
                    else:
                        # Extract first 1-2 digit number that's not part of a range
                        numbers = re.findall(r'\b(\d{1,2})\b', line)
                        for num in numbers:
                            if 10 <= int(num) <= 50:
                                if not re.search(rf'{num}\s*-\s*\d+', line):
                                    data['lymphocytes'] = num
                                    safe_print(f"Lymphocytes found: {num} from line: {line.strip()}")
                                    break
                
                # Monocytes - Look for percentage or absolute value
                if 'MONOCYTE' in line_upper and 'WBC' not in line_upper and 'monocytes' not in data:
                    # Try multiple patterns
                    percent_match = re.search(r'\b(\d{1,2})\s*%', line)
                    if percent_match:
                        val = percent_match.group(1)
                        if 0 <= int(val) <= 15:
                            data['monocytes'] = val
                            safe_print(f"Monocytes found: {val}% from line: {line.strip()}")
                    else:
                        # Extract first 1-2 digit number that's not part of a range
                        # Special handling for "06" or "6"
                        numbers = re.findall(r'\b(0?\d{1,2})\b', line)
                        for num in numbers:
                            num_int = int(num)
                            if 0 <= num_int <= 15:
                                if not re.search(rf'{num}\s*-\s*\d+', line):
                                    data['monocytes'] = str(num_int)  # Convert "06" to "6"
                                    safe_print(f"Monocytes found: {num_int} from line: {line.strip()}")
                                    break

                
                # Age - Look in patient info section
                if 'SEX/AGE' in line_upper or 'AGE' in line_upper:
                    age_match = re.search(r'\b(\d{1,3})\s*Y', line, re.IGNORECASE)
                    if age_match:
                        val = age_match.group(1)
                        if 0 <= int(val) <= 120:  # Valid age range
                            data['age'] = val
                            safe_print(f"Age found: {val} from line: {line.strip()}")
                
                
                # Hemoglobin - Multiple patterns
                if ('HEMOGLOBIN' in line_upper or 'HB' in line_upper or 'HGB' in line_upper) and 'MEAN' not in line_upper and 'hba' not in data:
                    # Try multiple patterns
                    patterns = [
                        r'\b(\d{1,2}\.\d{1})\b',  # 14.5
                        r'\b(\d{1,2}\.\d{2})\b',  # 14.55
                        r'\b(\d{1,2})\s*(?:G/DL|G/L|GM/DL|%)',  # 14 g/dL
                        r'(?:HB|HGB|HEMOGLOBIN)[^\d]*?(\d{1,2}\.\d{1,2})',  # After HB: 14.5
                        r'(?:HB|HGB|HEMOGLOBIN)[^\d]*?(\d{1,2})\s*(?:G|GM)'  # After HB: 14 g
                    ]
                    for pattern in patterns:
                        hb_match = re.search(pattern, line, re.IGNORECASE)
                        if hb_match:
                            val = hb_match.group(1)
                            try:
                                val_float = float(val)
                                if 5.0 <= val_float <= 25.0:  # Valid Hb range
                                    data['hba'] = str(val_float)
                                    data['hemoglobin'] = str(val_float)
                                    safe_print(f"Hemoglobin found: {val_float} from line: {line.strip()}")
                                    break
                            except ValueError:
                                continue
                
                # Platelet Count - Multiple patterns
                if ('PLATELET' in line_upper or 'PLT' in line_upper) and 'platelets' not in data:
                    # Remove commas and spaces for easier matching
                    line_clean = line.replace(',', '').replace(' ', '')
                    line_upper_clean = line_clean.upper()
                    
                    # Try multiple patterns
                    patterns = [
                        r'\b(\d{5,6})\b',  # 250000
                        r'(\d{2,3})X10\^3',  # 250X10^3
                        r'(\d{2,3})\.?\d?X10\^3',  # 250.0X10^3
                        r'(?:PLATELET|PLT)[^\d]*?(\d{5,6})',  # After PLATELET: 250000
                    ]
                    
                    for pattern in patterns:
                        plt_match = re.search(pattern, line_upper_clean, re.IGNORECASE)
                        if plt_match:
                            val = plt_match.group(1)
                            try:
                                val_int = int(float(val))
                                # If value is in thousands (like "250" for 250,000)
                                if 50 <= val_int <= 999:
                                    val_int = val_int * 1000
                                
                                if 50000 <= val_int <= 1000000:  # Valid platelet range
                                    data['platelets'] = str(val_int)
                                    safe_print(f"Platelets found: {val_int} from line: {line.strip()}")
                                    break
                            except ValueError:
                                continue

                
                # IgG - Immunoglobulin
                if 'IGG' in line_upper and 'IMMUNOGLOBULIN' not in line_upper:
                    igg_match = re.search(r'\b(\d{3,4})\b', line)
                    if igg_match:
                        val = igg_match.group(1)
                        if 500 <= int(val) <= 2000:  # Valid IgG range (mg/dL)
                            data['igg'] = val
                            safe_print(f"IgG found: {val} from line: {line.strip()}")

                # === LSD Parameters ===

                # Beta-Glucosidase (Glucocerebrosidase) — Gaucher disease marker
                if any(kw in line_upper for kw in [
                    'GLUCOSIDASE', 'GLUCOCEREBROSIDASE', 'GBA', 'BETA-GLUCOSIDASE',
                    'B-GLUCOSIDASE', 'BETA GLUCOSIDASE', 'ACID BETA', 'B-GLUC',
                    'GLUCOCEREBROSID', 'BETA-GLUC', 'GAUCHER'
                ]) and 'ALPHA' not in line_upper and 'b_glucosidase' not in data:
                    val_match = re.search(r'(\d{1,3}(?:\.\d{1,2})?)', line)
                    if val_match:
                        val = float(val_match.group(1))
                        if 0.1 <= val <= 50.0:  # Valid enzymatic activity range
                            data['b_glucosidase'] = str(val)
                            safe_print(f"Beta-glucosidase found: {val} from line: {line.strip()}")

                # Alpha-Galactosidase — Fabry disease marker
                if any(kw in line_upper for kw in [
                    'GALACTOSIDASE', 'ALPHA-GALACTOSIDASE', 'ALPHA GALACTOSIDASE',
                    'A-GALACTOSIDASE', 'GLA', 'A-GAL', 'ALPHA-GAL', 'FABRY',
                    'A-GLAC', 'ALPHA GAL'
                ]) and 'BETA' not in line_upper and 'a_galactosidase' not in data:
                    val_match = re.search(r'(\d{1,3}(?:\.\d{1,2})?)', line)
                    if val_match:
                        val = float(val_match.group(1))
                        if 0.1 <= val <= 50.0:
                            data['a_galactosidase'] = str(val)
                            safe_print(f"Alpha-galactosidase found: {val} from line: {line.strip()}")

                # Liver Size (span in cm)
                if any(kw in line_upper for kw in [
                    'LIVER', 'HEPATOMEGALY', 'LIVER SPAN', 'LIVER SIZE',
                    'HEPATIC', 'LIVER MEASUREMENT', 'LIVER LENGTH'
                ]) and 'liver_size' not in data:
                    size_match = re.search(r'(\d{1,2}(?:\.\d{1,2})?)\s*(?:CM|cm|centimeter|CMS)?', line)
                    if size_match:
                        val = float(size_match.group(1))
                        if 5.0 <= val <= 30.0:  # Valid liver span range
                            data['liver_size'] = str(val)
                            safe_print(f"Liver size found: {val} from line: {line.strip()}")

                # Spleen Size (length in cm)
                if any(kw in line_upper for kw in [
                    'SPLEEN', 'SPLENOMEGALY', 'SPLEEN SIZE', 'SPLEEN LENGTH',
                    'SPLENIC', 'SPLEEN MEASUREMENT'
                ]) and 'spleen_size' not in data:
                    size_match = re.search(r'(\d{1,2}(?:\.\d{1,2})?)\s*(?:CM|cm|centimeter|CMS)?', line)
                    if size_match:
                        val = float(size_match.group(1))
                        if 3.0 <= val <= 25.0:  # Valid spleen size range
                            data['spleen_size'] = str(val)
                            safe_print(f"Spleen size found: {val} from line: {line.strip()}")

                # Broad fallback: look for enzyme activity units (nmol/hr/mg)
                if ('NMOL' in line_upper or 'ENZYME' in line_upper or 'ACTIVITY' in line_upper) and ('b_glucosidase' not in data or 'a_galactosidase' not in data):
                    val_match = re.search(r'(\d{1,3}(?:\.\d{1,2})?)\s*(?:NMOL|nmol)', line, re.IGNORECASE)
                    if val_match:
                        val = float(val_match.group(1))
                        if 0.1 <= val <= 50.0:
                            if 'b_glucosidase' not in data:
                                data['b_glucosidase'] = str(val)
                                safe_print(f"Enzyme (b_glucosidase fallback): {val} from line: {line.strip()}")
                            elif 'a_galactosidase' not in data:
                                data['a_galactosidase'] = str(val)
                                safe_print(f"Enzyme (a_galactosidase fallback): {val} from line: {line.strip()}")

            
            # Strategy 2: Fallback regex patterns if line-by-line didn't work
            if 'wbc' not in data:
                # Try to find WBC with more context
                wbc_match = re.search(r'WBC\s+Count[^\d]*?(\d{4,6})\s*/cmm', text, re.IGNORECASE)
                if wbc_match:
                    data['wbc'] = wbc_match.group(1)
                    safe_print(f"WBC found (fallback): {wbc_match.group(1)}")
            
            safe_print(f"\n=== Final Parsed Data ===\n{data}\n")
            
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            import traceback
            traceback.print_exc()
            
        return data



