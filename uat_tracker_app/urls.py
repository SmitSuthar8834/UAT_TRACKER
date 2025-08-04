from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # Authentication
    path('api/login/', views.user_login, name='user_login'),
    path('api/logout/', views.user_logout, name='user_logout'),
    
    # Lookups and Companies
    path('api/companies/', views.get_companies, name='get_companies'),
    path('api/lookups/', views.get_lookups, name='get_lookups'),
    
    # Cases
    path('api/cases/', views.get_user_cases, name='get_user_cases'),
    path('api/cases/create/', views.create_case, name='create_case'),
    path('api/cases/<int:case_id>/', views.get_case_details, name='get_case_details'),
    path('api/cases/<int:case_id>/update-field/', views.update_case_field, name='update_case_field'),
    path('api/cases/<int:case_id>/add-note/', views.add_note, name='add_note'),
    path('api/cases/<int:case_id>/upload/', views.upload_attachment, name='upload_attachment'),
    path('api/cases/<int:case_id>/assign/', views.assign_case, name='assign_case'),
    
    # Profile Management
    path('api/profile/', views.get_user_profile, name='get_user_profile'),
    path('api/profile/update/', views.update_user_profile, name='update_user_profile'),
    path('api/profile/upload-image/', views.upload_profile_image, name='upload_profile_image'),
    
    # Company Management
    path('api/company/employees/', views.get_company_employees, name='get_company_employees'),
    
    # Dashboard
    path('api/dashboard-stats/', views.get_enhanced_dashboard_stats, name='get_enhanced_dashboard_stats'),
    
    # Creatio Integration
    path('api/sync-creatio/', views.sync_with_creatio, name='sync_with_creatio'),
    
    # Utilities
    path('api/demo-data/', views.create_demo_data, name='create_demo_data'),
    path('api/health/', views.health_check, name='health_check'),
    
    # Dynamic Admin Panel
    path('api/dynamic-pages/', views.get_dynamic_pages, name='get_dynamic_pages'),
    path('api/dynamic-pages/<slug:slug>/', views.get_dynamic_page, name='get_dynamic_page'),
    path('api/dynamic-widgets/', views.get_dynamic_widgets, name='get_dynamic_widgets'),
    path('api/system-settings/', views.get_system_settings, name='get_system_settings'),
]