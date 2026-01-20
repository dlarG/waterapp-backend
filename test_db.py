from config import Config

def test_config():
    """Test if configuration is working"""
    config = Config()
    print("=== Configuration Test ===")
    print(f"DB_TYPE: {config.DB_TYPE}")
    print(f"Database URI: {config.SQLALCHEMY_DATABASE_URI}")
    print("Configuration loaded successfully!")

if __name__ == "__main__":
    test_config()