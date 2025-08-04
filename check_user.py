#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uat_tracker.settings')
django.setup()

from django.contrib.auth.models import User
from uat_tracker_app.models import UserProfile, Company

def check_user():
    try:
        user = User.objects.get(username='Supervisor')
        print(f"User: {user.username}")
        print(f"Email: {user.email}")
        
        if hasattr(user, 'profile'):
            profile = user.profile
            print(f"Has profile: Yes")
            print(f"Company: {profile.company}")
            print(f"Is Admin: {profile.is_admin}")
        else:
            print("Has profile: No")
            # Create a profile and company if missing
            company, created = Company.objects.get_or_create(
                name="Default Company",
                defaults={'description': 'Default company for users'}
            )
            
            profile = UserProfile.objects.create(
                user=user,
                company=company,
                is_admin=True,
                can_assign_cases=True
            )
            print(f"Created profile with company: {company.name}")
            
    except User.DoesNotExist:
        print("User 'Supervisor' not found")

if __name__ == '__main__':
    check_user()