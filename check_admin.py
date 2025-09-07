import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import models in the correct order to avoid circular imports
from database import get_db
from models.user_profile import UserProfile
from models.user import User

def check_admin_user():
    """Check if admin user exists and create one if not."""
    with get_db() as session:
        # Check if admin user exists
        admin_user = session.query(User).filter(User.username == "admin").first()
        
        if admin_user:
            print("Admin user already exists:")
            print(f"  Username: {admin_user.username}")
            print(f"  Role: {admin_user.role}")
            print(f"  ID: {admin_user.id}")
            return admin_user
        else:
            print("No admin user found. Creating one...")
            # Create admin user
            admin_user = User(
                username="admin",
                role="admin",
                is_active=True
            )
            admin_user.set_password("admin123")
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            
            print("Admin user created successfully:")
            print(f"  Username: {admin_user.username}")
            print(f"  Password: admin123")
            print(f"  Role: {admin_user.role}")
            print(f"  ID: {admin_user.id}")
            return admin_user

if __name__ == "__main__":
    check_admin_user()