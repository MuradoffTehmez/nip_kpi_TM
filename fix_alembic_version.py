# fix_alembic_version.py
import psycopg2
from config import settings

# Verilənlər bazası bağlantısı
conn = psycopg2.connect(
    dbname=settings.NAME_KPI_DB,
    user=settings.USER_KPI_DB,
    password=settings.PASS_KPI_DB,
    host=settings.HOST_KPI_DB,
    port=settings.PORT_KPI_DB
)

# Kursor yarat
cur = conn.cursor()

# alembic_version cədvəlini yenilə
cur.execute("UPDATE alembic_version SET version_num = 'ab15f9cb8378';")

# Dəyişiklikləri yadda saxla
conn.commit()

# Bağlantını bağla
cur.close()
conn.close()

print("alembic_version cədvəli yeniləndi.")