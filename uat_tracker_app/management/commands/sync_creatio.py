from django.core.management.base import BaseCommand
from django.utils import timezone
from uat_tracker_app.models import UATCase, Note
from uat_tracker_app.creatio_service import CreatioService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync cases with Creatio CRM'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--full-sync',
            action='store_true',
            help='Perform a full sync instead of incremental',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test connection to Creatio',
        )
    
    def handle(self, *args, **options):
        creatio_service = CreatioService()
        
        if options['test_connection']:
            self.test_connection(creatio_service)
            return
        
        if options['full_sync']:
            self.stdout.write('Performing full sync with Creatio...')
            self.full_sync(creatio_service)
        else:
            self.stdout.write('Performing incremental sync with Creatio...')
            self.incremental_sync(creatio_service)
    
    def test_connection(self, creatio_service):
        """Test connection to Creatio"""
        try:
            success, message = creatio_service.test_connection()
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creatio connection test successful: {message}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Creatio connection test failed: {message}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Connection test error: {e}')
            )
    
    def full_sync(self, creatio_service):
        """Perform full sync of all cases"""
        try:
            # Sync all pending cases to Creatio
            pending_cases = UATCase.objects.filter(sync_status='pending')
            
            for case in pending_cases:
                self.sync_case_to_creatio(creatio_service, case)
            
            # Pull updates from Creatio
            self.pull_updates_from_creatio(creatio_service)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Full sync completed successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Full sync failed: {e}')
            )
    
    def incremental_sync(self, creatio_service):
        """Perform incremental sync based on last sync time"""
        try:
            # Sync pending cases to Creatio
            pending_cases = UATCase.objects.filter(sync_status='pending')
            
            for case in pending_cases:
                self.sync_case_to_creatio(creatio_service, case)
            
            # Pull recent updates from Creatio
            # Get the most recent sync time
            last_synced_case = UATCase.objects.filter(
                last_synced__isnull=False
            ).order_by('-last_synced').first()
            
            last_sync_time = None
            if last_synced_case:
                last_sync_time = last_synced_case.last_synced
            
            self.pull_updates_from_creatio(creatio_service, last_sync_time)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Incremental sync completed successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Incremental sync failed: {e}')
            )
    
    def sync_case_to_creatio(self, creatio_service, case):
        """Sync a single case to Creatio"""
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
                # Update existing case
                result = creatio_service.update_case(case.creatio_id, case_data)
                self.stdout.write(f'Updated case {case.id} in Creatio')
            else:
                # Create new case
                result = creatio_service.create_case(case_data)
                case.creatio_id = result.get('Id')
                self.stdout.write(f'Created case {case.id} in Creatio with ID {case.creatio_id}')
            
            case.sync_status = 'synced'
            case.last_synced = timezone.now()
            case.save()
            
            # Add system note
            Note.objects.create(
                case=case,
                author=case.requestor,
                content=f'Case synchronized with Creatio. Creatio ID: {case.creatio_id}'
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to sync case {case.id}: {e}')
            )
            logger.error(f'Failed to sync case {case.id}: {e}')
    
    def pull_updates_from_creatio(self, creatio_service, last_sync_time=None):
        """Pull updates from Creatio"""
        try:
            creatio_cases = creatio_service.sync_cases_from_creatio(last_sync_time)
            
            for creatio_case in creatio_cases:
                self.update_local_case_from_creatio(creatio_case)
            
            self.stdout.write(f'Pulled {len(creatio_cases)} updates from Creatio')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to pull updates from Creatio: {e}')
            )
            logger.error(f'Failed to pull updates from Creatio: {e}')
    
    def update_local_case_from_creatio(self, creatio_case):
        """Update local case with data from Creatio"""
        try:
            creatio_id = creatio_case.get('Id')
            
            # Find local case by Creatio ID
            try:
                local_case = UATCase.objects.get(creatio_id=creatio_id)
            except UATCase.DoesNotExist:
                self.stdout.write(f'Local case not found for Creatio ID {creatio_id}')
                return
            
            # Update local case with Creatio data
            local_case.subject = creatio_case.get('Subject', local_case.subject)
            local_case.description = creatio_case.get('Description', local_case.description)
            local_case.status = self._map_creatio_status(creatio_case.get('Status'))
            local_case.priority = self._map_creatio_priority(creatio_case.get('Priority'))
            local_case.last_synced = timezone.now()
            local_case.save()
            
            self.stdout.write(f'Updated local case {local_case.id} from Creatio')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to update local case: {e}')
            )
    
    def _map_creatio_status(self, creatio_status):
        """Map Creatio status to local status"""
        status_mapping = {
            'New': 'new',
            'In Progress': 'in-progress',
            'Resolved': 'resolved',
            'Closed': 'closed'
        }
        return status_mapping.get(creatio_status, 'new')
    
    def _map_creatio_priority(self, creatio_priority):
        """Map Creatio priority to local priority"""
        priority_mapping = {
            'Low': 'low',
            'Medium': 'medium',
            'High': 'high'
        }
        return priority_mapping.get(creatio_priority, 'medium')