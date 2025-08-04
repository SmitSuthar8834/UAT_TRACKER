#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uat_tracker.settings')
django.setup()

from uat_tracker_app.models import DynamicPage, DynamicWidget, SystemSetting

def create_sample_content():
    # Create a sample dynamic page
    page, created = DynamicPage.objects.get_or_create(
        slug='help',
        defaults={
            'title': 'Help & Documentation',
            'content': '''
            <div class="container-fluid">
                <h2>UAT Tracker Help</h2>
                <p>This is a dynamic page created from the admin panel!</p>
                
                <div class="row">
                    <div class="col-md-6">
                        <h4>Getting Started</h4>
                        <ul>
                            <li>Create test cases</li>
                            <li>Track progress</li>
                            <li>Manage teams</li>
                            <li>Generate reports</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h4>Features</h4>
                        <ul>
                            <li>Multi-company support</li>
                            <li>Role-based access</li>
                            <li>Creatio integration</li>
                            <li>Dynamic admin panel</li>
                        </ul>
                    </div>
                </div>
            </div>
            ''',
            'icon': 'fas fa-question-circle',
            'menu_order': 10
        }
    )
    
    # Create sample widgets
    widget1, created = DynamicWidget.objects.get_or_create(
        title='System Status',
        defaults={
            'widget_type': 'stat',
            'content': '{"value": "Online", "color": "success", "icon": "fas fa-server"}',
            'width': 'col-md-4',
            'order': 1
        }
    )
    
    widget2, created = DynamicWidget.objects.get_or_create(
        title='Active Users',
        defaults={
            'widget_type': 'stat',
            'content': '{"value": "24", "color": "info", "icon": "fas fa-users"}',
            'width': 'col-md-4',
            'order': 2
        }
    )
    
    # Create system settings
    setting1, created = SystemSetting.objects.get_or_create(
        key='app_name',
        defaults={
            'value': 'UAT Tracker Pro',
            'description': 'Application display name',
            'setting_type': 'text'
        }
    )
    
    setting2, created = SystemSetting.objects.get_or_create(
        key='max_file_size',
        defaults={
            'value': '10',
            'description': 'Maximum file upload size in MB',
            'setting_type': 'number'
        }
    )
    
    setting3, created = SystemSetting.objects.get_or_create(
        key='enable_notifications',
        defaults={
            'value': 'true',
            'description': 'Enable email notifications',
            'setting_type': 'boolean'
        }
    )
    
    print("Sample dynamic content created successfully!")
    print(f"- Dynamic page: {page.title}")
    print(f"- Widgets: {widget1.title}, {widget2.title}")
    print(f"- Settings: {setting1.key}, {setting2.key}, {setting3.key}")

if __name__ == '__main__':
    create_sample_content()