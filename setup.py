#!/usr/bin/env python3
"""
Setup script for UAT Tracker Django application
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.contrib.auth.models import User

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uat_tracker.settings')
    django.setup()

def create_superuser():
    """Create a superuser if it doesn't exist"""
    from django.contrib.auth.models import User
    
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        print("✓ Superuser created: admin / admin123")
        return admin_user
    else:
        print("✓ Superuser already exists")
        return User.objects.get(username='admin')

def create_lookups():
    """Create lookup data for dropdowns"""
    from uat_tracker_app.models import Priority, Status, Environment, CaseType
    
    # Create Priorities
    priorities = [
        {'name': 'Low', 'value': 'low', 'color': '#28a745', 'order': 1},
        {'name': 'Medium', 'value': 'medium', 'color': '#ffc107', 'order': 2},
        {'name': 'High', 'value': 'high', 'color': '#dc3545', 'order': 3},
        {'name': 'Critical', 'value': 'critical', 'color': '#6f42c1', 'order': 4},
    ]
    
    for priority_data in priorities:
        priority, created = Priority.objects.get_or_create(
            value=priority_data['value'],
            defaults=priority_data
        )
        if created:
            print(f"✓ Created priority: {priority.name}")
    
    # Create Statuses
    statuses = [
        {'name': 'New', 'value': 'new', 'color': '#007bff', 'order': 1},
        {'name': 'In Progress', 'value': 'in-progress', 'color': '#ffc107', 'order': 2},
        {'name': 'Resolved', 'value': 'resolved', 'color': '#28a745', 'order': 3},
        {'name': 'Closed', 'value': 'closed', 'color': '#6c757d', 'order': 4},
        {'name': 'Reopened', 'value': 'reopened', 'color': '#fd7e14', 'order': 5},
        {'name': 'Cancelled', 'value': 'cancelled', 'color': '#dc3545', 'order': 6},
    ]
    
    for status_data in statuses:
        status, created = Status.objects.get_or_create(
            value=status_data['value'],
            defaults=status_data
        )
        if created:
            print(f"✓ Created status: {status.name}")
    
    # Create Environments
    environments = [
        {'name': 'Development', 'value': 'development', 'color': '#17a2b8', 'order': 1},
        {'name': 'Test', 'value': 'test', 'color': '#ffc107', 'order': 2},
        {'name': 'Staging', 'value': 'staging', 'color': '#fd7e14', 'order': 3},
        {'name': 'Production', 'value': 'production', 'color': '#dc3545', 'order': 4},
    ]
    
    for env_data in environments:
        environment, created = Environment.objects.get_or_create(
            value=env_data['value'],
            defaults=env_data
        )
        if created:
            print(f"✓ Created environment: {environment.name}")
    
    # Create Case Types
    case_types = [
        {'name': 'Bug', 'value': 'bug', 'color': '#dc3545', 'order': 1},
        {'name': 'Feature Request', 'value': 'feature-request', 'color': '#007bff', 'order': 2},
        {'name': 'Enhancement', 'value': 'enhancement', 'color': '#28a745', 'order': 3},
        {'name': 'Question', 'value': 'question', 'color': '#17a2b8', 'order': 4},
        {'name': 'Change Request', 'value': 'change-request', 'color': '#ffc107', 'order': 5},
    ]
    
    for type_data in case_types:
        case_type, created = CaseType.objects.get_or_create(
            value=type_data['value'],
            defaults=type_data
        )
        if created:
            print(f"✓ Created case type: {case_type.name}")

def create_demo_data():
    """Create demo companies and test users"""
    from uat_tracker_app.models import Company, UserProfile
    from django.contrib.auth.models import User
    
    # Create companies
    companies_data = [
        {'name': 'ACME Corporation', 'description': 'Leading technology solutions provider'},
        {'name': 'Tech Solutions Inc', 'description': 'Innovative software development company'},
        {'name': 'Global Systems Ltd', 'description': 'Enterprise system integration specialists'}
    ]
    
    created_companies = []
    for company_data in companies_data:
        company, created = Company.objects.get_or_create(
            name=company_data['name'],
            defaults=company_data
        )
        if created:
            print(f"✓ Created company: {company_data['name']}")
        created_companies.append(company)
    
    # Create admin profile
    admin_user = User.objects.get(username='admin')
    admin_profile, created = UserProfile.objects.get_or_create(
        user=admin_user,
        defaults={
            'company': created_companies[0],
            'job_title': 'System Administrator',
            'department': 'IT',
            'is_admin': True,
            'can_assign_cases': True
        }
    )
    if created:
        print("✓ Created admin profile")
    
    # Create test users
    test_users = [
        {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'test123',
            'first_name': 'Test',
            'last_name': 'User',
            'company': created_companies[0],
            'job_title': 'QA Tester',
            'department': 'Quality Assurance'
        },
        {
            'username': 'manager',
            'email': 'manager@example.com',
            'password': 'manager123',
            'first_name': 'Project',
            'last_name': 'Manager',
            'company': created_companies[0],
            'job_title': 'Project Manager',
            'department': 'Project Management',
            'can_assign_cases': True
        }
    ]
    
    for user_data in test_users:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            
            UserProfile.objects.create(
                user=user,
                company=user_data['company'],
                job_title=user_data['job_title'],
                department=user_data['department'],
                can_assign_cases=user_data.get('can_assign_cases', False)
            )
            
            print(f"✓ Created user: {user_data['username']} / {user_data['password']}")

def main():
    """Main setup function"""
    print("🚀 Setting up Modern UAT Tracker...")
    
    # Setup Django
    setup_django()
    
    # Run migrations
    print("\n📦 Running migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create lookups
    print("\n📋 Creating lookup data...")
    create_lookups()
    
    # Create superuser
    print("\n👤 Setting up users...")
    create_superuser()
    
    # Create demo data
    print("\n📊 Creating demo data...")
    create_demo_data()
    
    print("\n✅ Setup complete!")
    print("\nYou can now:")
    print("1. Run the server: python manage.py runserver")
    print("2. Access admin: http://127.0.0.1:8000/admin/ (admin/admin123)")
    print("3. Access app: http://127.0.0.1:8000/")
    print("   - Test User: testuser / test123")
    print("   - Manager: manager / manager123")
    print("4. Configure Creatio integration in admin panel")
    print("5. Test Creatio sync: python manage.py sync_creatio --test-connection")

if __name__ == '__main__':
    main()