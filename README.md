# Backend API Technical Test - Django REST Framework

This project implements a multi-platform user authentication and device management system using Django and Django REST Framework with JWT authentication.

## Features

- **Multi-Platform Support**: Users can register on multiple platforms using the same email
- **JWT Authentication**: Platform-specific token-based authentication
- **Device Management**: Users can manage devices per platform with configurable limits
- **Configurable Business Rules**: Each platform can have custom business rules
- **Notification System**: Extensible notification system with multiple channels
- **Comprehensive Testing**: Full test coverage for all functionality

## Installation and Setup

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd SolvoGlobalCodeChallenge
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**:
   ```bash
   ./manage.py makemigrations
   ./manage.py migrate
   ```

5. **Create a superuser** (optional):
   ```bash
   ./manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   ./manage.py runserver
   ```

The API will be available at `http://127.0.0.1:8000/`

## API Endpoints

### Authentication Endpoints

#### Register a New Platform
```http
POST /api/auth/platforms/register/
Content-Type: application/json

{
    "name": "Platform A",
    "description": "Description of Platform A"
}
```

#### Register a User on a Platform
```http
POST /api/auth/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword123",
    "platform_name": "Platform A",
    "first_name": "John",
    "last_name": "Doe"
}
```

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword123",
    "platform_name": "Platform A"
}
```

**Response**:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    },
    "platform": {
        "id": 1,
        "name": "Platform A",
        "business_rules": {
            "max_devices": 5,
            "allow_inactive_login": true,
            "device_name_required": true,
            "ip_validation_enabled": false,
            "session_timeout_hours": 24
        }
    },
    "user_platform_id": 1
}
```

#### Logout
```http
POST /api/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "refresh_token": "<refresh_token>"
}
```

### Device Management Endpoints

#### List Devices
```http
GET /api/devices/
Authorization: Bearer <access_token>
```

#### Create a Device
```http
POST /api/devices/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "iPhone 13",
    "ip_address": "192.168.1.100",
    "device_type": "mobile",
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"
}
```

#### Get Device Details
```http
GET /api/devices/{device_id}/
Authorization: Bearer <access_token>
```

#### Update Device
```http
PATCH /api/devices/{device_id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Updated Device Name",
    "is_active": false
}
```

#### Delete Device
```http
DELETE /api/devices/{device_id}/
Authorization: Bearer <access_token>
```

#### Get Device Statistics
```http
GET /api/devices/statistics/
Authorization: Bearer <access_token>
```

### Notification Endpoints

#### List Notifications
```http
GET /api/notifications/
Authorization: Bearer <access_token>
```

#### Mark Notification as Read
```http
POST /api/notifications/{notification_id}/mark-read/
Authorization: Bearer <access_token>
```

#### Get Unread Count
```http
GET /api/notifications/unread-count/
Authorization: Bearer <access_token>
```

## Creating Test Data

### 1. Create Test Platforms

```bash
curl -X POST http://127.0.0.1:8000/api/auth/platforms/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Platform A",
    "description": "First test platform"
  }'

curl -X POST http://127.0.0.1:8000/api/auth/platforms/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Platform B",
    "description": "Second test platform"
  }'
```

### 2. Register Test Users

```bash
# Register user on Platform A
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpass123",
    "platform_name": "Platform A",
    "first_name": "Test",
    "last_name": "User"
  }'

# Register same user on Platform B
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpass123",
    "platform_name": "Platform B",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 3. Obtain JWT Token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpass123",
    "platform_name": "Platform A"
  }'
```

### 4. Create Test Devices

```bash
# Replace <access_token> with the token from step 3
curl -X POST http://127.0.0.1:8000/api/devices/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 13",
    "ip_address": "192.168.1.100",
    "device_type": "mobile"
  }'

curl -X POST http://127.0.0.1:8000/api/devices/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MacBook Pro",
    "ip_address": "192.168.1.101",
    "device_type": "desktop"
  }'
```

## Business Rules Configuration

Each platform can have configurable business rules stored in the `business_rules` JSON field:

### Default Rules:
- `max_devices`: 5 (Maximum number of devices per user)
- `allow_inactive_login`: true (Allow inactive users to login)
- `device_name_required`: true (Require device name)
- `ip_validation_enabled`: false (Enable IP address validation)
- `session_timeout_hours`: 24 (Session timeout in hours)

### Updating Platform Rules:

```bash
# Get platform info first to see current rules
curl -X GET http://127.0.0.1:8000/api/auth/platform/info/ \
  -H "Authorization: Bearer <access_token>"

# Update rules via Django admin or direct database access
# Example: Set max_devices to 10 for Platform A
```

## Testing

### Run All Tests
```bash
./manage.py test
```

### Run Specific App Tests
```bash
./manage.py test accounts
./manage.py test devices
./manage.py test notifications
```

### Run with Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Project Structure

```
backend_api/
├── accounts/           # User authentication and platform management
│   ├── models.py       # User, Platform, UserPlatform models
│   ├── views.py        # Authentication views
│   ├── serializers.py  # Authentication serializers
│   └── tests.py       # Authentication tests
├── devices/           # Device management
│   ├── models.py       # Device model
│   ├── views.py        # Device management views
│   ├── serializers.py  # Device serializers
│   └── tests.py       # Device tests
├── notifications/     # Notification system
│   ├── models.py       # Notification models
│   ├── services.py     # Notification service
│   ├── views.py        # Notification views
│   ├── serializers.py  # Notification serializers
│   └── tests.py       # Notification tests
└── backend_api/       # Django project settings
    ├── settings.py     # Project configuration
    └── urls.py         # Main URL configuration
```

## Technology Stack

- **Backend**: Django 4.2.7
- **API Framework**: Django REST Framework 3.14.0
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: SQLite (development)
- **Task Queue**: Celery with Redis (configured but optional)
- **Testing**: Django's built-in testing framework

## Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Docker Support (Optional)

A `docker-compose.yml` file can be added for containerized deployment:

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  celery:
    build: .
    command: celery -A backend_api worker -l info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## Common Issues and Solutions

### 1. Migration Issues
If you encounter migration issues, try:
```bash
./manage.py makemigrations accounts devices notifications
./manage.py migrate
```

### 2. Token Not Found
Ensure you're including the correct Authorization header:
```http
Authorization: Bearer <your_access_token>
```

### 3. Platform Information Missing
Make sure you're using the custom JWT authentication that includes platform information in the token payload.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is for technical evaluation purposes only.
