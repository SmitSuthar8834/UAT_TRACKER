from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Company, UATCase, Note, Attachment, UserProfile, 
    CreatioConfig, Priority, Status, Environment, CaseType
)

# Unregister the default User admin
admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('company', 'profile_image', 'phone', 'department', 'job_title', 'is_admin', 'can_assign_cases')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_company', 'get_job_title', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'profile__company', 'profile__is_admin')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_company(self, obj):
        try:
            return obj.profile.company.name
        except:
            return '-'
    get_company.short_description = 'Company'
    
    def get_job_title(self, obj):
        try:
            return obj.profile.job_title
        except:
            return '-'
    get_job_title.short_description = 'Job Title'

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_logo', 'employee_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'logo', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.logo.url)
        return '-'
    get_logo.short_description = 'Logo'
    
    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = 'Employees'

@admin.register(CreatioConfig)
class CreatioConfigAdmin(admin.ModelAdmin):
    list_display = ('company', 'base_url', 'client_id', 'is_active', 'last_sync')
    list_filter = ('is_active', 'last_sync')
    search_fields = ('company__name', 'base_url', 'client_id')
    readonly_fields = ('last_sync', 'created_at')
    
    fieldsets = (
        ('Company', {
            'fields': ('company',)
        }),
        ('OAuth 2.0 Configuration', {
            'fields': ('base_url', 'identity_service_url', 'client_id', 'client_secret', 'is_active'),
            'description': 'Configure OAuth 2.0 client credentials for Creatio integration'
        }),
        ('Legacy Configuration (Deprecated)', {
            'fields': ('username', 'password'),
            'classes': ('collapse',),
            'description': 'Legacy username/password authentication (deprecated, use OAuth instead)'
        }),
        ('Sync Information', {
            'fields': ('last_sync', 'created_at'),
            'classes': ('collapse',)
        })
    )

class LookupAdminMixin:
    list_display = ('name', 'value', 'get_color_display', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'value')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'name')
    
    def get_color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border-radius: 50%; display: inline-block;"></div>',
            obj.color
        )
    get_color_display.short_description = 'Color'

@admin.register(Priority)
class PriorityAdmin(LookupAdminMixin, admin.ModelAdmin):
    pass

@admin.register(Status)
class StatusAdmin(LookupAdminMixin, admin.ModelAdmin):
    pass

@admin.register(Environment)
class EnvironmentAdmin(LookupAdminMixin, admin.ModelAdmin):
    pass

@admin.register(CaseType)
class CaseTypeAdmin(LookupAdminMixin, admin.ModelAdmin):
    pass

class NoteInline(admin.TabularInline):
    model = Note
    extra = 0
    readonly_fields = ('author', 'created_at')
    fields = ('author', 'content', 'created_at')

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ('uploaded_by', 'uploaded_at')
    fields = ('file', 'filename', 'uploaded_by', 'uploaded_at')

@admin.register(UATCase)
class UATCaseAdmin(admin.ModelAdmin):
    list_display = (
        'case_number', 'subject', 'get_status_display', 'get_priority_display', 
        'environment', 'requestor', 'assigned_to', 'company', 'get_sync_status', 'created_at'
    )
    list_filter = (
        'status', 'priority', 'environment', 'case_type', 'company', 
        'sync_status', 'created_at', 'assigned_to'
    )
    search_fields = ('case_number', 'subject', 'description', 'requestor__username', 'requestor__first_name', 'requestor__last_name')
    readonly_fields = ('case_number', 'created_at', 'updated_at', 'last_synced')
    date_hierarchy = 'created_at'
    inlines = [NoteInline, AttachmentInline]
    
    fieldsets = (
        ('Case Information', {
            'fields': ('case_number', 'subject', 'description', 'reproduction_steps', 'expected_result', 'actual_result')
        }),
        ('Categorization', {
            'fields': ('priority', 'status', 'environment', 'case_type')
        }),
        ('Assignment', {
            'fields': ('requestor', 'company', 'assigned_to')
        }),
        ('Dates', {
            'fields': ('due_date', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Creatio Integration', {
            'fields': ('creatio_id', 'sync_status', 'sync_error', 'last_synced'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_status_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            obj.status.color,
            obj.status.name
        )
    get_status_display.short_description = 'Status'
    
    def get_priority_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            obj.priority.color,
            obj.priority.name
        )
    get_priority_display.short_description = 'Priority'
    
    def get_sync_status(self, obj):
        colors = {
            'pending': '#ffc107',
            'synced': '#28a745',
            'failed': '#dc3545'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.sync_status, '#6c757d'),
            obj.sync_status.title()
        )
    get_sync_status.short_description = 'Sync Status'

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('get_case_number', 'author', 'content_preview', 'created_at')
    list_filter = ('created_at', 'author', 'case__company')
    search_fields = ('content', 'case__subject', 'case__case_number', 'author__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def get_case_number(self, obj):
        return obj.case.case_number
    get_case_number.short_description = 'Case Number'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'get_case_number', 'uploaded_by', 'file_size', 'uploaded_at')
    list_filter = ('uploaded_at', 'uploaded_by', 'case__company')
    search_fields = ('filename', 'case__subject', 'case__case_number')
    readonly_fields = ('uploaded_at',)
    date_hierarchy = 'uploaded_at'
    
    def get_case_number(self, obj):
        return obj.case.case_number
    get_case_number.short_description = 'Case Number'
    
    def file_size(self, obj):
        try:
            size = obj.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except:
            return "Unknown"
    file_size.short_description = 'File Size'

# Customize admin site
admin.site.site_header = "UAT Tracker Administration"
admin.site.site_title = "UAT Tracker Admin"
admin.site.index_title = "Welcome to UAT Tracker Administration"

# Dynamic Admin Panel Configurations
from .models import DynamicPage, DynamicWidget, DynamicMenuItem, SystemSetting

@admin.register(DynamicPage)
class DynamicPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'show_in_menu', 'menu_order', 'requires_login', 'created_at')
    list_filter = ('is_active', 'show_in_menu', 'requires_login', 'created_at')
    search_fields = ('title', 'slug', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_active', 'show_in_menu', 'menu_order')
    
    fieldsets = (
        ('Page Information', {
            'fields': ('title', 'slug', 'content')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'show_in_menu', 'menu_order', 'icon')
        }),
        ('Access Control', {
            'fields': ('requires_login', 'allowed_roles'),
            'description': 'Control who can access this page'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DynamicWidget)
class DynamicWidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'widget_type', 'is_active', 'order', 'width')
    list_filter = ('widget_type', 'is_active')
    search_fields = ('title', 'content')
    list_editable = ('is_active', 'order')
    
    fieldsets = (
        ('Widget Information', {
            'fields': ('title', 'widget_type', 'content')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order', 'width', 'css_classes')
        }),
        ('Access Control', {
            'fields': ('allowed_roles',)
        })
    )

@admin.register(DynamicMenuItem)
class DynamicMenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'parent', 'order', 'is_active', 'requires_login')
    list_filter = ('is_active', 'requires_login', 'parent')
    search_fields = ('title', 'url')
    list_editable = ('order', 'is_active')
    
    fieldsets = (
        ('Menu Item', {
            'fields': ('title', 'url', 'icon', 'parent')
        }),
        ('Settings', {
            'fields': ('order', 'is_active', 'open_in_new_tab')
        }),
        ('Access Control', {
            'fields': ('requires_login', 'allowed_roles')
        })
    )

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_preview', 'setting_type', 'is_active', 'updated_at')
    list_filter = ('setting_type', 'is_active', 'updated_at')
    search_fields = ('key', 'value', 'description')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Setting Information', {
            'fields': ('key', 'value', 'description', 'setting_type')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value Preview'