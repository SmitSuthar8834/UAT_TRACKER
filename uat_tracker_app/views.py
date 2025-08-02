from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
import json
import logging
from .models import (
    UATCase, Note, Attachment, Company, UserProfile, CreatioConfig,
    Priority, Status, Environment, CaseType
)
from .creatio_service import CreatioService

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    """
    Serve the main UAT tracker HTML page
    """
    return render(request, 'modern_uat_tracker.html')

@csrf_exempt
def user_login(request):
    """
    Handle user login
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        company_id = data.get('company')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            company = get_object_or_404(Company, id=company_id)
            
            # Update user's company if needed
            # For simplicity, we're assuming the user's company is stored in profile
            # In a real app, you might have a UserProfile model
            
            return JsonResponse({
                'success': True,
                'user': {
                    'email': user.email,
                    'name': user.first_name + ' ' + user.last_name if user.first_name else user.username,
                    'company': company.name
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid credentials'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def user_logout(request):
    """
    Handle user logout
    """
    logout(request)
    return JsonResponse({'success': True})

@login_required
def get_user_cases(request):
    """
    Get cases for the logged-in user
    """
    cases = UATCase.objects.filter(requestor=request.user).order_by('-created_at')
    
    cases_data = []
    for case in cases:
        cases_data.append({
            'id': case.id,
            'subject': case.subject,
            'priority': case.priority,
            'environment': case.environment,
            'case_type': case.case_type,
            'description': case.description,
            'reproduction_steps': case.reproduction_steps,
            'status': case.status,
            'requestor': case.requestor.username,
            'company': case.company.name,
            'created_at': case.created_at.isoformat(),
            'creatio_id': case.creatio_id,
            'sync_status': case.sync_status,
            'notes_count': case.notes.count(),
            'attachments_count': case.attachments.count()
        })
    
    return JsonResponse({'cases': cases_data})

@login_required
def create_case(request):
    """
    Create a new UAT case
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Get company (in a real app, this would come from user's profile)
        company = Company.objects.first()  # For demo purposes
        
        case = UATCase.objects.create(
            subject=data.get('subject'),
            description=data.get('description'),
            reproduction_steps=data.get('reproduction_steps', ''),
            priority=data.get('priority', 'medium'),
            environment=data.get('environment'),
            case_type=data.get('type', 'bug'),
            requestor=request.user,
            company=company
        )
        
        # Sync with Creatio
        try:
            creatio_service = CreatioService()
            case_data = {
                'subject': case.subject,
                'description': case.description,
                'priority': case.priority,
                'status': case.status,
                'case_type': case.case_type,
                'reproduction_steps': case.reproduction_steps,
                'created_at': case.created_at.isoformat(),
            }
            
            result = creatio_service.create_case(case_data)
            case.creatio_id = result.get('Id', f'CR-{case.id}')
            case.sync_status = 'synced'
            case.last_synced = timezone.now()
            case.save()
            
            # Add system note about Creatio sync
            Note.objects.create(
                case=case,
                author=request.user,
                content=f'Case synchronized with Creatio. Case ID: {case.creatio_id}'
            )
            
            logger.info(f'Successfully synced case {case.id} with Creatio')
            
        except Exception as e:
            logger.error(f'Failed to sync case {case.id} with Creatio: {e}')
            case.sync_status = 'pending'
            case.save()
            
            # Add system note about sync failure
            Note.objects.create(
                case=case,
                author=request.user,
                content=f'Failed to sync with Creatio. Will retry later. Error: {str(e)}'
            )
        
        return JsonResponse({
            'success': True,
            'case': {
                'id': case.id,
                'subject': case.subject,
                'priority': case.priority,
                'environment': case.environment,
                'case_type': case.case_type,
                'description': case.description,
                'reproduction_steps': case.reproduction_steps,
                'status': case.status,
                'requestor': case.requestor.username,
                'company': case.company.name,
                'created_at': case.created_at.isoformat(),
                'creatio_id': case.creatio_id,
                'sync_status': case.sync_status,
                'notes': [],
                'attachments': []
            }
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_case_details(request, case_id):
    """
    Get details for a specific case
    """
    case = get_object_or_404(UATCase, id=case_id, requestor=request.user)
    
    # Get notes for the case
    notes = case.notes.all().order_by('-created_at')
    notes_data = []
    for note in notes:
        notes_data.append({
            'id': note.id,
            'author': note.author.username,
            'content': note.content,
            'timestamp': note.created_at.isoformat()
        })
    
    # Get attachments for the case
    attachments = case.attachments.all()
    attachments_data = []
    for attachment in attachments:
        attachments_data.append({
            'id': attachment.id,
            'filename': attachment.filename,
            'uploaded_by': attachment.uploaded_by.username,
            'uploaded_at': attachment.uploaded_at.isoformat()
        })
    
    case_data = {
        'id': case.id,
        'subject': case.subject,
        'priority': case.priority,
        'environment': case.environment,
        'case_type': case.case_type,
        'description': case.description,
        'reproduction_steps': case.reproduction_steps,
        'status': case.status,
        'requestor': case.requestor.username,
        'company': case.company.name,
        'created_at': case.created_at.isoformat(),
        'creatio_id': case.creatio_id,
        'sync_status': case.sync_status,
        'notes': notes_data,
        'attachments': attachments_data
    }
    
    return JsonResponse({'case': case_data})

@login_required
def update_case_field(request, case_id):
    """
    Update a specific field of a case
    """
    if request.method == 'POST':
        case = get_object_or_404(UATCase, id=case_id, requestor=request.user)
        data = json.loads(request.body)
        
        field = data.get('field')
        value = data.get('value')
        
        # Update the field
        if hasattr(case, field):
            setattr(case, field, value)
            case.save()
            
            # Add system note for status changes
            if field == 'status':
                Note.objects.create(
                    case=case,
                    author=request.user,
                    content=f'Status changed to: {value}'
                )
            
            # Sync with Creatio
            try:
                creatio_service = CreatioService()
                case_data = {
                    'subject': case.subject,
                    'description': case.description,
                    'priority': case.priority,
                    'status': case.status,
                    'case_type': case.case_type,
                    'reproduction_steps': case.reproduction_steps,
                }
                
                if case.creatio_id:
                    creatio_service.update_case(case.creatio_id, case_data)
                    case.sync_status = 'synced'
                    case.last_synced = timezone.now()
                    case.save()
                    logger.info(f'Successfully updated case {case.id} in Creatio')
                else:
                    case.sync_status = 'pending'
                    case.save()
                    
            except Exception as e:
                logger.error(f'Failed to sync case update with Creatio: {e}')
                case.sync_status = 'pending'
                case.save()
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid field'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def add_note(request, case_id):
    """
    Add a note to a case
    """
    if request.method == 'POST':
        case = get_object_or_404(UATCase, id=case_id, requestor=request.user)
        data = json.loads(request.body)
        
        note_content = data.get('content')
        if note_content:
            note = Note.objects.create(
                case=case,
                author=request.user,
                content=note_content
            )
            
            # Sync note with Creatio
            try:
                creatio_service = CreatioService()
                if case.creatio_id:
                    comment_data = {
                        'content': note.content,
                        'author': note.author.username,
                        'created_at': note.created_at.isoformat(),
                    }
                    creatio_service.add_case_comment(case.creatio_id, comment_data)
                    case.sync_status = 'synced'
                    case.last_synced = timezone.now()
                    case.save()
                    logger.info(f'Successfully synced note for case {case.id} with Creatio')
                else:
                    case.sync_status = 'pending'
                    case.save()
                    
            except Exception as e:
                logger.error(f'Failed to sync note with Creatio: {e}')
                case.sync_status = 'pending'
                case.save()
            
            return JsonResponse({
                'success': True,
                'note': {
                    'id': note.id,
                    'author': note.author.username,
                    'content': note.content,
                    'timestamp': note.created_at.isoformat()
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Note content is required'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# For demo purposes, we'll create some initial data if it doesn't exist
def create_demo_data(request):
    """
    Create demo companies and users
    """
    # Create companies if they don't exist
    companies = [
        {'name': 'ACME Corporation'},
        {'name': 'Tech Solutions Inc'},
        {'name': 'Global Systems Ltd'}
    ]
    
    for company_data in companies:
        company, created = Company.objects.get_or_create(
            name=company_data['name']
        )
    
    return JsonResponse({'success': True, 'message': 'Demo data created'})
@login_required
def get_companies(request):
    """
    Get list of companies for dropdown
    """
    companies = Company.objects.all()
    companies_data = []
    for company in companies:
        companies_data.append({
            'id': company.id,
            'name': company.name
        })
    
    return JsonResponse({'companies': companies_data})

@login_required
def sync_with_creatio(request):
    """
    Manual sync with Creatio
    """
    if request.method == 'POST':
        try:
            creatio_service = CreatioService()
            
            # Test connection first
            success, message = creatio_service.test_connection()
            if not success:
                return JsonResponse({
                    'success': False, 
                    'error': f'Creatio connection failed: {message}'
                })
            
            # Sync pending cases
            pending_cases = UATCase.objects.filter(
                requestor=request.user, 
                sync_status='pending'
            )
            
            synced_count = 0
            failed_count = 0
            
            for case in pending_cases:
                try:
                    case_data = {
                        'subject': case.subject,
                        'description': case.description,
                        'priority': case.priority,
                        'status': case.status,
                        'case_type': case.case_type,
                        'reproduction_steps': case.reproduction_steps,
                        'created_at': case.created_at.isoformat(),
                    }
                    
                    if case.creatio_id:
                        creatio_service.update_case(case.creatio_id, case_data)
                    else:
                        result = creatio_service.create_case(case_data)
                        case.creatio_id = result.get('Id', f'CR-{case.id}')
                    
                    case.sync_status = 'synced'
                    case.last_synced = timezone.now()
                    case.save()
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f'Failed to sync case {case.id}: {e}')
                    failed_count += 1
            
            return JsonResponse({
                'success': True,
                'synced_count': synced_count,
                'failed_count': failed_count,
                'message': f'Synced {synced_count} cases, {failed_count} failed'
            })
            
        except Exception as e:
            logger.error(f'Manual sync failed: {e}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_dashboard_stats(request):
    """
    Get dashboard statistics
    """
    user_cases = UATCase.objects.filter(requestor=request.user)
    
    stats = {
        'total_cases': user_cases.count(),
        'open_cases': user_cases.filter(status__in=['new', 'in-progress']).count(),
        'high_priority': user_cases.filter(priority='high').count(),
        'resolved_cases': user_cases.filter(status__in=['resolved', 'closed']).count(),
        'pending_sync': user_cases.filter(sync_status='pending').count(),
        'synced_cases': user_cases.filter(sync_status='synced').count(),
    }
    
    # Recent activity
    recent_cases = user_cases.order_by('-updated_at')[:5]
    recent_activity = []
    
    for case in recent_cases:
        recent_activity.append({
            'id': case.id,
            'subject': case.subject,
            'status': case.status,
            'priority': case.priority,
            'environment': case.environment,
            'updated_at': case.updated_at.isoformat(),
            'sync_status': case.sync_status
        })
    
    return JsonResponse({
        'stats': stats,
        'recent_activity': recent_activity
    })

@login_required
def upload_attachment(request, case_id):
    """
    Upload attachment to a case
    """
    if request.method == 'POST':
        case = get_object_or_404(UATCase, id=case_id, requestor=request.user)
        
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'})
        
        uploaded_file = request.FILES['file']
        
        # Create attachment
        attachment = Attachment.objects.create(
            case=case,
            file=uploaded_file,
            filename=uploaded_file.name,
            uploaded_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'attachment': {
                'id': attachment.id,
                'filename': attachment.filename,
                'uploaded_by': attachment.uploaded_by.username,
                'uploaded_at': attachment.uploaded_at.isoformat(),
                'url': attachment.file.url
            }
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def health_check(request):
    """
    Health check endpoint
    """
    try:
        # Test database connection
        Company.objects.count()
        
        # Test Creatio connection
        creatio_service = CreatioService()
        creatio_success, creatio_message = creatio_service.test_connection()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'creatio': {
                'status': 'connected' if creatio_success else 'disconnected',
                'message': creatio_message
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)

@login_required
def get_lookups(request):
    """
    Get all lookup data for dropdowns
    """
    try:
        lookups = {
            'priorities': [
                {
                    'id': p.id,
                    'name': p.name,
                    'value': p.value,
                    'color': p.color
                } for p in Priority.objects.filter(is_active=True)
            ],
            'statuses': [
                {
                    'id': s.id,
                    'name': s.name,
                    'value': s.value,
                    'color': s.color
                } for s in Status.objects.filter(is_active=True)
            ],
            'environments': [
                {
                    'id': e.id,
                    'name': e.name,
                    'value': e.value,
                    'color': e.color
                } for e in Environment.objects.filter(is_active=True)
            ],
            'caseTypes': [
                {
                    'id': ct.id,
                    'name': ct.name,
                    'value': ct.value,
                    'color': ct.color
                } for ct in CaseType.objects.filter(is_active=True)
            ]
        }
        
        return JsonResponse({
            'success': True,
            'lookups': lookups
        })
    except Exception as e:
        logger.error(f'Error loading lookups: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_user_profile(request):
    """
    Get user profile information
    """
    try:
        profile = request.user.profile
        
        profile_data = {
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'full_name': request.user.get_full_name(),
            },
            'profile': {
                'phone': profile.phone,
                'department': profile.department,
                'job_title': profile.job_title,
                'profile_image': profile.profile_image.url if profile.profile_image else None,
                'is_admin': profile.is_admin,
                'can_assign_cases': profile.can_assign_cases,
            },
            'company': {
                'id': profile.company.id,
                'name': profile.company.name,
                'logo': profile.company.logo.url if profile.company.logo else None,
            }
        }
        
        return JsonResponse({
            'success': True,
            'profile': profile_data
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User profile not found'
        })
    except Exception as e:
        logger.error(f'Error loading user profile: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def update_user_profile(request):
    """
    Update user profile information
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Update User model
                user = request.user
                user.first_name = data.get('first_name', user.first_name)
                user.last_name = data.get('last_name', user.last_name)
                user.save()
                
                # Update UserProfile model
                profile = user.profile
                profile.phone = data.get('phone', profile.phone)
                profile.department = data.get('department', profile.department)
                profile.job_title = data.get('job_title', profile.job_title)
                profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile updated successfully'
            })
        except Exception as e:
            logger.error(f'Error updating user profile: {e}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def upload_profile_image(request):
    """
    Upload user profile image
    """
    if request.method == 'POST':
        try:
            if 'profile_image' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'No image file provided'
                })
            
            profile = request.user.profile
            profile.profile_image = request.FILES['profile_image']
            profile.save()
            
            return JsonResponse({
                'success': True,
                'image_url': profile.profile_image.url,
                'message': 'Profile image updated successfully'
            })
        except Exception as e:
            logger.error(f'Error uploading profile image: {e}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_company_employees(request):
    """
    Get list of employees in the user's company for assignment
    """
    try:
        user_profile = request.user.profile
        employees = UserProfile.objects.filter(
            company=user_profile.company
        ).select_related('user')
        
        employees_data = []
        for emp in employees:
            employees_data.append({
                'id': emp.user.id,
                'name': emp.user.get_full_name() or emp.user.username,
                'email': emp.user.email,
                'job_title': emp.job_title,
                'department': emp.department,
                'can_assign_cases': emp.can_assign_cases,
                'profile_image': emp.profile_image.url if emp.profile_image else None
            })
        
        return JsonResponse({
            'success': True,
            'employees': employees_data
        })
    except Exception as e:
        logger.error(f'Error loading company employees: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_enhanced_dashboard_stats(request):
    """
    Get enhanced dashboard statistics with more details
    """
    try:
        user_profile = request.user.profile
        
        # Base query - filter by company for multi-tenancy
        if user_profile.is_admin:
            # Admin can see all company cases
            base_cases = UATCase.objects.filter(company=user_profile.company)
        else:
            # Regular users see only their cases
            base_cases = UATCase.objects.filter(requestor=request.user)
        
        # Calculate statistics
        total_cases = base_cases.count()
        new_cases = base_cases.filter(status__value='new').count()
        in_progress_cases = base_cases.filter(status__value='in-progress').count()
        resolved_cases = base_cases.filter(status__value='resolved').count()
        closed_cases = base_cases.filter(status__value='closed').count()
        cancelled_cases = base_cases.filter(status__value='cancelled').count()
        reopened_cases = base_cases.filter(status__value='reopened').count()
        
        high_priority = base_cases.filter(priority__value='high').count()
        pending_sync = base_cases.filter(sync_status='pending').count()
        
        # Recent activity
        recent_cases = base_cases.order_by('-updated_at')[:10]
        recent_activity = []
        
        for case in recent_cases:
            recent_activity.append({
                'id': case.id,
                'case_number': case.case_number,
                'subject': case.subject,
                'status': case.status.name,
                'priority': case.priority.name,
                'environment': case.environment.name,
                'requestor': case.requestor.get_full_name() or case.requestor.username,
                'assigned_to': case.assigned_to.get_full_name() if case.assigned_to else None,
                'updated_at': case.updated_at.isoformat(),
                'sync_status': case.sync_status
            })
        
        # Status distribution for charts
        status_distribution = []
        for status in Status.objects.filter(is_active=True):
            count = base_cases.filter(status=status).count()
            if count > 0:
                status_distribution.append({
                    'name': status.name,
                    'value': count,
                    'color': status.color
                })
        
        # Priority distribution
        priority_distribution = []
        for priority in Priority.objects.filter(is_active=True):
            count = base_cases.filter(priority=priority).count()
            if count > 0:
                priority_distribution.append({
                    'name': priority.name,
                    'value': count,
                    'color': priority.color
                })
        
        stats = {
            'total_cases': total_cases,
            'new_cases': new_cases,
            'in_progress_cases': in_progress_cases,
            'resolved_cases': resolved_cases,
            'closed_cases': closed_cases,
            'cancelled_cases': cancelled_cases,
            'reopened_cases': reopened_cases,
            'high_priority': high_priority,
            'pending_sync': pending_sync,
            'open_cases': new_cases + in_progress_cases + reopened_cases,
            'status_distribution': status_distribution,
            'priority_distribution': priority_distribution
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'recent_activity': recent_activity
        })
    except Exception as e:
        logger.error(f'Error loading enhanced dashboard stats: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def assign_case(request, case_id):
    """
    Assign a case to a user
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            assigned_to_id = data.get('assigned_to_id')
            
            case = get_object_or_404(UATCase, id=case_id)
            
            # Check permissions
            user_profile = request.user.profile
            if not (user_profile.can_assign_cases or user_profile.is_admin or case.requestor == request.user):
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have permission to assign this case'
                })
            
            # Assign the case
            if assigned_to_id:
                assigned_user = get_object_or_404(User, id=assigned_to_id)
                # Verify the assigned user is in the same company
                if assigned_user.profile.company != user_profile.company:
                    return JsonResponse({
                        'success': False,
                        'error': 'Cannot assign case to user from different company'
                    })
                case.assigned_to = assigned_user
            else:
                case.assigned_to = None
            
            case.save()
            
            # Add note about assignment
            assignee_name = case.assigned_to.get_full_name() if case.assigned_to else 'Unassigned'
            Note.objects.create(
                case=case,
                author=request.user,
                content=f'Case assigned to: {assignee_name}'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Case assigned to {assignee_name}'
            })
        except Exception as e:
            logger.error(f'Error assigning case: {e}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})