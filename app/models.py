from datetime import datetime, timezone
from .extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user') # 'admin', 'user'
    current_stage = db.Column(db.String(20), default='IMMUNITY') # 'IMMUNITY', 'SICKLE_CELL', 'LSD', 'COMPLETED'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    records = db.relationship('MedicalRecord', backref='user', lazy=True)
    chat_logs = db.relationship('ChatLog', backref='user', lazy=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Nullable for guest scans if needed
    patient_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    record_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    module_type = db.Column(db.String(20)) # 'IMMUNITY', 'SICKLE_CELL', 'LSD'

    immunity_result = db.relationship('ImmunityResult', backref='record', uselist=False, lazy=True)
    sickle_result = db.relationship('SickleResult', backref='record', uselist=False, lazy=True)
    lsd_result = db.relationship('LSDResult', backref='record', uselist=False, lazy=True)

class ImmunityResult(db.Model):
    __tablename__ = 'immunity_results'
    
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    wbc_count = db.Column(db.Float)
    neutrophils = db.Column(db.Float)
    lymphocytes = db.Column(db.Float)
    monocytes = db.Column(db.Float)
    igg = db.Column(db.Float)
    igm = db.Column(db.Float)
    iga = db.Column(db.Float)
    
    immunity_score = db.Column(db.Float)
    immunity_class = db.Column(db.String(20)) # Low, Medium, High
    confidence_score = db.Column(db.Float)  # AI confidence (0-100)
    recommendations = db.Column(db.Text)

class SickleResult(db.Model):
    __tablename__ = 'sickle_results'
    
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    hba_percent = db.Column(db.Float)
    hbs_percent = db.Column(db.Float)
    hbf_percent = db.Column(db.Float)
    hbb_sequence_snippet = db.Column(db.Text) # Store only a snippet or hash if too large
    
    prediction = db.Column(db.String(20)) # Normal, Carrier, Diseased
    confidence_score = db.Column(db.Float)  # AI confidence (0-100)
    genetic_notes = db.Column(db.Text)
    
    # Linked Immunity Data
    immunity_score = db.Column(db.Float)
    immunity_class = db.Column(db.String(20))

class LSDResult(db.Model):
    __tablename__ = 'lsd_results'
    
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    beta_glucosidase = db.Column(db.Float)
    alpha_galactosidase = db.Column(db.Float)
    liver_size = db.Column(db.Float)
    spleen_size = db.Column(db.Float)
    
    risk_level = db.Column(db.String(20)) # Low, Medium, High
    probability_score = db.Column(db.Float)
    confidence_score = db.Column(db.Float)  # AI confidence (0-100)
    
    # Linked Immunity Data
    immunity_score = db.Column(db.Float)
    immunity_class = db.Column(db.String(20))

class ChatLog(db.Model):
    __tablename__ = 'chat_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    message = db.Column(db.Text)
    response = db.Column(db.Text)
    context_used = db.Column(db.Text) # To store which docs were RAG'd
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
