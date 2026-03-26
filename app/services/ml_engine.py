import os
import random
import numpy as np

_models = {}
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ml_models')

def _load_model(name):
    
    if name in _models:
        return _models[name]
    
    path = os.path.join(MODEL_DIR, name)
    if os.path.exists(path):
        try:
            import joblib
            _models[name] = joblib.load(path)
            print(f"[MLEngine] Loaded model: {name}")
            return _models[name]
        except Exception as e:
            print(f"[MLEngine] Failed to load {name}: {e}")
    return None

class MLEngine:
    @staticmethod
    def predict_immunity(data, user_id=None):
        """
        AI-based Immunity Prediction using trained Random Forest model.
        Falls back to rule-based scoring if model is unavailable.
        """
        from app.models import User
        from app.extensions import db

        
        wbc = float(data.get('wbc', 0))
        neutrophils = float(data.get('neutrophils', 0))
        lymphocytes = float(data.get('lymphocytes', 0))
        monocytes = float(data.get('monocytes', 0))
        eosinophils = float(data.get('eosinophils', 0))
        platelets = float(data.get('platelets', 250000))
        hemoglobin = float(data.get('hemoglobin') or data.get('hba', 0))
        igg = float(data.get('igg', 0))
        igm = float(data.get('igm', 0))
        iga = float(data.get('iga', 0))
        age = int(data.get('age', 30))

        
        alc = (wbc * lymphocytes / 100) if lymphocytes > 0 and wbc > 0 else 0
        nlr = (neutrophils / lymphocytes) if lymphocytes > 0 else 0
        plr = (platelets / (wbc * lymphocytes / 100)) if lymphocytes > 0 and wbc > 0 else 0
        immune_balance = (lymphocytes / 100) if wbc > 0 else 0

        
        model_data = _load_model('immunity_rf.joblib')
        ml_used = False
        
        if model_data and wbc > 0:
            try:
                model = model_data['model']
                features = model_data['features']
                
                feature_values = {
                    'wbc': wbc, 'neutrophils': neutrophils, 'lymphocytes': lymphocytes,
                    'monocytes': monocytes, 'igg': igg, 'hemoglobin': hemoglobin,
                    'platelets': platelets, 'age': age, 'alc': alc, 'nlr': nlr
                }
                X = np.array([[feature_values.get(f, 0) for f in features]])
                
                prediction = model.predict(X)[0]
                probabilities = model.predict_proba(X)[0]
                class_names = model.classes_
                
                # Map prediction to score
                prob_dict = dict(zip(class_names, probabilities))
                if prediction == 'Strong':
                    final_score = int(75 + prob_dict.get('Strong', 0) * 25)
                elif prediction == 'Moderate':
                    final_score = int(50 + prob_dict.get('Moderate', 0) * 25)
                else:
                    final_score = int(prob_dict.get('Weak', 0) * 50)
                
                immunity_class = f"{prediction} Immunity"
                ml_used = True
                
            except Exception as e:
                print(f"[MLEngine] Model prediction failed, using rule-based: {e}")
                ml_used = False
        
        # === RULE-BASED FALLBACK ===
        if not ml_used:
            score = 0
            if wbc > 0:
                if 4500 <= wbc <= 10500: score += 15
                elif 3500 <= wbc < 4500: score += 10
                elif wbc < 3500: score += 3
                else: score += 8
            if alc > 0:
                if 1000 <= alc <= 4800: score += 15
                elif 800 <= alc < 1000: score += 10
                elif alc < 800: score += 3
                else: score += 12
            if neutrophils > 0:
                if 40 <= neutrophils <= 70: score += 10
                elif neutrophils < 40: score += 5
                else: score += 6
            if nlr > 0:
                if nlr <= 3: score += 15
                elif nlr <= 5: score += 10
                else: score += 3
            if monocytes > 0 and 2 <= monocytes <= 10: score += 5
            if igg > 0:
                if 700 <= igg <= 1600: score += 15
                elif 500 <= igg < 700: score += 10
                elif igg < 500: score += 3
                else: score += 12
            else:
                score += 12 if alc >= 1500 else 6
            if hemoglobin > 0:
                if (age <= 50 and hemoglobin >= 12) or (age > 50 and hemoglobin >= 11): score += 10
                elif hemoglobin < 10: score += 3
                else: score += 6
            if platelets > 0 and 150000 <= platelets <= 400000: score += 5
            if age < 60: score += 5
            elif age >= 70: score -= 5
            
            final_score = min(max(score, 0), 100)
            if final_score >= 75: immunity_class = 'Strong Immunity'
            elif final_score >= 50: immunity_class = 'Moderate Immunity'
            else: immunity_class = 'Weak Immunity'
        
        # === ANALYSIS (common to both paths) ===
        key_findings = []
        risk_indicators = []
        missing_params = []

        if wbc > 0:
            if 4500 <= wbc <= 10500: key_findings.append("✓ WBC count is in healthy range")
            elif wbc < 3500: risk_indicators.append("Low WBC count - reduced immune cell production")
            elif wbc > 10500: risk_indicators.append("Elevated WBC - possible infection or inflammation")
        else:
            missing_params.append("WBC")

        if alc > 0:
            if 1000 <= alc <= 4800: key_findings.append("✓ Lymphocyte count optimal for immune defense")
            elif alc < 800: risk_indicators.append("Low lymphocyte count - weakened adaptive immunity")
        else:
            missing_params.append("Lymphocytes")

        if neutrophils > 0:
            if 40 <= neutrophils <= 70: key_findings.append("✓ Neutrophils in healthy range")
            elif neutrophils < 40: risk_indicators.append("Low neutrophils - reduced bacterial defense")
            else: risk_indicators.append("High neutrophils - possible acute infection")

        if nlr > 0:
            if nlr <= 3: key_findings.append("✓ Low inflammation (NLR optimal)")
            elif nlr <= 5: key_findings.append("⚠ Mild inflammation detected (NLR elevated)")
            else: risk_indicators.append("High inflammation (NLR > 5) - immune stress")

        if monocytes > 0:
            if 2 <= monocytes <= 10: key_findings.append("✓ Monocytes normal")
            elif monocytes > 10: risk_indicators.append("Elevated monocytes - chronic inflammation possible")

        if igg > 0:
            if 700 <= igg <= 1600: key_findings.append("✓ IgG antibodies at protective levels")
            elif igg < 500: risk_indicators.append("Low IgG - weakened antibody immunity")
        else:
            missing_params.append("IgG")

        if hemoglobin > 0 and hemoglobin < 10:
            risk_indicators.append("Anemia detected - impairs immune function")

        # Classification explanation
        if 'Strong' in immunity_class:
            category_explanation = "Your immune system is functioning well and can effectively defend against infections."
        elif 'Moderate' in immunity_class:
            category_explanation = "Your immune system is functioning adequately but has room for improvement."
        else:
            category_explanation = "Your immune system shows signs of weakness and may need medical attention."

        # Recommendations
        recommendations = []
        patient_ref = f"Patient (Age {age})"
        if final_score < 75:
            recommendations.append(f"{patient_ref}: We recommend prioritizing 7-9 hours of restorative sleep to support T-cell regeneration.")
            recommendations.append("Incorporate more cytokine-supporting nutrients like leafy greens, citrus, and lean proteins.")
        if nlr > 3:
            recommendations.append("The elevated NLR suggesting mild immune stress should be managed with regular mindfulness practice.")
        if alc < 1000 or (igg > 0 and igg < 700):
            recommendations.append("Specific Suggestion: Targeted Vitamin D3 (2000 IU) and Zinc (15mg) may assist your adaptive response.")
        if hemoglobin > 0 and hemoglobin < 12:
            recommendations.append("Iron-optimized diet (heme or non-heme sources) is advised for better oxygen-carrying capacity.")
        if not recommendations:
            recommendations.append(f"Excellent profile, {patient_ref}. Maintain your current regimen and annual screenings.")

        # Confidence scoring
        param_weights = {
            'wbc': (wbc > 0, 20), 'lymphocytes': (lymphocytes > 0, 18),
            'neutrophils': (neutrophils > 0, 15), 'igg': (igg > 0, 15),
            'hemoglobin': (hemoglobin > 0, 12), 'platelets': (platelets > 0 and platelets != 250000, 8),
            'monocytes': (monocytes > 0, 6), 'age': (age > 0 and age != 30, 6)
        }
        total_weight = sum(w[1] for w in param_weights.values())
        achieved_weight = sum(w[1] for w in param_weights.values() if w[0])
        confidence_score = round((achieved_weight / total_weight) * 100, 1)
        confidence_level = 'High' if confidence_score >= 80 else ('Moderate' if confidence_score >= 60 else 'Low')

        # Top contributors
        contributions = []
        if wbc > 0:
            if 4500 <= wbc <= 10500: contributions.append({'param': 'WBC Count', 'impact': 'positive', 'value': wbc, 'points': 15})
            else: contributions.append({'param': 'WBC Count', 'impact': 'concern', 'value': wbc, 'points': -5})
        if lymphocytes > 0:
            if 1000 <= alc <= 4800: contributions.append({'param': 'Lymphocytes (ALC)', 'impact': 'positive', 'value': round(alc, 1), 'points': 15})
            else: contributions.append({'param': 'Lymphocytes (ALC)', 'impact': 'concern', 'value': round(alc, 1), 'points': -5})
        if nlr > 0:
            if nlr <= 3: contributions.append({'param': 'NLR (Inflammation)', 'impact': 'positive', 'value': round(nlr, 2), 'points': 15})
            elif nlr > 5: contributions.append({'param': 'NLR (Inflammation)', 'impact': 'concern', 'value': round(nlr, 2), 'points': -10})
        if igg > 0:
            if 700 <= igg <= 1600: contributions.append({'param': 'IgG Antibodies', 'impact': 'positive', 'value': igg, 'points': 15})
            elif igg < 500: contributions.append({'param': 'IgG Antibodies', 'impact': 'concern', 'value': igg, 'points': -10})
        top_contributors = sorted(contributions, key=lambda x: abs(x['points']), reverse=True)[:4]

        # Explanation
        explanation = f"{category_explanation} "
        if risk_indicators:
            explanation += f"Key concerns: {'; '.join(risk_indicators[:2])}. "
        else:
            explanation += "No major concerns detected. "
        if missing_params:
            explanation += f"Note: Assessment confidence reduced due to missing parameters: {', '.join(missing_params)}. "
        if ml_used:
            explanation += "(Prediction by Random Forest ML model) "

        # Advance Stage
        if user_id:
            user = User.query.get(user_id)
            if user and user.current_stage == 'IMMUNITY':
                user.current_stage = 'SICKLE_CELL'
                db.session.commit()

        return {
            'score': final_score,
            'immunity_score': final_score,
            'class': immunity_class,
            'immunity_class': immunity_class,
            'confidence_score': confidence_score,
            'confidence_level': confidence_level,
            'top_contributors': top_contributors,
            'key_findings': key_findings[:5],
            'risk_indicators': risk_indicators,
            'explanation': explanation,
            'recommendation': ' | '.join(recommendations[:3]),
            'ml_model_used': ml_used,
            'derived_features': {
                'alc': round(alc, 1),
                'nlr': round(nlr, 2),
                'plr': round(plr, 2),
                'immune_balance': round(immune_balance, 3)
            }
        }

    @staticmethod
    def predict_sickle_cell(data, user_id=None):
        """
        Predict Sickle Cell using trained XGBoost model.
        Falls back to rule-based detection if model unavailable.
        """
        from app.models import User, ImmunityResult, MedicalRecord
        from app.extensions import db

        hba = float(data.get('hba', 0))
        hbs = float(data.get('hbs', 0))
        hbf = float(data.get('hbf', 0))
        sequence = data.get('sequence', '').upper()

        # Genetic analysis
        try:
            from Bio.Seq import Seq
            mutation_detected = False
            amino_acid_mutation = False
            if sequence:
                dna_seq = Seq(sequence)
                mutation_detected = 'GTG' in sequence
                if len(sequence) >= 20:
                    protein = str(dna_seq.translate(to_stop=True))
                    if 'V' in protein and 'GTG' in sequence:
                        amino_acid_mutation = True
        except ImportError:
            mutation_detected = 'GTG' in sequence
            amino_acid_mutation = False

        # Derived features for model
        mutation_count = sequence.count('GTG')
        gag_count = sequence.count('GAG')
        seq_length = len(sequence)
        hb_ratio = hbs / max(hba, 0.1)
        hb_total = min(hba + hbs + hbf, 100)

        # === TRY ML MODEL ===
        model_data = _load_model('sickle_xgb.joblib')
        ml_used = False
        
        if model_data and (hba > 0 or hbs > 0):
            try:
                model = model_data['model']
                features = model_data['features']
                le = model_data['label_encoder']
                
                feature_values = {
                    'hba': hba, 'hbs': hbs, 'hbf': hbf,
                    'mutation_count': mutation_count, 'gag_count': gag_count,
                    'seq_length': seq_length, 'hb_ratio': hb_ratio, 'hb_total': hb_total
                }
                X = np.array([[feature_values.get(f, 0) for f in features]])
                
                pred_idx = model.predict(X)[0]
                probabilities = model.predict_proba(X)[0]
                prediction = le.inverse_transform([pred_idx])[0]
                ml_used = True
                
            except Exception as e:
                print(f"[MLEngine] Sickle model failed, using rule-based: {e}")
                ml_used = False

        # === RULE-BASED FALLBACK ===
        if not ml_used:
            if (mutation_detected or amino_acid_mutation) and hbs > 50:
                prediction = 'Diseased'
            elif mutation_detected or amino_acid_mutation or (hbs > 30):
                prediction = 'Carrier'
            else:
                prediction = 'Normal'

        # Generate clinical note
        if prediction == 'Diseased':
            note = f"HBB Gene Mutation {'(Protein: Valine detected)' if amino_acid_mutation else '(SNP: GTG detected)'} and high HbS levels confirmed. Sickle Cell Anemia (SS)."
        elif prediction == 'Carrier':
            note = "Genetic markers or elevated HbS detected. Potential Sickle Cell Trait (AS)."
        else:
            note = "Genetic markers and Hb distribution appear normal (AA)."
        
        if ml_used:
            note += " (Prediction by XGBoost ML model)"

        # Fetch latest immunity result for the user
        immunity_data = None
        if user_id:
            try:
                latest_immunity = db.session.query(ImmunityResult).join(MedicalRecord).filter(
                    MedicalRecord.user_id == user_id
                ).order_by(MedicalRecord.record_date.desc()).first()
                if latest_immunity:
                    immunity_data = {
                        'score': latest_immunity.immunity_score,
                        'class': latest_immunity.immunity_class
                    }
            except Exception as e:
                print(f"[MLEngine] Failed to fetch latest immunity: {e}")

        # Recommendations
        recommendations = []
        if immunity_data:
            imm_msg = f"NOTE: Linked Immunity status is {immunity_data['class']} (Score: {immunity_data['score']})."
            if "Weak" in immunity_data['class']:
                recommendations.append(f"{imm_msg} Vulnerability to infections is high; strict adherence to crisis prevention is advised.")
            else:
                recommendations.append(f"{imm_msg} Stronger immune defense may help in faster recovery from vaso-occlusive episodes.")

        if prediction == 'Diseased':
            recommendations.append("Immediate consultation with a Hematologist is required for crisis management and folic acid therapy.")
            recommendations.append("Hydration maintenance and pneumococcal vaccinations are critical for preventing complications.")
        elif prediction == 'Carrier':
            recommendations.append("Genetic counseling is advised before family planning to understand inheritance risks.")
            recommendations.append("Avoid extreme high-altitude activities or intense physical stress without proper medical clearance.")
        else:
            recommendations.append("Maintain routine healthy practices; your hemoglobin profile matches the normal population (HbAA).")

        # Confidence scoring
        confidence_factors = {
            'sequence_quality': seq_length >= 50,
            'hba_provided': hba > 0,
            'hbs_provided': hbs > 0,
            'hbf_provided': hbf > 0,
            'mutation_detected': mutation_detected or amino_acid_mutation,
            'hemoglobin_total': hb_total >= 90
        }
        confidence_score = round(sum(1 for v in confidence_factors.values() if v) / len(confidence_factors) * 100, 1)
        confidence_level = 'High' if confidence_score >= 80 else ('Moderate' if confidence_score >= 60 else 'Low')

        # Genetic analysis details
        genetic_analysis = {
            'sequence_length': seq_length,
            'gtg_codon_found': 'GTG' in sequence,
            'gag_codon_found': 'GAG' in sequence,
            'mutation_type': 'E6V (Glu→Val)' if amino_acid_mutation else ('SNP detected' if mutation_detected else 'None detected'),
            'biopython_verified': amino_acid_mutation
        }
        if 'GTG' in sequence:
            genetic_analysis['mutation_position'] = sequence.find('GTG')

        # Advance Stage
        if user_id:
            user = User.query.get(user_id)
            if user and user.current_stage == 'SICKLE_CELL':
                user.current_stage = 'LSD'
                db.session.commit()

        return {
            'prediction': prediction,
            'note': note,
            'mutation_detected': mutation_detected,
            'confidence_score': confidence_score,
            'confidence_level': confidence_level,
            'genetic_analysis': genetic_analysis,
            'sequence_preview': sequence[:100] + "..." if len(sequence) > 100 else sequence,
            'recommendation': " | ".join(recommendations),
            'ml_model_used': ml_used,
            'linked_immunity': immunity_data
        }

    @staticmethod
    def predict_lsd(data, user_id=None):
        """
        Predict LSD risk using trained Gradient Boosting model.
        Falls back to rule-based scoring if model unavailable.
        """
        from app.models import User, ImmunityResult, MedicalRecord
        from app.extensions import db

        b_gluc = float(data.get('b_glucosidase') or 0)
        a_gal = float(data.get('a_galactosidase') or 0)
        liver = float(data.get('liver_size') or 14)
        spleen = float(data.get('spleen_size') or 11)
        age = int(data.get('age') or 30)

        # Derived features
        enzyme_ratio = b_gluc / max(a_gal, 0.1)
        organ_index = (liver + spleen) / 2

        # === TRY ML MODEL ===
        model_data = _load_model('lsd_gb.joblib')
        ml_used = False
        
        if model_data and (b_gluc > 0 or a_gal > 0):
            try:
                model = model_data['model']
                features = model_data['features']
                
                feature_values = {
                    'b_glucosidase': b_gluc, 'a_galactosidase': a_gal,
                    'liver_size': liver, 'spleen_size': spleen,
                    'age': age, 'enzyme_ratio': enzyme_ratio, 'organ_index': organ_index
                }
                X = np.array([[feature_values.get(f, 0) for f in features]])
                
                risk_level = str(model.predict(X)[0])
                probabilities = model.predict_proba(X)[0]
                class_names = model.classes_
                prob_dict = dict(zip(class_names, probabilities))
                prob = float(round(prob_dict.get(risk_level, 0) * 100, 1))
                ml_used = True
                
            except Exception as e:
                print(f"[MLEngine] LSD model failed, using rule-based: {e}")
                ml_used = False

        # === RULE-BASED FALLBACK ===
        if not ml_used:
            score = 0
            findings_local = []
            if b_gluc < 2.5: score += 40
            elif b_gluc < 4.0: score += 20
            if a_gal < 3.0: score += 30
            if liver > 16: score += 15
            if spleen > 13: score += 15
            prob = min(score, 100)
            risk_level = 'High' if prob > 70 else ('Medium' if prob > 35 else 'Low')

        # Clinical findings
        findings = []
        if b_gluc < 2.5: findings.append("Critically low Beta-glucosidase")
        elif b_gluc < 4.0: findings.append("Low Beta-glucosidase")
        if a_gal < 3.0: findings.append("Low Alpha-galactosidase")
        if liver > 16: findings.append("Hepatomegaly (Enlarged Liver)")
        if spleen > 13: findings.append("Splenomegaly (Enlarged Spleen)")

        # Fetch latest immunity result for the user
        immunity_data = None
        if user_id:
            try:
                latest_immunity = db.session.query(ImmunityResult).join(MedicalRecord).filter(
                    MedicalRecord.user_id == user_id
                ).order_by(MedicalRecord.record_date.desc()).first()
                if latest_immunity:
                    immunity_data = {
                        'score': latest_immunity.immunity_score,
                        'class': latest_immunity.immunity_class
                    }
            except Exception as e:
                print(f"[MLEngine] Failed to fetch latest immunity: {e}")

        # Recommendations
        rec_list = []
        if immunity_data:
            imm_msg = f"NOTE: Immunity status is {immunity_data['class']}."
            if "Weak" in immunity_data['class']:
                rec_list.append(f"{imm_msg} Patients with LSD and low immunity are at higher risk for opportunistic infections.")
            else:
                rec_list.append(f"{imm_msg} Stable immunity provides a better baseline for metabolic therapy responses.")

        if risk_level == 'High':
            rec_list.append("High priority specialty referral: Consult a metabolic disease specialist or Gaucher/Fabry clinic.")
            rec_list.append("Baseline imaging (MRI) of liver and spleen suggested to monitor disease progression.")
        elif risk_level == 'Medium':
            rec_list.append("Enzyme supplementation therapy (ERT) evaluation may be needed; consult a clinical geneticist.")
            rec_list.append("Monitor CBC and bone density regularly as part of comprehensive care.")
        else:
            rec_list.append("Maintain annual clinical evaluations; your current enzyme and organ levels are within optimal ranges.")

        # Confidence scoring
        confidence_factors = {
            'b_gluc_provided': b_gluc > 0,
            'a_gal_provided': a_gal > 0,
            'liver_measured': liver > 0 and liver != 14,
            'spleen_measured': spleen > 0 and spleen != 11,
            'age_provided': age > 0 and age != 30
        }
        confidence_score = round(sum(1 for v in confidence_factors.values() if v) / len(confidence_factors) * 100, 1)
        confidence_level = 'High' if confidence_score >= 80 else ('Moderate' if confidence_score >= 60 else 'Low')

        # Clinical validation
        clinical_validation = {
            'enzyme_panel_complete': b_gluc > 0 and a_gal > 0,
            'organ_assessment_complete': liver > 0 and spleen > 0,
            'meets_diagnostic_criteria': risk_level == 'High' and (b_gluc < 2.5 or a_gal < 3.0),
            'requires_confirmatory_testing': risk_level == 'Medium',
            'validation_notes': []
        }
        if b_gluc < 2.5: clinical_validation['validation_notes'].append("Gaucher disease pattern (low beta-glucosidase)")
        if a_gal < 3.0: clinical_validation['validation_notes'].append("Fabry disease pattern (low alpha-galactosidase)")
        if liver > 16 and spleen > 13: clinical_validation['validation_notes'].append("Dual organomegaly indicative of storage disorder")

        # Severity grading
        if ml_used:
            severity_grade = 'Grade III (Severe)' if risk_level == 'High' else ('Grade II (Moderate)' if risk_level == 'Medium' else 'Normal')
        else:
            if prob > 70: severity_grade = 'Grade III (Severe)'
            elif prob > 50: severity_grade = 'Grade II (Moderate)'
            elif prob > 35: severity_grade = 'Grade I (Mild)'
            else: severity_grade = 'Normal'

        # Advance Stage
        if user_id:
            user = User.query.get(user_id)
            if user and user.current_stage == 'LSD':
                user.current_stage = 'COMPLETED'
                db.session.commit()

        note_suffix = " (Prediction by Gradient Boosting ML model)" if ml_used else ""

        return {
            'risk_level': risk_level,
            'probability': prob if not ml_used else prob,
            'confidence_score': confidence_score,
            'confidence_level': confidence_level,
            'severity_grade': severity_grade + note_suffix,
            'clinical_validation': clinical_validation,
            'findings': findings,
            'recommendation': " | ".join(rec_list),
            'ml_model_used': ml_used,
            'linked_immunity': immunity_data
        }
