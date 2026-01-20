import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DB_TYPE = os.getenv('DB_TYPE', 'local')
    
    # Local PostgreSQL Configuration
    LOCAL_DB_HOST = os.getenv('LOCAL_DB_HOST', 'localhost')
    LOCAL_DB_PORT = os.getenv('LOCAL_DB_PORT', '5432')
    LOCAL_DB_NAME = os.getenv('LOCAL_DB_NAME', 'water_monitoring')
    LOCAL_DB_USER = os.getenv('LOCAL_DB_USER', 'postgres')
    LOCAL_DB_PASSWORD = os.getenv('LOCAL_DB_PASSWORD', 'password')
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
    SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD', '')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    def __init__(self):
        # Build database URI based on type
        if self.DB_TYPE == 'supabase' and self.SUPABASE_URL and self.SUPABASE_DB_PASSWORD:
            # Extract project reference from Supabase URL
            project_ref = self.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')
            self.SQLALCHEMY_DATABASE_URI = f"postgresql://postgres:{self.SUPABASE_DB_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"
        else:
            # Use local PostgreSQL
            self.SQLALCHEMY_DATABASE_URI = f"postgresql://{self.LOCAL_DB_USER}:{self.LOCAL_DB_PASSWORD}@{self.LOCAL_DB_HOST}:{self.LOCAL_DB_PORT}/{self.LOCAL_DB_NAME}"
        
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        # Print database URI for debugging (remove password for security)
        safe_uri = self.SQLALCHEMY_DATABASE_URI.replace(self.LOCAL_DB_PASSWORD, '***') if self.LOCAL_DB_PASSWORD else self.SQLALCHEMY_DATABASE_URI
        print(f"Using database: {safe_uri}")