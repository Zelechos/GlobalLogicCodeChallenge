#!/bin/bash

# API Usage Examples for Multi-Platform User Authentication System
# This script demonstrates all major API endpoints

BASE_URL="http://127.0.0.1:8000/api"

echo "=== Multi-Platform User Authentication API Examples ==="
echo

# Function to make API calls with pretty output
call_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4
    
    if [ -n "$token" ]; then
        headers="-H \"Authorization: Bearer $token\" -H \"Content-Type: application/json\""
    else
        headers="-H \"Content-Type: application/json\""
    fi
    
    if [ -n "$data" ]; then
        curl -s -X $method "$BASE_URL$endpoint" $headers -d "$data" | python3 -m json.tool
    else
        curl -s -X $method "$BASE_URL$endpoint" $headers | python3 -m json.tool
    fi
    echo
    echo "---"
    echo
}

echo "1. Creating Test Platforms"
echo "========================"

# Create Platform A
PLATFORM_A_DATA='{
    "name": "Platform A",
    "description": "First test platform for demonstration"
}'
call_api "POST" "/auth/platforms/register/" "$PLATFORM_A_DATA"

# Create Platform B
PLATFORM_B_DATA='{
    "name": "Platform B",
    "description": "Second test platform with different rules"
}'
call_api "POST" "/auth/platforms/register/" "$PLATFORM_B_DATA"

echo "2. Registering Users on Platforms"
echo "==============================="

# Register user on Platform A
USER_A_DATA='{
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "platform_name": "Platform A",
    "first_name": "John",
    "last_name": "Doe"
}'
call_api "POST" "/auth/register/" "$USER_A_DATA"

# Register same user on Platform B
USER_B_DATA='{
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "platform_name": "Platform B",
    "first_name": "John",
    "last_name": "Doe"
}'
call_api "POST" "/auth/register/" "$USER_B_DATA"

# Register second user on Platform A
USER_C_DATA='{
    "email": "jane.smith@example.com",
    "password": "AnotherPass456!",
    "platform_name": "Platform A",
    "first_name": "Jane",
    "last_name": "Smith"
}'
call_api "POST" "/auth/register/" "$USER_C_DATA"

echo "3. User Login (Platform A)"
echo "========================="

# Login John on Platform A
LOGIN_A_DATA='{
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "platform_name": "Platform A"
}'
LOGIN_RESPONSE=$(call_api "POST" "/auth/login/" "$LOGIN_A_DATA")
TOKEN_A=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")
USER_PLATFORM_ID_A=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['user_platform_id'])")

echo "Token for John on Platform A: $TOKEN_A"
echo

echo "4. User Login (Platform B)"
echo "========================="

# Login John on Platform B
LOGIN_B_DATA='{
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "platform_name": "Platform B"
}'
LOGIN_RESPONSE_B=$(call_api "POST" "/auth/login/" "$LOGIN_B_DATA")
TOKEN_B=$(echo $LOGIN_RESPONSE_B | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")
USER_PLATFORM_ID_B=$(echo $LOGIN_RESPONSE_B | python3 -c "import sys, json; print(json.load(sys.stdin)['user_platform_id'])")

echo "Token for John on Platform B: $TOKEN_B"
echo

echo "5. Getting Platform Information"
echo "============================="

call_api "GET" "/auth/platform/info/" "" "$TOKEN_A"

echo "6. Creating Devices (Platform A)"
echo "==============================="

# Create devices for John on Platform A
DEVICE_1_DATA='{
    "name": "iPhone 13 Pro",
    "ip_address": "192.168.1.100",
    "device_type": "mobile",
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"
}'
call_api "POST" "/devices/" "$DEVICE_1_DATA" "$TOKEN_A"

DEVICE_2_DATA='{
    "name": "MacBook Pro 16\"",
    "ip_address": "192.168.1.101",
    "device_type": "desktop",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}'
call_api "POST" "/devices/" "$DEVICE_2_DATA" "$TOKEN_A"

DEVICE_3_DATA='{
    "name": "iPad Air",
    "ip_address": "192.168.1.102",
    "device_type": "tablet",
    "user_agent": "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X)"
}'
call_api "POST" "/devices/" "$DEVICE_3_DATA" "$TOKEN_A"

echo "7. Listing Devices (Platform A)"
echo "=============================="

call_api "GET" "/devices/" "" "$TOKEN_A"

echo "8. Device Statistics (Platform A)"
echo "================================"

call_api "GET" "/devices/statistics/" "" "$TOKEN_A"

echo "9. Creating Devices (Platform B)"
echo "==============================="

# Create devices for John on Platform B (different platform, same user)
DEVICE_4_DATA='{
    "name": "Work Laptop",
    "ip_address": "10.0.0.50",
    "device_type": "desktop",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}'
call_api "POST" "/devices/" "$DEVICE_4_DATA" "$TOKEN_B"

echo "10. Listing Devices (Platform B)"
echo "==============================="

call_api "GET" "/devices/" "" "$TOKEN_B"

echo "11. Updating Device Information"
echo "============================="

# Update device name and status
UPDATE_DATA='{
    "name": "iPhone 13 Pro (Updated)",
    "is_active": false
}'
call_api "PATCH" "/devices/1/" "$UPDATE_DATA" "$TOKEN_A"

echo "12. Getting Device Details"
echo "========================"

call_api "GET" "/devices/1/" "" "$TOKEN_A"

echo "13. Updating Last Seen Timestamp"
echo "=============================="

call_api "POST" "/devices/1/update-last-seen/" "" "$TOKEN_A"

echo "14. Listing Notifications"
echo "======================"

call_api "GET" "/notifications/" "" "$TOKEN_A"

echo "15. Getting Unread Count"
echo "======================"

call_api "GET" "/notifications/unread-count/" "" "$TOKEN_A"

echo "16. Marking Notification as Read"
echo "==============================="

call_api "POST" "/notifications/1/mark-read/" "" "$TOKEN_A"

echo "17. User Profile Information"
echo "=========================="

call_api "GET" "/auth/profile/" "" "$TOKEN_A"

echo "18. User's Platforms"
echo "==================="

call_api "GET" "/auth/platforms/my/" "" "$TOKEN_A"

echo "19. Testing Device Limits"
echo "========================"

# Try to add more devices than allowed (default is 5)
echo "Adding more devices to test limits..."

for i in {5..7}; do
    DEVICE_LIMIT_DATA="{
        \"name\": \"Test Device $i\",
        \"ip_address\": \"192.168.1.$((100+i))\",
        \"device_type\": \"other\"
    }"
    echo "Attempting to create Test Device $i..."
    call_api "POST" "/devices/" "$DEVICE_LIMIT_DATA" "$TOKEN_A"
done

echo "20. Filtering and Searching Devices"
echo "================================="

echo "Filtering by device_type=mobile:"
call_api "GET" "/devices/?device_type=mobile" "" "$TOKEN_A"

echo "Filtering by is_active=false:"
call_api "GET" "/devices/?is_active=false" "" "$TOKEN_A"

echo "Searching for 'MacBook':"
call_api "GET" "/devices/?search=MacBook" "" "$TOKEN_A"

echo "21. Logout"
echo "========="

LOGOUT_DATA="{\"refresh_token\": \"placeholder_refresh_token\"}"
call_api "POST" "/auth/logout/" "$LOGOUT_DATA" "$TOKEN_A"

echo "=== API Examples Complete ==="
echo "All major endpoints have been demonstrated."
echo "Check the responses above to verify the system is working correctly."
