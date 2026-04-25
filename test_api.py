#!/usr/bin/env python3
"""
API Testing Script for Multi-Platform User Authentication System
This script demonstrates all major API endpoints with proper error handling
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class APITester:
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api"):
        self.base_url = base_url
        self.tokens = {}
        self.user_platform_ids = {}
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     token: Optional[str] = None, print_response: bool = True) -> Dict[str, Any]:
        """Make HTTP request with proper headers and error handling."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if print_response:
                print(f"\n{method.upper()} {endpoint}")
                print(f"Status: {response.status_code}")
                if response.content:
                    print(f"Response: {json.dumps(response.json(), indent=2)}")
                print("-" * 50)
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {method.upper()} {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {}
    
    def setup_platforms(self):
        """Create test platforms."""
        print("=== Setting up Test Platforms ===")
        
        platforms = [
            {
                "name": "Platform A",
                "description": "First test platform for demonstration"
            },
            {
                "name": "Platform B", 
                "description": "Second test platform with different rules"
            },
            {
                "name": "Platform C",
                "description": "Third platform with strict device limits"
            }
        ]
        
        for platform in platforms:
            self._make_request("POST", "/auth/platforms/register/", platform)
    
    def setup_users(self):
        """Create test users on different platforms."""
        print("\n=== Setting up Test Users ===")
        
        users = [
            {
                "email": "john.doe@example.com",
                "password": "SecurePass123!",
                "platform_name": "Platform A",
                "first_name": "John",
                "last_name": "Doe"
            },
            {
                "email": "john.doe@example.com",
                "password": "SecurePass123!",
                "platform_name": "Platform B",
                "first_name": "John",
                "last_name": "Doe"
            },
            {
                "email": "jane.smith@example.com",
                "password": "AnotherPass456!",
                "platform_name": "Platform A",
                "first_name": "Jane",
                "last_name": "Smith"
            },
            {
                "email": "admin@example.com",
                "password": "AdminPass789!",
                "platform_name": "Platform C",
                "first_name": "Admin",
                "last_name": "User"
            }
        ]
        
        for user in users:
            self._make_request("POST", "/auth/register/", user)
    
    def login_users(self):
        """Login users and store tokens."""
        print("\n=== Logging in Users ===")
        
        logins = [
            ("john.doe@example.com", "SecurePass123!", "Platform A", "john_a"),
            ("john.doe@example.com", "SecurePass123!", "Platform B", "john_b"),
            ("jane.smith@example.com", "AnotherPass456!", "Platform A", "jane_a"),
            ("admin@example.com", "AdminPass789!", "Platform C", "admin_c")
        ]
        
        for email, password, platform, key in logins:
            login_data = {
                "email": email,
                "password": password,
                "platform_name": platform
            }
            
            response = self._make_request("POST", "/auth/login/", login_data)
            if response and "access" in response:
                self.tokens[key] = response["access"]
                self.user_platform_ids[key] = response.get("user_platform_id")
                print(f"Logged in {email} on {platform} - Token stored as '{key}'")
    
    def test_platform_info(self):
        """Test platform information endpoint."""
        print("\n=== Testing Platform Information ===")
        
        for key, token in self.tokens.items():
            print(f"\nPlatform info for {key}:")
            self._make_request("GET", "/auth/platform/info/", token=token)
    
    def test_device_management(self):
        """Test device creation, listing, and management."""
        print("\n=== Testing Device Management ===")
        
        # Test devices for different users
        device_sets = {
            "john_a": [
                {"name": "iPhone 13 Pro", "ip_address": "192.168.1.100", "device_type": "mobile"},
                {"name": "MacBook Pro 16\"", "ip_address": "192.168.1.101", "device_type": "desktop"},
                {"name": "iPad Air", "ip_address": "192.168.1.102", "device_type": "tablet"}
            ],
            "john_b": [
                {"name": "Work Laptop", "ip_address": "10.0.0.50", "device_type": "desktop"},
                {"name": "Android Phone", "ip_address": "10.0.0.51", "device_type": "mobile"}
            ],
            "jane_a": [
                {"name": "Surface Pro", "ip_address": "192.168.1.200", "device_type": "tablet"}
            ]
        }
        
        for user_key, devices in device_sets.items():
            if user_key not in self.tokens:
                continue
                
            print(f"\nCreating devices for {user_key}:")
            token = self.tokens[user_key]
            
            for device in devices:
                self._make_request("POST", "/devices/", device, token)
            
            # List devices
            print(f"\nDevices for {user_key}:")
            self._make_request("GET", "/devices/", token=token)
    
    def test_device_statistics(self):
        """Test device statistics endpoint."""
        print("\n=== Testing Device Statistics ===")
        
        for key, token in self.tokens.items():
            print(f"\nDevice statistics for {key}:")
            self._make_request("GET", "/devices/statistics/", token=token)
    
    def test_device_operations(self):
        """Test device update, delete, and filtering."""
        print("\n=== Testing Device Operations ===")
        
        if "john_a" not in self.tokens:
            return
        
        token = self.tokens["john_a"]
        
        # Update first device
        update_data = {
            "name": "iPhone 13 Pro (Updated)",
            "is_active": False
        }
        print("\nUpdating device 1:")
        self._make_request("PATCH", "/devices/1/", update_data, token)
        
        # Get device details
        print("\nGetting device 1 details:")
        self._make_request("GET", "/devices/1/", token=token)
        
        # Update last seen
        print("\nUpdating last seen for device 1:")
        self._make_request("POST", "/devices/1/update-last-seen/", token=token)
        
        # Test filtering
        print("\nFiltering devices by device_type=mobile:")
        self._make_request("GET", "/devices/?device_type=mobile", token=token)
        
        print("\nFiltering devices by is_active=false:")
        self._make_request("GET", "/devices/?is_active=false", token=token)
        
        print("\nSearching devices for 'MacBook':")
        self._make_request("GET", "/devices/?search=MacBook", token=token)
    
    def test_notifications(self):
        """Test notification endpoints."""
        print("\n=== Testing Notifications ===")
        
        for key, token in self.tokens.items():
            print(f"\nNotifications for {key}:")
            self._make_request("GET", "/notifications/", token=token)
            
            print(f"\nUnread count for {key}:")
            self._make_request("GET", "/notifications/unread-count/", token=token)
    
    def test_user_profiles(self):
        """Test user profile and platform endpoints."""
        print("\n=== Testing User Profiles ===")
        
        for key, token in self.tokens.items():
            print(f"\nProfile for {key}:")
            self._make_request("GET", "/auth/profile/", token=token)
            
            print(f"\nPlatforms for {key}:")
            self._make_request("GET", "/auth/platforms/my/", token=token)
    
    def test_device_limits(self):
        """Test device limit enforcement."""
        print("\n=== Testing Device Limits ===")
        
        if "jane_a" not in self.tokens:
            return
        
        token = self.tokens["jane_a"]
        
        # Try to add more devices than allowed
        print("Attempting to add devices beyond limit:")
        for i in range(5, 8):
            device_data = {
                "name": f"Test Device {i}",
                "ip_address": f"192.168.1.{200+i}",
                "device_type": "other"
            }
            print(f"\nAttempting to create Test Device {i}:")
            self._make_request("POST", "/devices/", device_data, token)
    
    def test_logout(self):
        """Test logout functionality."""
        print("\n=== Testing Logout ===")
        
        for key, token in self.tokens.items():
            logout_data = {"refresh_token": "dummy_refresh_token"}
            print(f"\nLogging out {key}:")
            self._make_request("POST", "/auth/logout/", logout_data, token)
    
    def run_all_tests(self):
        """Run all API tests in sequence."""
        print("Starting Comprehensive API Testing")
        print("=" * 50)
        
        try:
            self.setup_platforms()
            time.sleep(1)
            
            self.setup_users()
            time.sleep(1)
            
            self.login_users()
            time.sleep(1)
            
            self.test_platform_info()
            time.sleep(1)
            
            self.test_device_management()
            time.sleep(1)
            
            self.test_device_statistics()
            time.sleep(1)
            
            self.test_device_operations()
            time.sleep(1)
            
            self.test_notifications()
            time.sleep(1)
            
            self.test_user_profiles()
            time.sleep(1)
            
            self.test_device_limits()
            time.sleep(1)
            
            self.test_logout()
            
            print("\n" + "=" * 50)
            print("API Testing Complete!")
            print("All major endpoints have been tested.")
            print("Check the responses above to verify system functionality.")
            
        except Exception as e:
            print(f"Error during testing: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function to run API tests."""
    import sys
    
    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api"
    
    print(f"Testing API at: {base_url}")
    print("Make sure the Django development server is running!")
    print("Run: ./manage.py runserver")
    print()
    
    tester = APITester(base_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
