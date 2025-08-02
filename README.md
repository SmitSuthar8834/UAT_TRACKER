# Modern UAT Tracker 2025

A cutting-edge UAT (User Acceptance Testing) case management system with modern Django backend, sleek 2025 UI design, and seamless Creatio CRM integration.

## 🚀 Features

### 🎨 Modern 2025 Design
- **Sleek Interface**: Clean, modern design with glassmorphism effects
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Dark/Light Theme**: Automatic theme adaptation
- **Smooth Animations**: Fluid transitions and micro-interactions

### 👥 Multi-Company Support
- **Company Isolation**: Complete data separation between companies
- **Role-Based Access**: Admin, Manager, and User roles with different permissions
- **Employee Management**: Add and manage employees within companies

### 📊 Advanced Dashboard
- **Analytics View**: Comprehensive case statistics and trends
- **Status Tracking**: New, In Progress, Resolved, Closed, Reopened, Cancelled
- **Priority Management**: Low, Medium, High, Critical with color coding
- **Recent Activity**: Real-time updates on case changes

### 👤 Profile Management
- **User Profiles**: Complete profile management with image upload
- **Company Branding**: Company logos and branding support
- **Department Tracking**: Organize users by departments and job titles

### 🔧 Admin Panel Features
- **Modern Admin Theme**: Beautiful Jazzmin-powered admin interface
- **Configurable Lookups**: Manage priorities, statuses, environments, and case types
- **User Management**: Create and manage users with company assignments
- **Creatio Configuration**: Configure Creatio integration per company

### 🔄 Creatio Integration
- **Admin Panel Configuration**: No more environment files - configure through admin
- **Automatic Sync**: Real-time synchronization with Creatio CRM
- **Manual Sync**: On-demand synchronization with status tracking
- **Error Handling**: Robust error handling with retry mechanisms

## 📁 Project Structure

```
uat_tracker/
├── uat_tracker/                    # Django project settings
│   ├── settings.py                # Main settings with Jazzmin theme
│   ├── urls.py                    # URL routing
│   └── wsgi.py                    # WSGI configuration
├── uat_tracker_app/               # Main Django app
│   ├── models.py                  # Enhanced models with lookups
│   ├── views.py                   # Modern API views
│   ├── admin.py                   # Beautiful admin interface
│   ├── creatio_service.py         # Configurable Creatio service
│   └── management/commands/       # Management commands
├── templates/                     # HTML templates
│   └── modern_uat_tracker.html   # Modern 2025 frontend
├── static/                        # Static files (auto-created)
├── media/                         # Media files (auto-created)
├── requirements.txt               # Python dependencies
├── setup.py                      # Enhanced setup script
└── README.md                     # This file
```

## 🛠️ Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Database and Demo Data

```bash
# Run the enhanced setup script
python setup.py
```

This will:
- Create database tables with migrations
- Set up lookup data (priorities, statuses, environments, case types)
- Create superuser (admin/admin123)
- Create demo companies with branding
- Create test users with profiles

### 3. Start the Server

```bash
python manage.py runserver
```

Access the application at: http://127.0.0.1:8000/

## 🔐 Login Credentials

- **Admin**: admin / admin123 (Full system access)
- **Manager**: manager / manager123 (Can assign cases)
- **Test User**: testuser / test123 (Regular user)

## 🎯 Key Features Walkthrough

### 🏠 Home Dashboard
- **Analytics Cards**: Total, Open, High Priority, Resolved cases
- **Status Distribution**: Visual breakdown of case statuses
- **Recent Activity**: Latest case updates and changes
- **Quick Actions**: Fast access to common tasks

### 📋 Case Management
- **Smart Case Numbers**: Auto-generated case numbers (UAT-2025-0001)
- **Rich Case Details**: Subject, description, reproduction steps, expected/actual results
- **Dynamic Assignments**: Assign cases to team members
- **File Attachments**: Upload and manage case attachments
- **Notes System**: Add comments and track case history

### 👤 Profile Management
- **Profile Images**: Upload and manage profile pictures
- **Personal Information**: Name, email, phone, department, job title
- **Company Association**: Automatic company assignment and branding
- **Permission Management**: Role-based access control

### ⚙️ Admin Panel
- **Modern Theme**: Beautiful Jazzmin-powered interface
- **Company Management**: Add companies with logos and descriptions
- **User Management**: Create users with profiles and permissions
- **Lookup Management**: Configure priorities, statuses, environments, case types
- **Creatio Configuration**: Set up Creatio integration per company

## 🔄 Creatio Integration

### Configuration (Admin Panel)
1. Go to Admin Panel → Creatio Configs
2. Add new configuration for your company
3. Enter Creatio instance URL, credentials, and OAuth details
4. Test connection and activate

### Features
- **Per-Company Configuration**: Each company can have its own Creatio setup
- **Automatic Sync**: Cases sync automatically on create/update
- **Manual Sync**: Use the sync button for on-demand synchronization
- **Status Tracking**: Visual indicators for sync status
- **Error Handling**: Failed syncs are marked and can be retried

## 🌐 API Endpoints

### Authentication
- `POST /api/login/` - User login with company selection
- `POST /api/logout/` - User logout

### Lookups & Data
- `GET /api/lookups/` - Get all dropdown data
- `GET /api/companies/` - Get companies list
- `GET /api/company/employees/` - Get company employees

### Cases
- `GET /api/cases/` - Get user cases (filtered by permissions)
- `POST /api/cases/create/` - Create new case
- `GET /api/cases/{id}/` - Get case details
- `POST /api/cases/{id}/update-field/` - Update case field
- `POST /api/cases/{id}/add-note/` - Add note to case
- `POST /api/cases/{id}/assign/` - Assign case to user
- `POST /api/cases/{id}/upload/` - Upload attachment

### Profile
- `GET /api/profile/` - Get user profile
- `POST /api/profile/update/` - Update profile
- `POST /api/profile/upload-image/` - Upload profile image

### Dashboard
- `GET /api/dashboard-stats/` - Get enhanced dashboard statistics

### Creatio
- `POST /api/sync-creatio/` - Manual Creatio synchronization

## 🗄️ Database Models

### Core Models
- **Company**: Multi-tenant company management with branding
- **UserProfile**: Extended user profiles with company association
- **UATCase**: Enhanced case model with auto-generated numbers
- **Note**: Case comments and history tracking
- **Attachment**: File attachment management

### Lookup Models
- **Priority**: Configurable priority levels with colors
- **Status**: Configurable status types with colors
- **Environment**: Configurable environment types
- **CaseType**: Configurable case categories

### Integration Models
- **CreatioConfig**: Per-company Creatio configuration

## 🔧 Management Commands

### Creatio Sync
```bash
# Test connection
python manage.py sync_creatio --test-connection

# Full sync (all pending cases)
python manage.py sync_creatio --full-sync

# Incremental sync (recent changes)
python manage.py sync_creatio
```

## 🎨 Customization

### Adding New Lookup Types
1. Create model in `models.py`
2. Add admin configuration in `admin.py`
3. Update API endpoints in `views.py`
4. Add frontend handling in template

### Customizing UI Theme
- Modify CSS variables in the template
- Update Jazzmin settings in `settings.py`
- Add custom CSS/JS files

### Adding New Case Fields
1. Update UATCase model
2. Create migration
3. Update admin interface
4. Update API serialization
5. Update frontend forms

## 🚨 Troubleshooting

### Common Issues

1. **Migration Errors**
   ```bash
   python manage.py makemigrations
   python manage.py migrate --fake-initial
   ```

2. **Static Files Not Loading**
   ```bash
   python manage.py collectstatic
   ```

3. **Creatio Connection Issues**
   - Check configuration in admin panel
   - Verify OAuth credentials
   - Test connection using management command

4. **Permission Errors**
   - Verify user has proper company assignment
   - Check role permissions in admin panel

### Debug Mode
Enable debug mode in `settings.py`:
```python
DEBUG = True
```

## 🔒 Security Features

- **Company Data Isolation**: Complete separation between companies
- **Role-Based Access Control**: Different permissions for different roles
- **Secure File Uploads**: Validated file uploads with size limits
- **CSRF Protection**: Built-in Django CSRF protection
- **SQL Injection Protection**: Django ORM prevents SQL injection

## 📱 Mobile Responsiveness

- **Responsive Design**: Works on all screen sizes
- **Touch-Friendly**: Optimized for touch interactions
- **Mobile Navigation**: Collapsible sidebar for mobile
- **Fast Loading**: Optimized for mobile networks

## 🚀 Performance Features

- **Database Optimization**: Efficient queries with select_related
- **Caching**: Built-in Django caching support
- **Pagination**: API pagination for large datasets
- **Lazy Loading**: Images and content loaded on demand

## 📈 Future Enhancements

- **Real-time Notifications**: WebSocket-based notifications
- **Advanced Analytics**: Charts and graphs for case trends
- **Email Integration**: Email notifications for case updates
- **API Documentation**: Swagger/OpenAPI documentation
- **Mobile App**: React Native mobile application

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django framework for the robust backend
- Jazzmin for the beautiful admin interface
- Inter font family for modern typography
- Font Awesome for the icon set

---

**Built with ❤️ for modern UAT management in 2025**