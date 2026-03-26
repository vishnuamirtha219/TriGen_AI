# TriGen-AI: Medical Intelligence System

TriGen-AI is a comprehensive desktop application designed for medical analysis and prediction. It leverages Artificial Intelligence to assess Immunity, predict Sickle Cell Anemia risks, and analyze Lysosomal Storage Disorders (LSD).

## Key Features

### 1. Immunity Assessment
*   **Input**: Blood report parameters (WBC, Neutrophils, Lymphocytes, etc.) via manual entry or PDF/CSV upload.
*   **Analysis**: Calculates an Immunity Score (0-100) and classifies it (High/Medium/Low).
*   **Visualization**: Doughnut/Ring chart showing immunity robustness.

### 2. Sickle Cell Prediction
*   **Input**: Hemoglobin levels (HbA, HbS, HbF) and Genetic Sequence (FASTA).
*   **Features**: Detects HBB gene mutations (GAG -> GTG) and analyzes hemoglobin composition.
*   **Visualization**: Bar chart comparing hemoglobin variants.

### 3. LSD Risk Analysis
*   **Input**: Enzymatic activity (Beta-Glucosidase, Alpha-Galactosidase) and Organ sizes.
*   **Analysis**: Predicts risk of Gaucher and Fabry diseases.
*   **Visualization**: Risk Gauge Chart.

### 4. Intelligent Chatbot
*   **Context-Aware**: The chatbot knows your current analysis results.
*   **RAG-Powered**: Provides answers based on embedded medical guidelines for the specific disorders.

## Tech Stack
*   **Backend**: Python (Flask)
*   **Database**: PostgreSQL (Production) / SQLite (Dev)
*   **Frontend**: HTML5, CSS3 (Glassmorphism), JavaScript
*   **ML Engine**: Scikit-Learn / XGBoost (Simulated Logic for Demo)
*   **Desktop Wrapper**: PyWebView

## Installation & Setup

1.  **Prerequisites**:
    *   Python 3.8+
    *   PostgreSQL (Optional, defaults to SQLite if not configured)

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Database Setup**:
    *   The app uses `site.db` (SQLite) by default.
    *   To use PostgreSQL, set `DATABASE_URL` in `.env` or `config.py`.

4.  **Run the Application**:
    *   **Desktop Mode** (Recommended):
        ```bash
        python run.py desktop
        ```
    *   **Server Mode** (Browser):
        ```bash
        python run.py
        ```

## Usage Guide
1.  **Login/Register**: Create an account to access the dashboard.
2.  **Select Module**: Choose from Immunity, Sickle Cell, or LSD on the dashboard.
3.  **Enter Data**: Use the "Manual" form or "Upload" tab to provide medical data.
4.  **Analyze**: Click "Analyze/Predict" to see results and charts.
5.  **Chat**: Click the chat bubble (bottom-right) to ask questions about your results.
6.  **Report**: Download a PDF summary of the analysis.

## Developer
*   **Author**: Google Deepmind Code Agent
*   **Version**: 1.0.0
