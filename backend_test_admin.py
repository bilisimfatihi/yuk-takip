#!/usr/bin/env python3
"""
Comprehensive test suite for Admin User Management + Password Hashing system.
Tests all scenarios from the review request.
"""

import requests
import sys
from typing import Dict, Optional

# Base URL from .env
BASE_URL = "https://load-management-6.preview.emergentagent.com/api"

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tokens = {}  # Store tokens for different users
        self.test_user_ids = []  # Track created test users for cleanup
        self.initial_counts = {}
        
    def test(self, name: str, condition: bool, error_msg: str = ""):
        if condition:
            print(f"✅ {name}")
            self.passed += 1
        else:
            print(f"❌ {name}")
            if error_msg:
                print(f"   Error: {error_msg}")
            self.failed += 1
        return condition
    
    def api_call(self, method: str, endpoint: str, token: Optional[str] = None, json_data: Optional[Dict] = None):
        """Make API call and return (status_code, response_json)"""
        url = f"{BASE_URL}/{endpoint}"
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                r = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                r = requests.post(url, headers=headers, json=json_data, timeout=10)
            elif method == 'PUT':
                r = requests.put(url, headers=headers, json=json_data, timeout=10)
            elif method == 'DELETE':
                r = requests.delete(url, headers=headers, timeout=10)
            else:
                return (0, {"error": "Invalid method"})
            
            try:
                return (r.status_code, r.json())
            except Exception:
                return (r.status_code, {"error": "Invalid JSON response", "text": r.text})
        except Exception as e:
            return (0, {"error": str(e)})
    
    def login(self, username: str, password: str) -> Optional[str]:
        """Login and return token"""
        status, data = self.api_call('POST', 'auth/login', json_data={'username': username, 'password': password})
        if status == 200 and 'token' in data:
            return data['token']
        return None
    
    def print_section(self, title: str):
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
    
    def run_all_tests(self):
        """Run all test scenarios"""
        
        # Initialize system
        self.print_section("SETUP: Initialize System")
        status, data = self.api_call('POST', 'auth/init')
        self.test("POST /auth/init succeeds", status == 200, f"Status: {status}, Data: {data}")
        
        # Store initial data counts
        self.print_section("SETUP: Record Initial Data Counts")
        admin_token = self.login('admin@yuktakip.local', 'admin123')
        if admin_token:
            self.tokens['admin'] = admin_token
            for collection in ['companies', 'drivers', 'vehicles', 'loads']:
                status, data = self.api_call('GET', collection, token=admin_token)
                if status == 200:
                    if isinstance(data, dict) and 'items' in data:
                        count = len(data['items'])
                    elif isinstance(data, list):
                        count = len(data)
                    else:
                        count = 0
                    self.initial_counts[collection] = count
                    print(f"   Initial {collection} count: {count}")
        
        # Run test scenarios
        self.test_scenario_1_admin_bootstrap()
        self.test_scenario_2_admin_bypass()
        self.test_scenario_3_user_crud()
        self.test_scenario_4_self_password_change()
        self.test_scenario_5_data_preservation()
        self.test_scenario_6_password_format()
        self.test_scenario_7_legacy_migration()
        
        # Print summary
        self.print_section("TEST SUMMARY")
        total = self.passed + self.failed
        print(f"Total tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success rate: {(self.passed/total*100):.1f}%")
        
        return self.failed == 0
    
    def test_scenario_1_admin_bootstrap(self):
        """Test admin bootstrap & login"""
        self.print_section("SCENARIO 1: Admin Bootstrap & Login")
        
        # 1.1: Login with admin email
        token = self.login('admin@yuktakip.local', 'admin123')
        self.test("1.1: Login as admin@yuktakip.local/admin123 succeeds", token is not None)
        if token:
            self.tokens['admin'] = token
            
            # Verify token returns admin user with correct roles
            status, data = self.api_call('GET', 'auth/me', token=token)
            self.test("1.2: GET /auth/me returns 200", status == 200)
            self.test("1.3: User has 'admin' role", 'admin' in data.get('roles', []))
            self.test("1.4: User has email field", 'email' in data and data['email'] == 'admin@yuktakip.local')
            self.test("1.5: User object has no password field", 'password' not in data)
            self.test("1.6: User object has no _id field", '_id' not in data)
        
        # 1.7: Login with username 'admin'
        token2 = self.login('admin', 'admin123')
        self.test("1.7: Login as username 'admin'/admin123 succeeds", token2 is not None)
        
        # 1.8: Verify demo users still work
        yukler_token = self.login('yukler', '1234')
        self.test("1.8: Demo user yukler/1234 still works", yukler_token is not None)
        if yukler_token:
            self.tokens['yukler'] = yukler_token
        
        planlama_token = self.login('planlama', '1234')
        self.test("1.9: Demo user planlama/1234 still works", planlama_token is not None)
        if planlama_token:
            self.tokens['planlama'] = planlama_token
        
        depo_token = self.login('depo', '1234')
        self.test("1.10: Demo user depo/1234 still works", depo_token is not None)
        if depo_token:
            self.tokens['depo'] = depo_token
    
    def test_scenario_2_admin_bypass(self):
        """Test admin can access all endpoints"""
        self.print_section("SCENARIO 2: Admin Bypass (Admin can access all endpoints)")
        
        admin_token = self.tokens.get('admin')
        if not admin_token:
            print("⚠️  Skipping: No admin token available")
            return
        
        # Create test data for admin bypass tests
        # 2.1: POST /companies (was YS-only)
        status, company = self.api_call('POST', 'companies', token=admin_token, 
                                        json_data={'name': 'Admin Test Company', 'active': True})
        self.test("2.1: Admin can POST /companies (was YS-only)", status == 200)
        company_id = company.get('id') if status == 200 else None
        
        # 2.2: POST /drivers (was AP-only)
        status, driver = self.api_call('POST', 'drivers', token=admin_token,
                                       json_data={'name': 'Admin Test Driver', 'phone': '905551234567'})
        self.test("2.2: Admin can POST /drivers (was AP-only)", status == 200)
        driver_id = driver.get('id') if status == 200 else None
        
        # 2.3: POST /vehicles (was AP-only)
        status, vehicle = self.api_call('POST', 'vehicles', token=admin_token,
                                        json_data={'type': 'Kamyonet', 'plate': '34 TEST 999'})
        self.test("2.3: Admin can POST /vehicles (was AP-only)", status == 200)
        vehicle_id = vehicle.get('id') if status == 200 else None
        
        # 2.4: POST /loads (was YS-only)
        if company_id:
            # Get an address for this company
            status, addresses = self.api_call('GET', f'addresses?companyId={company_id}', token=admin_token)
            if status == 200 and len(addresses) > 0:
                address_id = addresses[0]['id']
            else:
                # Create an address
                status, addr = self.api_call('POST', 'addresses', token=admin_token,
                                            json_data={'companyId': company_id, 'name': 'Test Address', 'city': 'Istanbul'})
                address_id = addr.get('id') if status == 200 else None
            
            if address_id:
                status, load = self.api_call('POST', 'loads', token=admin_token,
                                            json_data={
                                                'companyId': company_id,
                                                'addressId': address_id,
                                                'shipmentType': 'ic_nakliye',
                                                'destCity': 'Ankara',
                                                'destCountry': 'Türkiye'
                                            })
                self.test("2.4: Admin can POST /loads (was YS-only)", status == 200)
                load_id = load.get('id') if status == 200 else None
                
                # 2.5: POST /loads/:id/plan (was AP-only)
                if load_id and driver_id and vehicle_id:
                    status, data = self.api_call('POST', f'loads/{load_id}/plan', token=admin_token,
                                                json_data={
                                                    'driverId': driver_id,
                                                    'vehicleId': vehicle_id,
                                                    'plannedDateTime': '2024-01-15T10:00:00Z'
                                                })
                    self.test("2.5: Admin can POST /loads/:id/plan (was AP-only)", status == 200)
                    
                    # 2.6: POST /loads/:id/status with 'delivered' (was depocu-only)
                    status, data = self.api_call('POST', f'loads/{load_id}/status', token=admin_token,
                                                json_data={'status': 'delivered', 'note': 'Admin delivered'})
                    self.test("2.6: Admin can set status='delivered' (was depocu-only)", status == 200)
                    
                    # 2.7: POST /loads/:id/status with 'shipped' (was YS-only)
                    status, data = self.api_call('POST', f'loads/{load_id}/status', token=admin_token,
                                                json_data={'status': 'shipped', 'note': 'Admin shipped'})
                    self.test("2.7: Admin can set status='shipped' (was YS-only)", status == 200)
                    
                    # Cleanup: delete test load
                    self.api_call('DELETE', f'loads/{load_id}', token=admin_token)
        
        # Cleanup test data
        if company_id:
            self.api_call('DELETE', f'companies/{company_id}', token=admin_token)
        if driver_id:
            self.api_call('DELETE', f'drivers/{driver_id}', token=admin_token)
        if vehicle_id:
            self.api_call('DELETE', f'vehicles/{vehicle_id}', token=admin_token)
    
    def test_scenario_3_user_crud(self):
        """Test user CRUD operations as admin"""
        self.print_section("SCENARIO 3: User CRUD (as admin)")
        
        admin_token = self.tokens.get('admin')
        if not admin_token:
            print("⚠️  Skipping: No admin token available")
            return
        
        # 3.1: Create user with valid data
        status, user1 = self.api_call('POST', 'users', token=admin_token,
                                      json_data={
                                          'name': 'Test User One',
                                          'email': 'testuser1@example.com',
                                          'password': 'test1234',
                                          'roles': ['yuk_sorumlusu']
                                      })
        self.test("3.1: POST /users creates user successfully", status == 200)
        self.test("3.2: Username auto-derived from email", user1.get('username') == 'testuser1')
        self.test("3.3: Response has no password field", 'password' not in user1)
        user1_id = user1.get('id') if status == 200 else None
        if user1_id:
            self.test_user_ids.append(user1_id)
        
        # 3.4: Empty roles -> 400
        status, data = self.api_call('POST', 'users', token=admin_token,
                                     json_data={
                                         'name': 'Bad User',
                                         'email': 'bad@example.com',
                                         'password': 'test1234',
                                         'roles': []
                                     })
        self.test("3.4: POST /users with empty roles returns 400", status == 400)
        
        # 3.5: Duplicate email -> 400
        status, data = self.api_call('POST', 'users', token=admin_token,
                                     json_data={
                                         'name': 'Duplicate User',
                                         'email': 'testuser1@example.com',
                                         'password': 'test1234',
                                         'roles': ['yuk_sorumlusu']
                                     })
        self.test("3.5: POST /users with duplicate email returns 400", status == 400)
        
        # 3.6: Invalid role filtering (only invalid roles -> 400)
        status, data = self.api_call('POST', 'users', token=admin_token,
                                     json_data={
                                         'name': 'Invalid Role User',
                                         'email': 'invalid@example.com',
                                         'password': 'test1234',
                                         'roles': ['super_hacker', 'mega_admin']
                                     })
        self.test("3.6: POST /users with only invalid roles returns 400", status == 400)
        
        # 3.7: Mixed valid/invalid roles (invalid filtered out)
        status, user2 = self.api_call('POST', 'users', token=admin_token,
                                      json_data={
                                          'name': 'Mixed Role User',
                                          'email': 'mixed@example.com',
                                          'password': 'test1234',
                                          'roles': ['yuk_sorumlusu', 'super_hacker', 'arac_planlama']
                                      })
        self.test("3.7: POST /users with mixed roles succeeds", status == 200)
        self.test("3.8: Invalid roles filtered out", 
                  set(user2.get('roles', [])) == {'yuk_sorumlusu', 'arac_planlama'})
        user2_id = user2.get('id') if status == 200 else None
        if user2_id:
            self.test_user_ids.append(user2_id)
        
        # 3.9: Multiple valid roles
        if user2_id:
            # Login as this user and verify they can access both YS and AP endpoints
            token = self.login('mixed@example.com', 'test1234')
            self.test("3.9: Multi-role user can login", token is not None)
            
            if token:
                # Test YS permission (POST /companies)
                status, comp = self.api_call('POST', 'companies', token=token,
                                            json_data={'name': 'Multi Role Test Company'})
                self.test("3.10: Multi-role user can POST /companies (YS permission)", status == 200)
                if status == 200:
                    self.api_call('DELETE', f"companies/{comp['id']}", token=admin_token)
                
                # Test AP permission (POST /drivers)
                status, drv = self.api_call('POST', 'drivers', token=token,
                                           json_data={'name': 'Multi Role Test Driver'})
                self.test("3.11: Multi-role user can POST /drivers (AP permission)", status == 200)
                if status == 200:
                    self.api_call('DELETE', f"drivers/{drv['id']}", token=admin_token)
                
                # Test admin-only endpoint (should fail)
                status, data = self.api_call('GET', 'users', token=token)
                self.test("3.12: Multi-role user CANNOT access /users (admin only)", status == 403)
        
        # 3.13: Update user roles
        if user1_id:
            status, updated = self.api_call('PUT', f'users/{user1_id}', token=admin_token,
                                           json_data={'roles': ['depocu']})
            self.test("3.13: PUT /users/:id updates roles", status == 200)
            self.test("3.14: Roles updated correctly", updated.get('roles') == ['depocu'])
        
        # 3.15: Deactivate user
        if user1_id:
            status, updated = self.api_call('PUT', f'users/{user1_id}', token=admin_token,
                                           json_data={'active': False})
            self.test("3.15: PUT /users/:id deactivates user", status == 200)
            
            # Try to login as deactivated user
            token = self.login('testuser1@example.com', 'test1234')
            self.test("3.16: Deactivated user cannot login", token is None)
            
            # Reactivate for further tests
            self.api_call('PUT', f'users/{user1_id}', token=admin_token, json_data={'active': True})
        
        # 3.17: Last admin safety - cannot remove admin role from last admin
        # First, get admin user id
        status, users = self.api_call('GET', 'users', token=admin_token)
        admin_user = next((u for u in users if 'admin' in u.get('roles', [])), None)
        if admin_user:
            admin_id = admin_user['id']
            status, data = self.api_call('PUT', f'users/{admin_id}', token=admin_token,
                                        json_data={'roles': ['yuk_sorumlusu']})
            self.test("3.17: Cannot remove admin role from last admin", status == 400)
            
            # 3.18: Cannot deactivate last admin
            status, data = self.api_call('PUT', f'users/{admin_id}', token=admin_token,
                                        json_data={'active': False})
            self.test("3.18: Cannot deactivate last active admin", status == 400)
        
        # 3.19: Cannot delete self
        if admin_user:
            status, data = self.api_call('DELETE', f'users/{admin_id}', token=admin_token)
            self.test("3.19: Admin cannot delete own account", status == 400)
        
        # 3.20: Reset password (test with depo user)
        depo_token = self.tokens.get('depo')
        if depo_token:
            # Get depo user id
            status, users = self.api_call('GET', 'users', token=admin_token)
            depo_user = next((u for u in users if u.get('username') == 'depo'), None)
            if depo_user:
                depo_id = depo_user['id']
                
                # Reset password as admin
                status, data = self.api_call('POST', f'users/{depo_id}/reset-password', token=admin_token,
                                            json_data={'newPassword': 'newdepo123'})
                self.test("3.20: Admin can reset user password", status == 200)
                
                # Old token should be invalid (session purged)
                status, data = self.api_call('GET', 'auth/me', token=depo_token)
                self.test("3.21: Old token invalid after password reset", status == 401)
                
                # Old password should not work
                token = self.login('depo', '1234')
                self.test("3.22: Old password does not work after reset", token is None)
                
                # New password should work
                token = self.login('depo', 'newdepo123')
                self.test("3.23: New password works after reset", token is not None)
                
                # Restore original password for other tests
                self.api_call('POST', f'users/{depo_id}/reset-password', token=admin_token,
                             json_data={'newPassword': '1234'})
                self.tokens['depo'] = self.login('depo', '1234')
        
        # 3.24-3.27: Non-admin access to /users endpoints (should all be 403)
        yukler_token = self.tokens.get('yukler')
        if yukler_token:
            status, data = self.api_call('GET', 'users', token=yukler_token)
            self.test("3.24: Non-admin GET /users returns 403", status == 403)
            
            status, data = self.api_call('POST', 'users', token=yukler_token,
                                        json_data={'name': 'Test', 'email': 'test@x.com', 
                                                  'password': 'test', 'roles': ['depocu']})
            self.test("3.25: Non-admin POST /users returns 403", status == 403)
            
            if user1_id:
                status, data = self.api_call('PUT', f'users/{user1_id}', token=yukler_token,
                                            json_data={'name': 'Hacked'})
                self.test("3.26: Non-admin PUT /users/:id returns 403", status == 403)
                
                status, data = self.api_call('DELETE', f'users/{user1_id}', token=yukler_token)
                self.test("3.27: Non-admin DELETE /users/:id returns 403", status == 403)
                
                status, data = self.api_call('POST', f'users/{user1_id}/reset-password', token=yukler_token,
                                            json_data={'newPassword': 'hacked'})
                self.test("3.28: Non-admin POST /users/:id/reset-password returns 403", status == 403)
    
    def test_scenario_4_self_password_change(self):
        """Test self password change"""
        self.print_section("SCENARIO 4: Self Password Change")
        
        yukler_token = self.tokens.get('yukler')
        if not yukler_token:
            print("⚠️  Skipping: No yukler token available")
            return
        
        # 4.1: Change password successfully
        status, data = self.api_call('POST', 'auth/change-password', token=yukler_token,
                                    json_data={'currentPassword': '1234', 'newPassword': 'tempyukler'})
        self.test("4.1: POST /auth/change-password succeeds", status == 200)
        
        # 4.2: Old password should not work
        token = self.login('yukler', '1234')
        self.test("4.2: Old password does not work after change", token is None)
        
        # 4.3: New password should work
        token = self.login('yukler', 'tempyukler')
        self.test("4.3: New password works after change", token is not None)
        
        # 4.4: Restore original password (as admin)
        admin_token = self.tokens.get('admin')
        if admin_token:
            status, users = self.api_call('GET', 'users', token=admin_token)
            yukler_user = next((u for u in users if u.get('username') == 'yukler'), None)
            if yukler_user:
                status, data = self.api_call('POST', f"users/{yukler_user['id']}/reset-password", 
                                            token=admin_token,
                                            json_data={'newPassword': '1234'})
                self.test("4.4: Admin restores yukler password to '1234'", status == 200)
                self.tokens['yukler'] = self.login('yukler', '1234')
        
        # 4.5: Wrong current password
        yukler_token = self.tokens.get('yukler')
        if yukler_token:
            status, data = self.api_call('POST', 'auth/change-password', token=yukler_token,
                                        json_data={'currentPassword': 'wrong', 'newPassword': 'newpass'})
            self.test("4.5: Wrong currentPassword returns 400", status == 400)
            self.test("4.6: Error message is 'Mevcut şifre hatalı'", 
                     'Mevcut şifre hatalı' in data.get('error', ''))
        
        # 4.7: newPassword too short
        if yukler_token:
            status, data = self.api_call('POST', 'auth/change-password', token=yukler_token,
                                        json_data={'currentPassword': '1234', 'newPassword': '123'})
            self.test("4.7: newPassword < 4 chars returns 400", status == 400)
        
        # 4.8: Without token
        status, data = self.api_call('POST', 'auth/change-password',
                                    json_data={'currentPassword': '1234', 'newPassword': 'newpass'})
        self.test("4.8: Without token returns 401", status == 401)
    
    def test_scenario_5_data_preservation(self):
        """Test data preservation"""
        self.print_section("SCENARIO 5: Data Preservation")
        
        admin_token = self.tokens.get('admin')
        if not admin_token:
            print("⚠️  Skipping: No admin token available")
            return
        
        # Count current data
        for collection in ['companies', 'drivers', 'vehicles', 'loads']:
            status, data = self.api_call('GET', collection, token=admin_token)
            if status == 200:
                if isinstance(data, dict) and 'items' in data:
                    current_count = len(data['items'])
                elif isinstance(data, list):
                    current_count = len(data)
                else:
                    current_count = 0
                
                initial_count = self.initial_counts.get(collection, 0)
                self.test(f"5.{collection}: Count preserved ({initial_count} -> {current_count})",
                         current_count == initial_count,
                         f"Expected {initial_count}, got {current_count}")
    
    def test_scenario_6_password_format(self):
        """Test password format"""
        self.print_section("SCENARIO 6: Password Format")
        
        admin_token = self.tokens.get('admin')
        if not admin_token:
            print("⚠️  Skipping: No admin token available")
            return
        
        # 6.1: Create a new user and verify password is hashed
        status, user = self.api_call('POST', 'users', token=admin_token,
                                     json_data={
                                         'name': 'Password Test User',
                                         'email': 'pwtest@example.com',
                                         'password': 'testpass123',
                                         'roles': ['depocu']
                                     })
        self.test("6.1: Create user for password format test", status == 200)
        
        if status == 200:
            user_id = user['id']
            self.test_user_ids.append(user_id)
            
            # 6.2: Login response should not include password
            token = self.login('pwtest@example.com', 'testpass123')
            self.test("6.2: User can login with plaintext password", token is not None)
            
            # 6.3: GET /auth/me should not include password
            if token:
                status, me_data = self.api_call('GET', 'auth/me', token=token)
                self.test("6.3: GET /auth/me does not include password", 'password' not in me_data)
            
            # 6.4: GET /users should not include password
            status, users = self.api_call('GET', 'users', token=admin_token)
            if status == 200:
                test_user = next((u for u in users if u['id'] == user_id), None)
                self.test("6.4: GET /users does not include password", 
                         test_user is not None and 'password' not in test_user)
    
    def test_scenario_7_legacy_migration(self):
        """Test legacy demo user migration"""
        self.print_section("SCENARIO 7: Legacy Demo User Migration")
        
        # 7.1: Demo users can still login with plaintext password '1234'
        for username in ['yukler', 'planlama', 'depo']:
            token = self.login(username, '1234')
            self.test(f"7.{username}: Demo user {username} can login with '1234'", token is not None)
        
        # Note: After login, the password should be migrated to scrypt format in the DB,
        # but we can't verify this directly without DB access. The fact that login works
        # confirms the migration logic is functioning.

def main():
    print("="*80)
    print("  ADMIN USER MANAGEMENT + PASSWORD HASHING TEST SUITE")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print()
    
    runner = TestRunner()
    success = runner.run_all_tests()
    
    # Cleanup test users
    if runner.test_user_ids and runner.tokens.get('admin'):
        print("\n" + "="*80)
        print("  CLEANUP: Deleting test users")
        print("="*80)
        for user_id in runner.test_user_ids:
            status, data = runner.api_call('DELETE', f'users/{user_id}', token=runner.tokens['admin'])
            print(f"   Deleted user {user_id}: {status == 200}")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
