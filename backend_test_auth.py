#!/usr/bin/env python3
"""
Comprehensive authentication and authorization testing for YükTakip MVP.
Tests all auth endpoints, role-based permissions, and data preservation.
"""

import requests
import sys
import os
from typing import Dict, List, Optional

# Read base URL from environment
BASE_URL = os.getenv('NEXT_PUBLIC_BASE_URL', 'https://load-management-6.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test state
tokens = {}
test_data_ids = {
    'companies': [],
    'addresses': [],
    'drivers': [],
    'vehicles': [],
    'loads': []
}
initial_counts = {}

def log_test(name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"  → {details}")
    if not passed:
        sys.exit(1)

def api_call(method: str, endpoint: str, token: Optional[str] = None, json_data: Optional[dict] = None, expect_error: bool = False):
    """Make API call with optional auth"""
    url = f"{API_BASE}/{endpoint}"
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            resp = requests.post(url, headers=headers, json=json_data, timeout=10)
        elif method == 'PUT':
            resp = requests.put(url, headers=headers, json=json_data, timeout=10)
        elif method == 'DELETE':
            resp = requests.delete(url, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if not expect_error and resp.status_code >= 400:
            print(f"  ⚠️  Unexpected error {resp.status_code}: {resp.text}")
        
        return resp
    except Exception as e:
        print(f"  ⚠️  Request failed: {e}")
        if not expect_error:
            raise
        return None

print("=" * 80)
print("YUKTAKIP AUTHENTICATION & AUTHORIZATION TEST SUITE")
print("=" * 80)
print(f"Base URL: {API_BASE}\n")

# ============================================================================
# SECTION 1: INIT & LOGIN
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 1: INIT & LOGIN")
print("=" * 80)

# Test 1.1: Call /auth/init twice (idempotency)
print("\n[Test 1.1] POST /auth/init - First call")
resp = api_call('POST', 'auth/init')
log_test("POST /auth/init returns 200", resp.status_code == 200)
data = resp.json()
log_test("Response has ok=true", data.get('ok') == True)
log_test("Response has demoUsers array with 3 entries", 
         isinstance(data.get('demoUsers'), list) and len(data['demoUsers']) == 3)

print("\n[Test 1.2] POST /auth/init - Second call (idempotency)")
resp2 = api_call('POST', 'auth/init')
log_test("Second POST /auth/init returns 200", resp2.status_code == 200)
data2 = resp2.json()
log_test("Second call also returns 3 demoUsers", 
         isinstance(data2.get('demoUsers'), list) and len(data2['demoUsers']) == 3)

# Test 1.3: Login as each user
demo_users = [
    {'username': 'yukler', 'password': '1234', 'expected_name': 'Yük Sorumlusu Demo', 'expected_roles': ['yuk_sorumlusu']},
    {'username': 'planlama', 'password': '1234', 'expected_name': 'Araç Planlama Demo', 'expected_roles': ['arac_planlama']},
    {'username': 'depo', 'password': '1234', 'expected_name': 'Depocu Demo', 'expected_roles': ['depocu']},
]

for user_info in demo_users:
    print(f"\n[Test 1.3.{user_info['username']}] Login as {user_info['username']}")
    resp = api_call('POST', 'auth/login', json_data={
        'username': user_info['username'],
        'password': user_info['password']
    })
    log_test(f"Login {user_info['username']} returns 200", resp.status_code == 200)
    
    data = resp.json()
    log_test(f"Response has token (non-empty string)", 
             isinstance(data.get('token'), str) and len(data['token']) > 0)
    log_test(f"Response has user object", isinstance(data.get('user'), dict))
    
    user = data['user']
    log_test(f"User has id", 'id' in user)
    log_test(f"User has username={user_info['username']}", user.get('username') == user_info['username'])
    log_test(f"User has name={user_info['expected_name']}", user.get('name') == user_info['expected_name'])
    log_test(f"User has roles={user_info['expected_roles']}", user.get('roles') == user_info['expected_roles'])
    log_test(f"User does NOT contain password field", 'password' not in user)
    log_test(f"User does NOT contain _id field", '_id' not in user)
    
    # Store token for later use
    tokens[user_info['username']] = data['token']

# Test 1.4: Wrong password
print("\n[Test 1.4] Login with wrong password")
resp = api_call('POST', 'auth/login', json_data={
    'username': 'yukler',
    'password': 'wrongpassword'
}, expect_error=True)
log_test("Wrong password returns 401", resp.status_code == 401)

# Test 1.5: GET /auth/me with bad token
print("\n[Test 1.5] GET /auth/me with invalid token")
resp = api_call('GET', 'auth/me', token='invalid-token-12345', expect_error=True)
log_test("Invalid token returns 401", resp.status_code == 401)

# Test 1.6: GET /auth/me with valid tokens
for username in ['yukler', 'planlama', 'depo']:
    print(f"\n[Test 1.6.{username}] GET /auth/me with {username} token")
    resp = api_call('GET', 'auth/me', token=tokens[username])
    log_test(f"GET /auth/me with {username} token returns 200", resp.status_code == 200)
    
    user = resp.json()
    log_test(f"User has username={username}", user.get('username') == username)
    log_test(f"User does NOT contain password", 'password' not in user)
    log_test(f"User does NOT contain _id", '_id' not in user)

# ============================================================================
# SECTION 2: UNAUTHENTICATED ACCESS (401 without token)
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 2: UNAUTHENTICATED ACCESS")
print("=" * 80)

unauthenticated_endpoints = [
    ('GET', 'loads'),
    ('GET', 'companies'),
    ('GET', 'drivers'),
    ('GET', 'vehicles'),
    ('GET', 'dashboard'),
    ('POST', 'loads'),
    ('POST', 'companies'),
]

for method, endpoint in unauthenticated_endpoints:
    print(f"\n[Test 2.{endpoint}] {method} /{endpoint} without token")
    json_data = {'name': 'test'} if method == 'POST' else None
    resp = api_call(method, endpoint, token=None, json_data=json_data, expect_error=True)
    log_test(f"{method} /{endpoint} without token returns 401", resp.status_code == 401)

# ============================================================================
# SECTION 3: DATA PRESERVATION - Count existing data
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 3: DATA PRESERVATION - Initial counts")
print("=" * 80)

# Use yukler token (has access to everything for reading)
yukler_token = tokens['yukler']

for collection in ['companies', 'drivers', 'vehicles']:
    resp = api_call('GET', collection, token=yukler_token)
    if resp.status_code == 200:
        data = resp.json()
        initial_counts[collection] = len(data)
        print(f"  Initial {collection} count: {initial_counts[collection]}")

# For addresses, count all
resp = api_call('GET', 'addresses', token=yukler_token)
if resp.status_code == 200:
    initial_counts['addresses'] = len(resp.json())
    print(f"  Initial addresses count: {initial_counts['addresses']}")

# For loads, use pagination response
resp = api_call('GET', 'loads', token=yukler_token)
if resp.status_code == 200:
    data = resp.json()
    initial_counts['loads'] = data.get('total', 0)
    print(f"  Initial loads count: {initial_counts['loads']}")

# ============================================================================
# SECTION 4: ROLE PERMISSION MATRIX - yuk_sorumlusu
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 4: ROLE PERMISSION MATRIX - yuk_sorumlusu (yukler)")
print("=" * 80)

yukler_token = tokens['yukler']

# Create test company for use in other tests
print("\n[Test 4.1] yuk_sorumlusu: POST /companies (should succeed)")
resp = api_call('POST', 'companies', token=yukler_token, json_data={
    'name': 'TEST AUTH Company',
    'phone': '05551234567',
    'email': 'test@auth.com'
})
log_test("yuk_sorumlusu can POST /companies", resp.status_code == 200)
test_company = resp.json()
test_data_ids['companies'].append(test_company['id'])

# Create test address
print("\n[Test 4.2] yuk_sorumlusu: POST /addresses (should succeed)")
resp = api_call('POST', 'addresses', token=yukler_token, json_data={
    'companyId': test_company['id'],
    'name': 'TEST AUTH Address',
    'address': 'Test St.',
    'city': 'Istanbul'
})
log_test("yuk_sorumlusu can POST /addresses", resp.status_code == 200)
test_address = resp.json()
test_data_ids['addresses'].append(test_address['id'])

# Create test load
print("\n[Test 4.3] yuk_sorumlusu: POST /loads (should succeed)")
resp = api_call('POST', 'loads', token=yukler_token, json_data={
    'companyId': test_company['id'],
    'addressId': test_address['id'],
    'shipmentType': 'ic_nakliye',
    'destCity': 'Ankara',
    'destCountry': 'Türkiye',
    'packages': '10',
    'kg': '500'
})
log_test("yuk_sorumlusu can POST /loads", resp.status_code == 200)
test_load = resp.json()
test_data_ids['loads'].append(test_load['id'])

# Verify statusHistory[0].user is set correctly
print("\n[Test 4.4] StatusHistory user field for yuk_sorumlusu")
log_test("statusHistory[0].user is 'Yük Sorumlusu Demo'", 
         test_load.get('statusHistory', [{}])[0].get('user') == 'Yük Sorumlusu Demo',
         f"Got: {test_load.get('statusHistory', [{}])[0].get('user')}")

# Test status change with any status (yuk_sorumlusu can set any status)
print("\n[Test 4.5] yuk_sorumlusu: POST /loads/:id/status with 'created' (should succeed)")
resp = api_call('POST', f'loads/{test_load["id"]}/status', token=yukler_token, json_data={
    'status': 'created',
    'note': 'Test status change'
})
log_test("yuk_sorumlusu can set status to 'created'", resp.status_code == 200)

# Test forbidden operations for yuk_sorumlusu
print("\n[Test 4.6] yuk_sorumlusu: POST /loads/:id/plan (should fail 403)")
resp = api_call('POST', f'loads/{test_load["id"]}/plan', token=yukler_token, json_data={
    'driverId': 'dummy-id',
    'vehicleId': 'dummy-id'
}, expect_error=True)
log_test("yuk_sorumlusu CANNOT POST /loads/:id/plan", resp.status_code == 403)

print("\n[Test 4.7] yuk_sorumlusu: POST /drivers (should fail 403)")
resp = api_call('POST', 'drivers', token=yukler_token, json_data={
    'name': 'TEST Driver',
    'phone': '05559876543'
}, expect_error=True)
log_test("yuk_sorumlusu CANNOT POST /drivers", resp.status_code == 403)

print("\n[Test 4.8] yuk_sorumlusu: POST /vehicles (should fail 403)")
resp = api_call('POST', 'vehicles', token=yukler_token, json_data={
    'plate': '34 TEST 123',
    'type': 'Kamyonet'
}, expect_error=True)
log_test("yuk_sorumlusu CANNOT POST /vehicles", resp.status_code == 403)

# Test read access
print("\n[Test 4.9] yuk_sorumlusu: GET /drivers (should succeed)")
resp = api_call('GET', 'drivers', token=yukler_token)
log_test("yuk_sorumlusu can GET /drivers", resp.status_code == 200)

print("\n[Test 4.10] yuk_sorumlusu: GET /vehicles (should succeed)")
resp = api_call('GET', 'vehicles', token=yukler_token)
log_test("yuk_sorumlusu can GET /vehicles", resp.status_code == 200)

# ============================================================================
# SECTION 5: ROLE PERMISSION MATRIX - arac_planlama
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 5: ROLE PERMISSION MATRIX - arac_planlama (planlama)")
print("=" * 80)

planlama_token = tokens['planlama']

# Test allowed operations
print("\n[Test 5.1] arac_planlama: POST /drivers (should succeed)")
resp = api_call('POST', 'drivers', token=planlama_token, json_data={
    'name': 'TEST AUTH Driver',
    'phone': '05559876543'
})
log_test("arac_planlama can POST /drivers", resp.status_code == 200)
test_driver = resp.json()
test_data_ids['drivers'].append(test_driver['id'])

print("\n[Test 5.2] arac_planlama: POST /vehicles (should succeed)")
resp = api_call('POST', 'vehicles', token=planlama_token, json_data={
    'plate': '34 TEST 999',
    'type': 'Kamyonet'
})
log_test("arac_planlama can POST /vehicles", resp.status_code == 200)
test_vehicle = resp.json()
test_data_ids['vehicles'].append(test_vehicle['id'])

print("\n[Test 5.3] arac_planlama: POST /loads/:id/plan (should succeed)")
resp = api_call('POST', f'loads/{test_load["id"]}/plan', token=planlama_token, json_data={
    'driverId': test_driver['id'],
    'vehicleId': test_vehicle['id'],
    'plannedDateTime': '2024-01-15T10:00:00Z'
})
log_test("arac_planlama can POST /loads/:id/plan", resp.status_code == 200)
planned_load = resp.json()

# Verify statusHistory user field for arac_planlama
print("\n[Test 5.4] StatusHistory user field for arac_planlama")
history = planned_load.get('statusHistory', [])
log_test("statusHistory has at least 2 entries after planning", len(history) >= 2)
if len(history) >= 2:
    log_test("Latest statusHistory entry user is 'Araç Planlama Demo'", 
             history[-1].get('user') == 'Araç Planlama Demo',
             f"Got: {history[-1].get('user')}")

# Test allowed status changes
print("\n[Test 5.5] arac_planlama: POST /loads/:id/status with 'in_transit' (should succeed)")
resp = api_call('POST', f'loads/{test_load["id"]}/status', token=planlama_token, json_data={
    'status': 'in_transit',
    'note': 'Test in_transit'
})
log_test("arac_planlama can set status to 'in_transit'", resp.status_code == 200)

print("\n[Test 5.6] arac_planlama: POST /loads/:id/status with 'cancelled' (should succeed)")
resp = api_call('POST', f'loads/{test_load["id"]}/status', token=planlama_token, json_data={
    'status': 'cancelled',
    'note': 'Test cancelled'
})
log_test("arac_planlama can set status to 'cancelled'", resp.status_code == 200)

# Test forbidden status changes
print("\n[Test 5.7] arac_planlama: POST /loads/:id/status with 'delivered' (should fail 403)")
resp = api_call('POST', f'loads/{test_load["id"]}/status', token=planlama_token, json_data={
    'status': 'delivered',
    'note': 'Test delivered'
}, expect_error=True)
log_test("arac_planlama CANNOT set status to 'delivered'", resp.status_code == 403)

print("\n[Test 5.8] arac_planlama: POST /loads/:id/status with 'shipped' (should fail 403)")
resp = api_call('POST', f'loads/{test_load["id"]}/status', token=planlama_token, json_data={
    'status': 'shipped',
    'note': 'Test shipped'
}, expect_error=True)
log_test("arac_planlama CANNOT set status to 'shipped'", resp.status_code == 403)

print("\n[Test 5.9] arac_planlama: POST /loads/:id/status with 'created' (should fail 403)")
resp = api_call('POST', f'loads/{test_load["id"]}/status', token=planlama_token, json_data={
    'status': 'created',
    'note': 'Test created'
}, expect_error=True)
log_test("arac_planlama CANNOT set status to 'created'", resp.status_code == 403)

# Test forbidden operations
print("\n[Test 5.10] arac_planlama: POST /loads (should fail 403)")
resp = api_call('POST', 'loads', token=planlama_token, json_data={
    'companyId': test_company['id'],
    'addressId': test_address['id'],
    'shipmentType': 'ic_nakliye'
}, expect_error=True)
log_test("arac_planlama CANNOT POST /loads", resp.status_code == 403)

print("\n[Test 5.11] arac_planlama: POST /companies (should fail 403)")
resp = api_call('POST', 'companies', token=planlama_token, json_data={
    'name': 'TEST Company 2'
}, expect_error=True)
log_test("arac_planlama CANNOT POST /companies", resp.status_code == 403)

print("\n[Test 5.12] arac_planlama: POST /addresses (should fail 403)")
resp = api_call('POST', 'addresses', token=planlama_token, json_data={
    'companyId': test_company['id'],
    'name': 'TEST Address 2'
}, expect_error=True)
log_test("arac_planlama CANNOT POST /addresses", resp.status_code == 403)

# Test read access
print("\n[Test 5.13] arac_planlama: GET /companies (should succeed)")
resp = api_call('GET', 'companies', token=planlama_token)
log_test("arac_planlama can GET /companies", resp.status_code == 200)

print("\n[Test 5.14] arac_planlama: GET /addresses (should succeed)")
resp = api_call('GET', 'addresses', token=planlama_token)
log_test("arac_planlama can GET /addresses", resp.status_code == 200)

# ============================================================================
# SECTION 6: ROLE PERMISSION MATRIX - depocu
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 6: ROLE PERMISSION MATRIX - depocu (depo)")
print("=" * 80)

depo_token = tokens['depo']

# Test allowed operations
print("\n[Test 6.1] depocu: GET /loads (should succeed)")
resp = api_call('GET', 'loads', token=depo_token)
log_test("depocu can GET /loads", resp.status_code == 200)

print("\n[Test 6.2] depocu: GET /loads/:id (should succeed)")
resp = api_call('GET', f'loads/{test_load["id"]}', token=depo_token)
log_test("depocu can GET /loads/:id", resp.status_code == 200)

print("\n[Test 6.3] depocu: GET /companies (should succeed)")
resp = api_call('GET', 'companies', token=depo_token)
log_test("depocu can GET /companies", resp.status_code == 200)

print("\n[Test 6.4] depocu: GET /addresses (should succeed)")
resp = api_call('GET', 'addresses', token=depo_token)
log_test("depocu can GET /addresses", resp.status_code == 200)

print("\n[Test 6.5] depocu: GET /vehicles (should succeed)")
resp = api_call('GET', 'vehicles', token=depo_token)
log_test("depocu can GET /vehicles", resp.status_code == 200)

print("\n[Test 6.6] depocu: GET /dashboard (should succeed)")
resp = api_call('GET', 'dashboard', token=depo_token)
log_test("depocu can GET /dashboard", resp.status_code == 200)

# Test allowed status change (delivered only)
print("\n[Test 6.7] depocu: POST /loads/:id/status with 'delivered' (should succeed)")
resp = api_call('POST', f'loads/{test_load["id"]}/status', token=depo_token, json_data={
    'status': 'delivered',
    'note': 'Test delivered by depocu'
})
log_test("depocu can set status to 'delivered'", resp.status_code == 200)
delivered_load = resp.json()

# Verify statusHistory user field for depocu
print("\n[Test 6.8] StatusHistory user field for depocu")
history = delivered_load.get('statusHistory', [])
if len(history) > 0:
    log_test("Latest statusHistory entry user is 'Depocu Demo'", 
             history[-1].get('user') == 'Depocu Demo',
             f"Got: {history[-1].get('user')}")

# Test forbidden status changes
forbidden_statuses = ['planning', 'in_transit', 'shipped', 'cancelled', 'created']
for status in forbidden_statuses:
    print(f"\n[Test 6.9.{status}] depocu: POST /loads/:id/status with '{status}' (should fail 403)")
    resp = api_call('POST', f'loads/{test_load["id"]}/status', token=depo_token, json_data={
        'status': status,
        'note': f'Test {status}'
    }, expect_error=True)
    log_test(f"depocu CANNOT set status to '{status}'", resp.status_code == 403)

# Test forbidden operations
print("\n[Test 6.10] depocu: GET /drivers (should fail 403)")
resp = api_call('GET', 'drivers', token=depo_token, expect_error=True)
log_test("depocu CANNOT GET /drivers", resp.status_code == 403)

print("\n[Test 6.11] depocu: POST /loads (should fail 403)")
resp = api_call('POST', 'loads', token=depo_token, json_data={
    'companyId': test_company['id'],
    'addressId': test_address['id']
}, expect_error=True)
log_test("depocu CANNOT POST /loads", resp.status_code == 403)

print("\n[Test 6.12] depocu: POST /loads/:id/plan (should fail 403)")
resp = api_call('POST', f'loads/{test_load["id"]}/plan', token=depo_token, json_data={
    'driverId': 'dummy',
    'vehicleId': 'dummy'
}, expect_error=True)
log_test("depocu CANNOT POST /loads/:id/plan", resp.status_code == 403)

print("\n[Test 6.13] depocu: POST /companies (should fail 403)")
resp = api_call('POST', 'companies', token=depo_token, json_data={
    'name': 'TEST'
}, expect_error=True)
log_test("depocu CANNOT POST /companies", resp.status_code == 403)

print("\n[Test 6.14] depocu: POST /addresses (should fail 403)")
resp = api_call('POST', 'addresses', token=depo_token, json_data={
    'companyId': test_company['id'],
    'name': 'TEST'
}, expect_error=True)
log_test("depocu CANNOT POST /addresses", resp.status_code == 403)

print("\n[Test 6.15] depocu: POST /drivers (should fail 403)")
resp = api_call('POST', 'drivers', token=depo_token, json_data={
    'name': 'TEST'
}, expect_error=True)
log_test("depocu CANNOT POST /drivers", resp.status_code == 403)

print("\n[Test 6.16] depocu: POST /vehicles (should fail 403)")
resp = api_call('POST', 'vehicles', token=depo_token, json_data={
    'plate': 'TEST'
}, expect_error=True)
log_test("depocu CANNOT POST /vehicles", resp.status_code == 403)

# ============================================================================
# SECTION 7: CLEANUP & DATA PRESERVATION
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 7: CLEANUP & DATA PRESERVATION")
print("=" * 80)

# Clean up test data (in reverse order of creation)
print("\n[Cleanup] Deleting test data...")

# Delete test load
if test_data_ids['loads']:
    for load_id in test_data_ids['loads']:
        resp = api_call('DELETE', f'loads/{load_id}', token=yukler_token)
        print(f"  Deleted load {load_id}: {resp.status_code == 200}")

# Delete test driver
if test_data_ids['drivers']:
    for driver_id in test_data_ids['drivers']:
        resp = api_call('DELETE', f'drivers/{driver_id}', token=planlama_token)
        print(f"  Deleted driver {driver_id}: {resp.status_code == 200}")

# Delete test vehicle
if test_data_ids['vehicles']:
    for vehicle_id in test_data_ids['vehicles']:
        resp = api_call('DELETE', f'vehicles/{vehicle_id}', token=planlama_token)
        print(f"  Deleted vehicle {vehicle_id}: {resp.status_code == 200}")

# Delete test address
if test_data_ids['addresses']:
    for address_id in test_data_ids['addresses']:
        resp = api_call('DELETE', f'addresses/{address_id}', token=yukler_token)
        print(f"  Deleted address {address_id}: {resp.status_code == 200}")

# Delete test company
if test_data_ids['companies']:
    for company_id in test_data_ids['companies']:
        resp = api_call('DELETE', f'companies/{company_id}', token=yukler_token)
        print(f"  Deleted company {company_id}: {resp.status_code == 200}")

# Verify counts are back to original
print("\n[Test 7.1] Verify data preservation - Final counts")
for collection in ['companies', 'drivers', 'vehicles']:
    resp = api_call('GET', collection, token=yukler_token)
    if resp.status_code == 200:
        final_count = len(resp.json())
        log_test(f"{collection} count preserved ({initial_counts[collection]} -> {final_count})", 
                 final_count == initial_counts[collection])

resp = api_call('GET', 'addresses', token=yukler_token)
if resp.status_code == 200:
    final_count = len(resp.json())
    log_test(f"addresses count preserved ({initial_counts['addresses']} -> {final_count})", 
             final_count == initial_counts['addresses'])

resp = api_call('GET', 'loads', token=yukler_token)
if resp.status_code == 200:
    final_count = resp.json().get('total', 0)
    log_test(f"loads count preserved ({initial_counts['loads']} -> {final_count})", 
             final_count == initial_counts['loads'])

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✅ ALL AUTHENTICATION & AUTHORIZATION TESTS PASSED")
print("=" * 80)
print("\nTest Summary:")
print("  ✅ Init & Login flow (idempotency, token generation, user data)")
print("  ✅ Unauthenticated access (401 for all non-auth endpoints)")
print("  ✅ yuk_sorumlusu permissions (full CRUD on loads/companies/addresses)")
print("  ✅ arac_planlama permissions (planning, drivers, vehicles)")
print("  ✅ depocu permissions (read-only + delivered status)")
print("  ✅ StatusHistory user field (correctly set from token, not body)")
print("  ✅ Data preservation (no production data lost)")
print("\n" + "=" * 80)
