import requests
import json
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

class CreatioService:
    """
    Service class for integrating with Creatio CRM using OAuth 2.0 client credentials
    """
    
    def __init__(self, company=None):
        self.company = company
        self.config = None
        self.access_token = None
        self.token_expires_at = None
        self.session = requests.Session()
        
        if company:
            try:
                from .models import CreatioConfig
                self.config = CreatioConfig.objects.get(company=company, is_active=True)
            except CreatioConfig.DoesNotExist:
                logger.warning(f"No active Creatio config found for company: {company.name}")
                self.config = None
    
    def _decrypt_secret(self, encrypted_secret):
        """
        Decrypt the stored client secret
        """
        try:
            # In production, use a proper key management system
            key = settings.SECRET_KEY[:32].encode().ljust(32, b'0')[:32]
            f = Fernet(key)
            return f.decrypt(encrypted_secret.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt secret: {e}")
            return encrypted_secret  # Fallback to plain text for development
    
    def _get_config_values(self):
        """
        Get configuration values from database or fallback to settings
        """
        if self.config:
            return {
                'base_url': self.config.base_url.rstrip('/'),
                'identity_service_url': getattr(self.config, 'identity_service_url', 'https://myidentityservice.com').rstrip('/'),
                'client_id': self.config.client_id,
                'client_secret': self._decrypt_secret(self.config.client_secret) if self.config.client_secret else '',
            }
        else:
            # Fallback to settings for backward compatibility
            base_url = getattr(settings, 'CREATIO_BASE_URL', '').rstrip('/')
            return {
                'base_url': base_url,
                'identity_service_url': getattr(settings, 'CREATIO_IDENTITY_URL', 'https://myidentityservice.com').rstrip('/'),
                'client_id': getattr(settings, 'CREATIO_CLIENT_ID', ''),
                'client_secret': getattr(settings, 'CREATIO_CLIENT_SECRET', ''),
            }
    
    def get_access_token(self):
        """
        Get OAuth access token using client credentials flow
        """
        # Check if we have a valid token
        if (self.access_token and self.token_expires_at and 
            datetime.now() < self.token_expires_at - timedelta(minutes=5)):
            return self.access_token
        
        config = self._get_config_values()
        
        if not all([config['identity_service_url'], config['client_id'], config['client_secret']]):
            raise Exception("Creatio OAuth configuration is incomplete. Please check client_id and client_secret.")
        
        # OAuth 2.0 client credentials flow
        token_url = f"{config['identity_service_url']}/connect/token"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Successfully obtained OAuth access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get OAuth token: {e}")
            raise Exception(f"Failed to get OAuth token: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from OAuth service: {e}")
            raise Exception(f"Invalid response from OAuth service: {e}")
        except KeyError as e:
            logger.error(f"Missing access_token in OAuth response: {e}")
            raise Exception(f"Invalid OAuth response format: {e}")
    
    def make_authenticated_request(self, method, endpoint, data=None, service_type='odata', params=None):
        """
        Make an authenticated request to Creatio API using OAuth Bearer token
        """
        # Get access token
        access_token = self.get_access_token()
        
        config = self._get_config_values()
        
        # Build URL based on service type
        if service_type == 'odata':
            url = f"{config['base_url']}/0/odata/{endpoint}"
        elif service_type == 'dataservice':
            url = f"{config['base_url']}/0/DataService/json/SyncReply/{endpoint}"
        elif service_type == 'servicemodel':
            url = f"{config['base_url']}/0/ServiceModel/{endpoint}"
        else:
            url = f"{config['base_url']}/0/{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'ForceUseSession': 'true'
        }
        
        # Add CSRF token for certain operations
        csrf_token = 'p3peDzlxSo7qOL5TM.Xbq'  # You may need to get this dynamically
        headers['BPMCSRF'] = csrf_token
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params or data, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle different response types
            if response.content:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {'success': True, 'content': response.text}
            else:
                return {'success': True}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Creatio API request failed: {e}")
            # If authentication failed, reset token
            if hasattr(e, 'response') and e.response and e.response.status_code in [401, 403]:
                self.access_token = None
                self.token_expires_at = None
            raise Exception(f"Creatio API request failed: {e}")
    
    def create_case(self, case_data):
        """
        Create a case in Creatio using DataService
        """
        # Map our case data to Creatio case structure
        creatio_case = {
            'Subject': case_data.get('subject'),
            'Description': case_data.get('description'),
            'Symptoms': case_data.get('reproduction_steps', ''),
            'Origin': 'UAT Tracker',
            'RegisteredOn': case_data.get('created_at'),
            # Map priority, status, and category using lookup values
            'PriorityId': self._get_priority_id(case_data.get('priority')),
            'StatusId': self._get_status_id(case_data.get('status')),
            'CategoryId': self._get_category_id(case_data.get('case_type')),
        }
        
        # Remove None values
        creatio_case = {k: v for k, v in creatio_case.items() if v is not None}
        
        try:
            # Use DataService for creating records
            insert_query = {
                'rootSchemaName': 'Case',
                'operationType': 0,  # Insert operation
                'columnValues': creatio_case
            }
            
            result = self.make_authenticated_request('POST', 'InsertQuery', insert_query, 'dataservice')
            
            if result.get('success'):
                case_id = result.get('id')
                logger.info(f"Successfully created case in Creatio with ID: {case_id}")
                return {'Id': case_id, 'success': True}
            else:
                error_msg = result.get('errorInfo', {}).get('message', 'Unknown error')
                raise Exception(f"Creatio case creation failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Failed to create case in Creatio: {e}")
            raise
    
    def update_case(self, creatio_id, case_data):
        """
        Update a case in Creatio using DataService
        """
        # Map our case data to Creatio case structure
        creatio_case = {
            'Subject': case_data.get('subject'),
            'Description': case_data.get('description'),
            'Symptoms': case_data.get('reproduction_steps', ''),
            'PriorityId': self._get_priority_id(case_data.get('priority')),
            'StatusId': self._get_status_id(case_data.get('status')),
            'CategoryId': self._get_category_id(case_data.get('case_type')),
        }
        
        # Remove None values
        creatio_case = {k: v for k, v in creatio_case.items() if v is not None}
        
        try:
            # Use DataService for updating records
            update_query = {
                'rootSchemaName': 'Case',
                'operationType': 1,  # Update operation
                'filters': {
                    'filterType': 1,
                    'comparisonType': 3,
                    'isEnabled': True,
                    'trimDateTimeParameterToDate': False,
                    'leftExpression': {
                        'expressionType': 0,
                        'columnPath': 'Id'
                    },
                    'rightExpression': {
                        'expressionType': 2,
                        'parameter': {
                            'dataValueType': 0,
                            'value': creatio_id
                        }
                    }
                },
                'columnValues': creatio_case
            }
            
            result = self.make_authenticated_request('POST', 'UpdateQuery', update_query, 'dataservice')
            
            if result.get('success'):
                logger.info(f"Successfully updated case in Creatio: {creatio_id}")
                return {'success': True}
            else:
                error_msg = result.get('errorInfo', {}).get('message', 'Unknown error')
                raise Exception(f"Creatio case update failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Failed to update case in Creatio: {e}")
            raise
    
    def get_case(self, creatio_id):
        """
        Get a case from Creatio using DataService
        """
        try:
            select_query = {
                'rootSchemaName': 'Case',
                'operationType': 0,  # Select operation
                'filters': {
                    'filterType': 1,
                    'comparisonType': 3,
                    'isEnabled': True,
                    'trimDateTimeParameterToDate': False,
                    'leftExpression': {
                        'expressionType': 0,
                        'columnPath': 'Id'
                    },
                    'rightExpression': {
                        'expressionType': 2,
                        'parameter': {
                            'dataValueType': 0,
                            'value': creatio_id
                        }
                    }
                },
                'columns': {
                    'items': {
                        'Id': {'expression': {'expressionType': 0, 'columnPath': 'Id'}},
                        'Subject': {'expression': {'expressionType': 0, 'columnPath': 'Subject'}},
                        'Description': {'expression': {'expressionType': 0, 'columnPath': 'Description'}},
                        'Symptoms': {'expression': {'expressionType': 0, 'columnPath': 'Symptoms'}},
                        'Status': {'expression': {'expressionType': 0, 'columnPath': 'Status.Name'}},
                        'Priority': {'expression': {'expressionType': 0, 'columnPath': 'Priority.Name'}},
                        'Category': {'expression': {'expressionType': 0, 'columnPath': 'Category.Name'}},
                        'RegisteredOn': {'expression': {'expressionType': 0, 'columnPath': 'RegisteredOn'}},
                        'ModifiedOn': {'expression': {'expressionType': 0, 'columnPath': 'ModifiedOn'}}
                    }
                }
            }
            
            result = self.make_authenticated_request('POST', 'SelectQuery', select_query, 'dataservice')
            
            if result.get('success') and result.get('rows'):
                return result['rows'][0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get case from Creatio: {e}")
            raise
    
    def add_case_comment(self, creatio_id, comment_data):
        """
        Add a comment to a case in Creatio
        """
        comment = {
            'CaseId': creatio_id,
            'Message': comment_data.get('content'),
            'CreatedBy': comment_data.get('author'),
            'CreatedOn': comment_data.get('created_at'),
        }
        
        try:
            result = self.make_authenticated_request('POST', 'CaseComment', comment)
            logger.info(f"Successfully added comment to case in Creatio: {creatio_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to add comment to case in Creatio: {e}")
            raise
    
    def sync_cases_from_creatio(self, last_sync_time=None):
        """
        Pull updated cases from Creatio
        """
        params = {}
        if last_sync_time:
            params['$filter'] = f"ModifiedOn gt {last_sync_time.isoformat()}"
        
        try:
            result = self.make_authenticated_request('GET', 'Case', params=params)
            return result.get('value', [])
        except Exception as e:
            logger.error(f"Failed to sync cases from Creatio: {e}")
            raise
    
    def _get_priority_id(self, priority_name):
        """
        Get Creatio priority ID by name
        """
        if not priority_name:
            return None
        
        try:
            # Use OData filter with startswith function
            filter_param = f"startswith(Name,'{priority_name}')"
            result = self.make_authenticated_request('GET', 'CasePriority', params={'$filter': filter_param})
            
            if result.get('value') and len(result['value']) > 0:
                return result['value'][0]['Id']
            else:
                logger.warning(f"Priority '{priority_name}' not found in Creatio")
                return None
        except Exception as e:
            logger.error(f"Failed to get priority ID: {e}")
            return None
    
    def _get_status_id(self, status_name):
        """
        Get Creatio status ID by name
        """
        if not status_name:
            return None
        
        try:
            # Use OData filter with startswith function
            filter_param = f"startswith(Name,'{status_name}')"
            result = self.make_authenticated_request('GET', 'CaseStatus', params={'$filter': filter_param})
            
            if result.get('value') and len(result['value']) > 0:
                return result['value'][0]['Id']
            else:
                logger.warning(f"Status '{status_name}' not found in Creatio")
                return None
        except Exception as e:
            logger.error(f"Failed to get status ID: {e}")
            return None
    
    def _get_category_id(self, category_name):
        """
        Get Creatio category ID by name
        """
        if not category_name:
            return None
        
        try:
            # Use OData filter with startswith function
            filter_param = f"startswith(Name,'{category_name}')"
            result = self.make_authenticated_request('GET', 'CaseCategory', params={'$filter': filter_param})
            
            if result.get('value') and len(result['value']) > 0:
                return result['value'][0]['Id']
            else:
                logger.warning(f"Category '{category_name}' not found in Creatio")
                return None
        except Exception as e:
            logger.error(f"Failed to get category ID: {e}")
            return None
    
    def test_connection(self):
        """
        Test the connection to Creatio
        """
        try:
            # First test OAuth token retrieval
            token = self.get_access_token()
            if not token:
                return False, "Failed to obtain OAuth access token"
            
            # Try to make a simple request to verify the connection
            result = self.make_authenticated_request('GET', 'Case', params={'$top': '1'})
            if result:
                return True, "Connection successful - OAuth token obtained and API accessible"
            else:
                return False, "OAuth token obtained but API request failed"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"