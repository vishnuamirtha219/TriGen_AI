"""
TriGen-AI — ML Model Training Script
Generates synthetic medical datasets and trains classifiers for all 3 modules:
  1. Immunity Assessment (Random Forest)
  2. Sickle Cell Prediction (XGBoost)
  3. LSD Risk Assessment (Gradient Boosting)

Usage: python train_models.py
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Ensure output directory exists
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml_models')
os.makedirs(MODEL_DIR, exist_ok=True)

np.random.seed(42)


# ============================================================
# MODULE 1: IMMUNITY CLASSIFIER
# ============================================================
def generate_immunity_data(n=3000):
    """Generate synthetic immunity data based on clinical reference ranges."""
    data = []
    
    for _ in range(n):
        # Randomly assign class first, then generate features accordingly
        label = np.random.choice(['Strong', 'Moderate', 'Weak'], p=[0.35, 0.40, 0.25])
        
        if label == 'Strong':
            wbc = np.random.normal(7500, 1500)
            neutrophils = np.random.normal(55, 8)
            lymphocytes = np.random.normal(32, 5)
            monocytes = np.random.normal(5, 1.5)
            igg = np.random.normal(1100, 200)
            hemoglobin = np.random.normal(14.5, 1)
            platelets = np.random.normal(275000, 50000)
            age = np.random.randint(18, 55)
        elif label == 'Moderate':
            wbc = np.random.normal(5500, 2000)
            neutrophils = np.random.normal(58, 12)
            lymphocytes = np.random.normal(26, 7)
            monocytes = np.random.normal(6, 2.5)
            igg = np.random.normal(800, 250)
            hemoglobin = np.random.normal(12.5, 1.5)
            platelets = np.random.normal(230000, 60000)
            age = np.random.randint(25, 65)
        else:  # Weak
            wbc = np.random.normal(3500, 1200)
            neutrophils = np.random.normal(45, 15)
            lymphocytes = np.random.normal(18, 6)
            monocytes = np.random.normal(8, 3)
            igg = np.random.normal(500, 200)
            hemoglobin = np.random.normal(10.5, 1.5)
            platelets = np.random.normal(180000, 60000)
            age = np.random.randint(40, 80)
        
        # Derived features
        alc = max(0, (wbc * lymphocytes / 100))
        nlr = neutrophils / max(lymphocytes, 1)
        
        data.append({
            'wbc': max(0, wbc),
            'neutrophils': np.clip(neutrophils, 0, 100),
            'lymphocytes': np.clip(lymphocytes, 0, 100),
            'monocytes': np.clip(monocytes, 0, 30),
            'igg': max(0, igg),
            'hemoglobin': max(0, hemoglobin),
            'platelets': max(0, platelets),
            'age': age,
            'alc': alc,
            'nlr': nlr,
            'label': label
        })
    
    return pd.DataFrame(data)


def train_immunity_model():
    """Train Random Forest for immunity classification."""
    print("\n" + "="*60)
    print("MODULE 1: IMMUNITY CLASSIFIER (Random Forest)")
    print("="*60)
    
    df = generate_immunity_data(3000)
    features = ['wbc', 'neutrophils', 'lymphocytes', 'monocytes', 'igg', 'hemoglobin', 'platelets', 'age', 'alc', 'nlr']
    
    X = df[features]
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nAccuracy: {accuracy:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature importance
    importance = dict(zip(features, model.feature_importances_))
    print("Feature Importance:")
    for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
        print(f"  {feat:15s} {imp:.4f}")
    
    path = os.path.join(MODEL_DIR, 'immunity_rf.joblib')
    joblib.dump({'model': model, 'features': features}, path)
    print(f"\nModel saved to: {path}")
    return accuracy


# ============================================================
# MODULE 2: SICKLE CELL CLASSIFIER
# ============================================================
def generate_sickle_data(n=2500):
    """Generate synthetic sickle cell data based on clinical hemoglobin patterns."""
    data = []
    
    for _ in range(n):
        label = np.random.choice(['Normal', 'Carrier', 'Diseased'], p=[0.45, 0.35, 0.20])
        
        if label == 'Normal':
            hba = np.random.normal(96, 1.5)
            hbs = np.random.normal(0, 0.3)
            hbf = np.random.normal(1.5, 0.5)
            mutation_count = 0
            gag_count = np.random.randint(3, 8)
            seq_length = np.random.randint(100, 500)
        elif label == 'Carrier':
            hba = np.random.normal(58, 5)
            hbs = np.random.normal(38, 4)
            hbf = np.random.normal(3, 1.5)
            mutation_count = np.random.randint(1, 3)
            gag_count = np.random.randint(2, 6)
            seq_length = np.random.randint(100, 500)
        else:  # Diseased
            hba = np.random.normal(5, 3)
            hbs = np.random.normal(85, 6)
            hbf = np.random.normal(8, 3)
            mutation_count = np.random.randint(2, 6)
            gag_count = np.random.randint(0, 2)
            seq_length = np.random.randint(100, 500)
        
        # Derived
        hb_ratio = hbs / max(hba, 0.1)
        hb_total = hba + hbs + hbf
        
        data.append({
            'hba': np.clip(hba, 0, 100),
            'hbs': np.clip(hbs, 0, 100),
            'hbf': np.clip(hbf, 0, 100),
            'mutation_count': mutation_count,
            'gag_count': gag_count,
            'seq_length': seq_length,
            'hb_ratio': hb_ratio,
            'hb_total': min(hb_total, 100),
            'label': label
        })
    
    return pd.DataFrame(data)


def train_sickle_model():
    """Train XGBoost for sickle cell classification."""
    print("\n" + "="*60)
    print("MODULE 2: SICKLE CELL CLASSIFIER (XGBoost)")
    print("="*60)
    
    df = generate_sickle_data(2500)
    features = ['hba', 'hbs', 'hbf', 'mutation_count', 'gag_count', 'seq_length', 'hb_ratio', 'hb_total']
    
    X = df[features]
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    from xgboost import XGBClassifier
    from sklearn.preprocessing import LabelEncoder
    
    le = LabelEncoder()
    y_train_enc = le.fit_transform(y_train)
    y_test_enc = le.transform(y_test)
    
    model = XGBClassifier(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        use_label_encoder=False,
        eval_metric='mlogloss'
    )
    model.fit(X_train, y_train_enc)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test_enc, y_pred)
    
    print(f"\nAccuracy: {accuracy:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test_enc, y_pred, target_names=le.classes_))
    
    path = os.path.join(MODEL_DIR, 'sickle_xgb.joblib')
    joblib.dump({'model': model, 'features': features, 'label_encoder': le}, path)
    print(f"\nModel saved to: {path}")
    return accuracy


# ============================================================
# MODULE 3: LSD RISK CLASSIFIER
# ============================================================
def generate_lsd_data(n=2000):
    """Generate synthetic LSD risk data based on enzyme levels and organ sizes."""
    data = []
    
    for _ in range(n):
        label = np.random.choice(['Low', 'Medium', 'High'], p=[0.45, 0.30, 0.25])
        
        if label == 'Low':
            b_gluc = np.random.normal(8, 2)
            a_gal = np.random.normal(8, 2)
            liver = np.random.normal(14, 1)
            spleen = np.random.normal(11, 1)
        elif label == 'Medium':
            b_gluc = np.random.normal(3.5, 1)
            a_gal = np.random.normal(4, 1.5)
            liver = np.random.normal(15.5, 1.5)
            spleen = np.random.normal(12.5, 1.5)
        else:  # High
            b_gluc = np.random.normal(1.5, 0.8)
            a_gal = np.random.normal(2, 1)
            liver = np.random.normal(18, 2)
            spleen = np.random.normal(15, 2)
        
        age = np.random.randint(5, 75)
        
        # Derived
        enzyme_ratio = b_gluc / max(a_gal, 0.1)
        organ_index = (liver + spleen) / 2
        
        data.append({
            'b_glucosidase': max(0, b_gluc),
            'a_galactosidase': max(0, a_gal),
            'liver_size': max(0, liver),
            'spleen_size': max(0, spleen),
            'age': age,
            'enzyme_ratio': enzyme_ratio,
            'organ_index': organ_index,
            'label': label
        })
    
    return pd.DataFrame(data)


def train_lsd_model():
    """Train Gradient Boosting for LSD risk classification."""
    print("\n" + "="*60)
    print("MODULE 3: LSD RISK CLASSIFIER (Gradient Boosting)")
    print("="*60)
    
    df = generate_lsd_data(2000)
    features = ['b_glucosidase', 'a_galactosidase', 'liver_size', 'spleen_size', 'age', 'enzyme_ratio', 'organ_index']
    
    X = df[features]
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        min_samples_split=5,
        min_samples_leaf=3,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nAccuracy: {accuracy:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature importance
    importance = dict(zip(features, model.feature_importances_))
    print("Feature Importance:")
    for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
        print(f"  {feat:20s} {imp:.4f}")
    
    path = os.path.join(MODEL_DIR, 'lsd_gb.joblib')
    joblib.dump({'model': model, 'features': features}, path)
    print(f"\nModel saved to: {path}")
    return accuracy


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("TriGen-AI — ML Model Training Pipeline")
    print("=" * 60)
    
    results = {}
    results['Immunity (Random Forest)'] = train_immunity_model()
    results['Sickle Cell (XGBoost)'] = train_sickle_model()
    results['LSD Risk (Gradient Boosting)'] = train_lsd_model()
    
    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)
    for name, acc in results.items():
        status = "✓" if acc >= 0.85 else "⚠"
        print(f"  {status} {name:35s}  Accuracy: {acc:.4f}")
    
    print(f"\nModels saved to: {MODEL_DIR}/")
    print("Training complete!")
