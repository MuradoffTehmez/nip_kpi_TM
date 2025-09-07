"""Script to seed the database with test data."""

import os
import sys
from faker import Faker
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from database import Base, get_db
from models.user import User
from config import settings

# Initialize Faker
fake = Faker()

def clear_existing_data(db):
    """Clear existing data from the database."""
    print("Clearing existing data...")
    # Delete all records from all tables
    # Note: This should be done in the correct order to respect foreign key constraints
    db.query(User).delete()
    db.commit()

def create_users(db):
    """Create test users with different roles."""
    print("Creating users...")
    
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        role="admin",
        is_active=True
    )
    admin_user.set_password("admin123")
    db.add(admin_user)
    
    # Create manager users
    managers = []
    for i in range(3):
        manager = User(
            username=f"manager{i+1}",
            email=f"manager{i+1}@example.com",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role="manager",
            is_active=True
        )
        manager.set_password("manager123")
        db.add(manager)
        managers.append(manager)
    
    # Commit to get IDs
    db.commit()
    
    # Create employee users
    employees = []
    for i in range(10):
        employee = User(
            username=f"employee{i+1}",
            email=f"employee{i+1}@example.com",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role="user",  # Using "user" as in the existing system
            manager_id=random.choice(managers).id,  # Assign to a random manager
            is_active=True
        )
        employee.set_password("employee123")
        db.add(employee)
        employees.append(employee)
    
    db.commit()
    
    # Refresh objects to get IDs
    db.refresh(admin_user)
    for manager in managers:
        db.refresh(manager)
    for employee in employees:
        db.refresh(employee)
    
    return admin_user, managers, employees

def create_kpi_periods():
    """Create KPI evaluation periods."""
    print("Creating KPI evaluation periods...")
    # Implementation depends on your specific KPI models
    # This would create a few evaluation periods

def create_kpi_evaluations(employees):
    """Create KPI evaluations for employees."""
    print("Creating KPI evaluations...")
    # Implementation depends on your specific KPI models
    # This would create evaluations for all employees

def create_360_sessions(employees, managers):
    """Create 360-degree evaluation sessions."""
    print("Creating 360-degree evaluation sessions...")
    # Implementation depends on your specific 360-degree models
    # This would create sessions with participants and answers

def create_pdp_plans(employees):
    """Create Personal Development Plans."""
    print("Creating Personal Development Plans...")
    # Implementation depends on your specific PDP models
    # This would create development plans and items

def seed_database():
    """Main function to seed the database with test data."""
    print("Starting database seeding...")
    
    # Create database session
    db = next(get_db())
    
    try:
        # Clear existing data
        clear_existing_data(db)
        
        # Create users
        admin, managers, employees = create_users(db)
        
        # Create KPI periods
        create_kpi_periods()
        
        # Create KPI evaluations
        create_kpi_evaluations(employees)
        
        # Create 360-degree sessions
        create_360_sessions(employees, managers)
        
        # Create PDP plans
        create_pdp_plans(employees)
        
        print("Database seeding completed successfully!")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()