from sqlalchemy import create_engine, text
from config import settings

def check_database():
    try:
        engine = create_engine(settings.get_db_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print("Existing tables:", tables)
            return tables
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return []

if __name__ == "__main__":
    check_database()