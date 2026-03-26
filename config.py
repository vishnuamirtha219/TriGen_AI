import os
import sys
import urllib.parse
import socket
from dotenv import load_dotenv

# Determine the base path (frozen EXE vs normal)
BASE_PATH = os.environ.get('TRIGEN_BASE_PATH', os.path.dirname(os.path.abspath(__file__)))

# Load .env file from the base path
dotenv_path = os.path.join(BASE_PATH, '.env')
load_dotenv(dotenv_path)

def resolve_db_host(db_url):
    """
    Resolves the hostname in the database URL to an IP address to avoid 
    intermittent DNS resolution failures (like psycopg2.OperationalError)
    with Supabase's pooler.
    """
    if not db_url:
        return db_url
    
    hostname = None
    try:
        parsed = urllib.parse.urlparse(db_url)
        hostname = parsed.hostname
        if hostname and "pooler.supabase.com" in hostname:
            try:
                ip_address = socket.gethostbyname(hostname)
            except socket.gaierror:
                print(f"Warning: DNS resolution failed for {hostname}, using fallback IP.")
                # Fallback to known IPs for aws-1-ap-south-1.pooler.supabase.com
                ip_address = "3.111.225.200" 
                
            netloc = parsed.netloc.replace(hostname, ip_address)
            # Replace netloc and return new URL
            return urllib.parse.urlunparse(parsed._replace(netloc=netloc))
    except Exception as e:
        print(f"Warning: Failed to parse or modify database host {hostname or 'unknown'}: {e}")
    return db_url

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'

    # Use Supabase Database - resolve hostname to IP
    SQLALCHEMY_DATABASE_URI = resolve_db_host(os.getenv("DATABASE_URL"))

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google Gemini LLM
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or ''

    # Upload Configurations
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024