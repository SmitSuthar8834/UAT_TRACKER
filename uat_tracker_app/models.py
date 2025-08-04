from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Companies"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    is_admin = models.BooleanField(default=False)
    can_assign_cases = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.name}"

class CreatioConfig(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='creatio_config')
    base_url = models.URLField(help_text="Creatio instance URL (e.g., https://mycreatio.com)")
    identity_service_url = models.URLField(
        help_text="Identity service URL for OAuth (e.g., https://myidentityservice.com)",
        default="https://myidentityservice.com"
    )
    client_id = models.CharField(max_length=100, help_text="OAuth client ID")
    client_secret = models.CharField(max_length=100, help_text="OAuth client secret (encrypted)")
    # Keep legacy fields for backward compatibility
    username = models.CharField(max_length=100, blank=True, help_text="Legacy username (deprecated)")
    password = models.CharField(max_length=100, blank=True, help_text="Legacy password (deprecated)")
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Creatio Config - {self.company.name}"

class Priority(models.Model):
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Priorities"
        ordering = ['order']

class Status(models.Model):
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Statuses"
        ordering = ['order']

class Environment(models.Model):
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']

class CaseType(models.Model):
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']

class UATCase(models.Model):
    # Basic information
    case_number = models.CharField(max_length=20, unique=True, blank=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    reproduction_steps = models.TextField(blank=True, null=True)
    expected_result = models.TextField(blank=True, null=True)
    actual_result = models.TextField(blank=True, null=True)
    
    # Categorization (using dynamic lookups)
    priority = models.ForeignKey(Priority, on_delete=models.PROTECT)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    environment = models.ForeignKey(Environment, on_delete=models.PROTECT)
    case_type = models.ForeignKey(CaseType, on_delete=models.PROTECT)
    
    # Relationships
    requestor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_cases')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    
    # Creatio integration
    creatio_id = models.CharField(max_length=50, blank=True, null=True)
    sync_status = models.CharField(max_length=20, default='pending')  # pending, synced, failed
    sync_error = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.case_number:
            # Generate case number
            year = timezone.now().year
            count = UATCase.objects.filter(created_at__year=year).count() + 1
            self.case_number = f"UAT-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.case_number}: {self.subject}"
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("can_assign_cases", "Can assign cases to users"),
            ("can_view_all_company_cases", "Can view all company cases"),
        ]

class Note(models.Model):
    case = models.ForeignKey(UATCase, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Note by {self.author.username} on {self.case.subject}"

class Attachment(models.Model):
    case = models.ForeignKey(UATCase, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.filename} for {self.case.subject}"
# Dynamic Admin Panel Models
class DynamicPage(models.Model):
    """
    Model for creating dynamic pages through admin panel
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="URL slug for the page")
    content = models.TextField(help_text="HTML content for the page")
    is_active = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=True, help_text="Show in navigation menu")
    menu_order = models.IntegerField(default=0, help_text="Order in menu (lower numbers first)")
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class (e.g., fas fa-home)")
    requires_login = models.BooleanField(default=True, help_text="Require user login to access")
    allowed_roles = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Comma-separated roles (admin,manager,user) - leave blank for all"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['menu_order', 'title']

class DynamicWidget(models.Model):
    """
    Model for creating dashboard widgets through admin panel
    """
    WIDGET_TYPES = [
        ('stat', 'Statistics Card'),
        ('chart', 'Chart Widget'),
        ('table', 'Data Table'),
        ('custom', 'Custom HTML'),
    ]
    
    title = models.CharField(max_length=200)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES, default='stat')
    content = models.TextField(help_text="Widget content (HTML/JSON config)")
    css_classes = models.CharField(max_length=200, blank=True, help_text="Additional CSS classes")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    width = models.CharField(
        max_length=20, 
        default='col-md-6',
        help_text="Bootstrap column class (e.g., col-md-6, col-lg-4)"
    )
    allowed_roles = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Comma-separated roles - leave blank for all"
    )
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['order', 'title']

class DynamicMenuItem(models.Model):
    """
    Model for creating custom menu items
    """
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=200, help_text="URL or route name")
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    requires_login = models.BooleanField(default=True)
    allowed_roles = models.CharField(max_length=100, blank=True)
    open_in_new_tab = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['order', 'title']

class SystemSetting(models.Model):
    """
    Model for managing system settings through admin panel
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    setting_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('number', 'Number'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
            ('color', 'Color'),
            ('url', 'URL'),
        ],
        default='text'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"
    
    class Meta:
        ordering = ['key']