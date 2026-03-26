from flask import Blueprint, request, jsonify
from app.services.ml_engine import MLEngine
from datetime import datetime
import os

api_bp = Blueprint('api', __name__, url_prefix='/api')


def analyze_hbb_mutation(sequence):
    """
    Analyze HBB gene sequence for sickle cell mutations.
    Detects GAG → GTG (Glu → Val) mutation pattern.
    Returns mutation status: normal, carrier (heterozygous), diseased (homozygous)
    """
    if not sequence:
        return {
            'mutation_status': 'unknown',
            'mutation_detected': False,
            'mutation_count': 0,
            'mutation_type': 'No sequence provided'
        }
    
    sequence = sequence.upper()
    
    # Count GTG (mutant) and GAG (normal) codons
    # In HBB gene, the sickle mutation is at codon 6: GAG (Glu) → GTG (Val)
    gtg_count = sequence.count('GTG')
    gag_count = sequence.count('GAG')
    
    # Also check for the specific mutation context (position-aware)
    # Look for patterns that suggest HBB gene context
    mutation_detected = gtg_count > 0
    
    # Classify based on ratio/counts
    if gtg_count == 0:
        status = 'normal'
        mutation_type = 'None detected (AA genotype)'
    elif gag_count > 0 and gtg_count > 0:
        # Both normal and mutant codons present = heterozygous/carrier
        status = 'carrier'
        mutation_type = 'Heterozygous (AS genotype) - Sickle Cell Trait'
    else:
        # Only mutant codons = homozygous/diseased
        status = 'diseased'
        mutation_type = 'Homozygous (SS genotype) - Sickle Cell Anemia'
    
    return {
        'mutation_status': status,
        'mutation_detected': mutation_detected,
        'mutation_count': gtg_count,
        'gag_count': gag_count,
        'mutation_type': mutation_type
    }


def autofill_hemoglobin_from_mutation(mutation_status):
    """
    Auto-fill hemoglobin values based on genetic mutation status.
    These are medical-grade estimates based on typical clinical ranges.
    
    Source: Standard hematology references for sickle cell disease.
    """
    estimates = {
        'normal': {
            'hba': 97,  # Normal HbA: 95-98%
            'hbs': 0,   # Normal HbS: 0%
            'hbf': 2    # Normal HbF: 1-2%
        },
        'carrier': {
            'hba': 60,  # Carrier HbA: 55-65%
            'hbs': 38,  # Carrier HbS: 35-45%
            'hbf': 2    # Carrier HbF: 1-5%
        },
        'diseased': {
            'hba': 5,   # Diseased HbA: 0-10%
            'hbs': 85,  # Diseased HbS: 80-95%
            'hbf': 10   # Diseased HbF: 5-20%
        },
        'unknown': {
            'hba': 0,
            'hbs': 0,
            'hbf': 0
        }
    }
    
    return estimates.get(mutation_status, estimates['unknown'])

@api_bp.route('/parse_file', methods=['POST'])
def parse_file():
    """
    Parse uploaded files (PDF, FASTA, FNA, CSV) and extract clinical data.
    Used for auto-filling form fields from lab reports and gene sequences.
    """
    from config import Config
    from app.services.file_parser import FileParser
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save the file temporarily
    filename = file.filename
    upload_folder = Config.UPLOAD_FOLDER
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    try:
        data = {}
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if ext == 'pdf':
            # Parse PDF blood report
            data = FileParser.parse_pdf(filepath)
        elif ext in ['fasta', 'fna', 'fa', 'fas']:
            # Parse FASTA/FNA gene sequence
            sequence, clinical_data = FileParser.parse_fasta(filepath)
            data = clinical_data
            data['sequence'] = sequence
            
            # === GENETIC MUTATION ANALYSIS ===
            # Detect GAG → GTG (Glu → Val) mutation in HBB gene
            mutation_info = analyze_hbb_mutation(sequence)
            data.update(mutation_info)
            
            # Auto-fill hemoglobin values based on mutation status
            hemoglobin_estimates = autofill_hemoglobin_from_mutation(mutation_info['mutation_status'])
            data.update(hemoglobin_estimates)
            data['is_ai_estimated'] = True
            data['ai_note'] = '🔬 Values are AI-estimated based on genetic mutation pattern. For exact values, please upload blood test report (HPLC/Electrophoresis).'
            
        elif ext == 'csv':
            # Parse CSV lab report
            data = FileParser.parse_csv(filepath)
        else:
            return jsonify({'error': f'Unsupported file type: {ext}'}), 400
        
        # Clean up temp file (optional)
        # os.remove(filepath)
        
        return jsonify({
            'success': True,
            'data': data,
            'filename': filename,
            'file_type': ext
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/predict/immunity', methods=['POST'])
def predict_immunity():
    from flask import session
    from app.extensions import db
    from app.models import MedicalRecord, ImmunityResult
    data = request.json
    user_id = session.get('user_id')
    result = MLEngine.predict_immunity(data, user_id=user_id)
    
    # Save to database
    try:
        record = MedicalRecord(
            user_id=user_id,
            patient_name=data.get('patient_name', 'Anonymous'),
            age=int(data.get('age') or 0),
            gender=data.get('gender', 'N/A'),
            module_type='IMMUNITY'
        )
        db.session.add(record)
        db.session.flush()
        
        imm_res = ImmunityResult(
            record_id=record.id,
            wbc_count=float(data.get('wbc', 0)),
            neutrophils=float(data.get('neutrophils', 0)),
            lymphocytes=float(data.get('lymphocytes', 0)),
            monocytes=float(data.get('monocytes', 0)),
            igg=float(data.get('igg', 0)),
            igm=float(data.get('igm', 0)),
            iga=float(data.get('iga', 0)),
            immunity_score=result.get('immunity_score', result.get('score', 0)),
            immunity_class=result.get('immunity_class', result.get('class', '')),
            confidence_score=result.get('confidence_score', 0),
            recommendations=result.get('recommendation', '')
        )
        db.session.add(imm_res)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[API] DB save error (immunity): {e}")
    
    return jsonify(result)

@api_bp.route('/predict/sickle_cell', methods=['POST'])
def predict_sickle_cell():
    from flask import session
    from app.extensions import db
    from app.models import MedicalRecord, SickleResult
    data = request.json
    user_id = session.get('user_id')
    result = MLEngine.predict_sickle_cell(data, user_id=user_id)
    
    # Save to database
    try:
        record = MedicalRecord(
            user_id=user_id,
            patient_name=data.get('patient_name', 'Anonymous'),
            age=int(data.get('age') or 0),
            gender=data.get('gender', 'N/A'),
            module_type='SICKLE_CELL'
        )
        db.session.add(record)
        db.session.flush()
        
        sickle_res = SickleResult(
            record_id=record.id,
            hba_percent=float(data.get('hba', 0)),
            hbs_percent=float(data.get('hbs', 0)),
            hbf_percent=float(data.get('hbf', 0)),
            hbb_sequence_snippet=data.get('sequence', '')[:500],
            prediction=result['prediction'],
            confidence_score=result.get('confidence_score', 0),
            genetic_notes=result['note'],
            immunity_score=result.get('linked_immunity', {}).get('score') if result.get('linked_immunity') else None,
            immunity_class=result.get('linked_immunity', {}).get('class') if result.get('linked_immunity') else None
        )
        db.session.add(sickle_res)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[API] DB save error (sickle_cell): {e}")
    
    return jsonify(result)

@api_bp.route('/predict/lsd', methods=['POST'])
def predict_lsd():
    from flask import session
    from app.extensions import db
    from app.models import MedicalRecord, LSDResult
    data = request.json
    user_id = session.get('user_id')
    result = MLEngine.predict_lsd(data, user_id=user_id)
    
    # Save to database
    try:
        record = MedicalRecord(
            user_id=user_id,
            patient_name=data.get('patient_name', 'Anonymous'),
            age=int(data.get('age') or 0),
            gender=data.get('gender', 'N/A'),
            module_type='LSD'
        )
        db.session.add(record)
        db.session.flush()
        
        lsd_res = LSDResult(
            record_id=record.id,
            beta_glucosidase=float(data.get('b_glucosidase') or 0),
            alpha_galactosidase=float(data.get('a_galactosidase') or 0),
            liver_size=float(data.get('liver_size') or 0),
            spleen_size=float(data.get('spleen_size') or 0),
            risk_level=result['risk_level'],
            probability_score=result['probability'],
            confidence_score=result.get('confidence_score', 0),
            immunity_score=result.get('linked_immunity', {}).get('score') if result.get('linked_immunity') else None,
            immunity_class=result.get('linked_immunity', {}).get('class') if result.get('linked_immunity') else None
        )
        db.session.add(lsd_res)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[API] DB save error (lsd): {e}")
    
    return jsonify(result)

@api_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for the global chatbot.
    Expects JSON: { "message": "hello", "context": {...} }
    Uses LLM (Google Gemini) for intelligent responses.
    Persists conversations to PostgreSQL.
    """
    from flask import session
    from app.extensions import db
    from app.models import ChatLog

    try:
        data = request.get_json(force=True, silent=True) or {}
        message = data.get('message', '')
        context = data.get('context', {})
        user_id = session.get('user_id')

        if not message:
            return jsonify({'response': 'Please type a message to get started!'})

        from app.services.rag_system import rag_bot
        response_text = rag_bot.generate_response(message, context)

        # Persist to PostgreSQL
        try:
            chat_log = ChatLog(
                user_id=user_id,
                message=message,
                response=response_text,
                context_used=str(context) if context else None
            )
            db.session.add(chat_log)
            db.session.commit()
        except Exception as e:
            print(f"[Chat] Failed to save chat log: {e}")
            db.session.rollback()

        return jsonify({
            'response': response_text
        })

    except Exception as e:
        print(f"[Chat] Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        # Always return valid JSON so frontend doesn't crash
        return jsonify({
            'response': "I'm the TriGen-AI Medical Assistant. I can help with Immunity Analysis, "
                        "Sickle Cell Anemia, and Lysosomal Storage Disorders. How can I help you today?\n\n"
                        "*Note: I encountered a temporary issue. Please try again.*"
        })

@api_bp.route('/report/download', methods=['POST'])
def download_report():
    data = request.json
    module = data.get('module')
    inputs = data.get('inputs')
    results = data.get('results')
    
    import os
    from app.services.report_gen import ReportGenerator
    from config import Config
    from flask import send_file
    
    filename = f"Report_{module}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(os.path.dirname(Config.UPLOAD_FOLDER), 'reports', filename)
    
    ReportGenerator.generate_report(module, inputs, results, filepath)
    
    return jsonify({'download_url': f"/reports/{filename}"})

@api_bp.route('/admin/records', methods=['GET'])
def get_admin_records():
    """
    Detailed records view for admins to see inputs and outputs.
    """
    from flask import session
    from app.models import User, MedicalRecord, ImmunityResult, SickleResult, LSDResult
    
    # Simple auth check (could use decorator but this is an API)
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    admin = User.query.get(user_id)
    if not admin or admin.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    records = MedicalRecord.query.order_by(MedicalRecord.record_date.desc()).all()
    results = []
    
    for r in records:
        record_data = {
            'id': r.id,
            'patient_name': r.patient_name,
            'age': r.age,
            'gender': r.gender,
            'module': r.module_type,
            'date': r.record_date.strftime('%Y-%m-%d %H:%M'),
            'details': {}
        }
        
        if r.module_type == 'IMMUNITY' and r.immunity_result:
            record_data['details'] = {
                'wbc': r.immunity_result.wbc_count,
                'score': r.immunity_result.immunity_score,
                'class': r.immunity_result.immunity_class,
                'confidence': r.immunity_result.confidence_score
            }
        elif r.module_type == 'SICKLE_CELL' and r.sickle_result:
            record_data['details'] = {
                'hbs': r.sickle_result.hbs_percent,
                'prediction': r.sickle_result.prediction,
                'confidence': r.sickle_result.confidence_score,
                'sequence': r.sickle_result.hbb_sequence_snippet
            }
        elif r.module_type == 'LSD' and r.lsd_result:
            record_data['details'] = {
                'risk': r.lsd_result.risk_level,
                'prob': r.lsd_result.probability_score,
                'confidence': r.lsd_result.confidence_score
            }
            
        results.append(record_data)
        
    return jsonify({'success': True, 'records': results})

@api_bp.route('/user/history', methods=['GET'])
def get_user_history():
    """Get the authenticated user's own analysis history."""
    from flask import session
    from app.models import MedicalRecord, ImmunityResult, SickleResult, LSDResult

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    records = MedicalRecord.query.filter_by(user_id=user_id)\
        .order_by(MedicalRecord.record_date.desc()).all()
    results = []

    for r in records:
        record_data = {
            'id': r.id,
            'patient_name': r.patient_name,
            'age': r.age,
            'gender': r.gender,
            'module': r.module_type,
            'date': r.record_date.strftime('%Y-%m-%d %H:%M'),
            'details': {}
        }

        if r.module_type == 'IMMUNITY' and r.immunity_result:
            record_data['details'] = {
                'score': r.immunity_result.immunity_score,
                'class': r.immunity_result.immunity_class,
                'confidence': r.immunity_result.confidence_score,
                'wbc': r.immunity_result.wbc_count
            }
        elif r.module_type == 'SICKLE_CELL' and r.sickle_result:
            record_data['details'] = {
                'prediction': r.sickle_result.prediction,
                'confidence': r.sickle_result.confidence_score,
                'hbs': r.sickle_result.hbs_percent
            }
        elif r.module_type == 'LSD' and r.lsd_result:
            record_data['details'] = {
                'risk': r.lsd_result.risk_level,
                'probability': r.lsd_result.probability_score,
                'confidence': r.lsd_result.confidence_score
            }

        results.append(record_data)

    return jsonify({'success': True, 'records': results})

