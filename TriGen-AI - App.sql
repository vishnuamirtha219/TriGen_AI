-- TriGen-AI PostgreSQL Schema

-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    role VARCHAR(20) DEFAULT 'user', -- 'admin', 'user'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medical Records (Centralized)
CREATE TABLE medical_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    patient_name VARCHAR(100),
    age INTEGER,
    gender VARCHAR(10),
    record_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    module_type VARCHAR(20) -- 'IMMUNITY', 'SICKLE_CELL', 'LSD'
);

-- Module 1: Immunity Results
CREATE TABLE immunity_results (
    id SERIAL PRIMARY KEY,
    record_id INTEGER REFERENCES medical_records(id) ON DELETE CASCADE,
    wbc_count FLOAT,
    neutrophils FLOAT,
    lymphocytes FLOAT,
    monocytes FLOAT,
    igg FLOAT,
    igm FLOAT, -- Added in model, presumed needed
    iga FLOAT, -- Added in model
    immunity_score FLOAT,
    immunity_class VARCHAR(20),
    confidence_score FLOAT, -- AI prediction confidence (0-100)
    recommendations TEXT
);

-- Module 2: Sickle Cell Results
CREATE TABLE sickle_results (
    id SERIAL PRIMARY KEY,
    record_id INTEGER REFERENCES medical_records(id) ON DELETE CASCADE,
    hba_percent FLOAT,
    hbs_percent FLOAT,
    hbf_percent FLOAT,
    hbb_sequence_snippet TEXT,
    prediction VARCHAR(20), -- 'Normal', 'Carrier', 'Diseased'
    confidence_score FLOAT, -- AI prediction confidence (0-100)
    genetic_notes TEXT
);

-- Module 3: LSD Results
CREATE TABLE lsd_results (
    id SERIAL PRIMARY KEY,
    record_id INTEGER REFERENCES medical_records(id) ON DELETE CASCADE,
    beta_glucosidase FLOAT,
    alpha_galactosidase FLOAT,
    liver_size FLOAT,
    spleen_size FLOAT,
    risk_level VARCHAR(20),
    probability_score FLOAT,
    confidence_score FLOAT -- AI prediction confidence (0-100)
);

-- Chat Logs
CREATE TABLE chat_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    message TEXT,
    response TEXT,
    context_used TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_medical_records_user_id ON medical_records(user_id);
CREATE INDEX idx_medical_records_date ON medical_records(record_date);
