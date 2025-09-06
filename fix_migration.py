import psycopg2
from config import settings

# Database connection parameters
db_params = {
    'dbname': settings.NAME_KPI_DB,
    'user': settings.USER_KPI_DB,
    'password': settings.PASS_KPI_DB,
    'host': settings.HOST_KPI_DB,
    'port': settings.PORT_KPI_DB
}

try:
    # Connect to the database
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    
    # Update the alembic version to the correct revision
    cursor.execute("UPDATE alembic_version SET version_num = '41939a0e9444';")
    
    # Commit the transaction
    conn.commit()
    
    print("Alembic version updated successfully!")
    
except Exception as e:
    print(f"Error updating alembic version: {e}")
    
finally:
    # Close the connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()