#!/usr/bin/env python3
"""
Backend test for Vehicle Type Standardization + Tractor/Trailer Planning Validation
YükTakip MVP - Test vehicle types and dorse planning logic
"""

import requests
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/.env')
BASE_URL = os.getenv('NEXT_PUBLIC_BASE_URL', 'https://load-management-6.preview.emergentagent.com')
API_URL = f"{BASE_URL}/api"

# Test counters
tests_passed = 0
tests_failed = 0
test_vehicles = []
test_drivers = []
test_loads = []
test_companies = []
test_addresses = []

def log_test(name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
    else:
        tests_failed += 1
        print(f"❌ {name}")
        if details:
            print(f"   {details}")

def login(username, password):
    """Login and return token"""
    try:
        resp = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('token')
        else:
            print(f"Login failed for {username}: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"Login exception for {username}: {e}")
        return None

def count_data(token):
    """Count existing data for preservation check"""
    headers = {"Authorization": f"Bearer {token}"}
    counts = {}
    try:
        # Vehicles
        resp = requests.get(f"{API_URL}/vehicles", headers=headers, timeout=10)
        counts['vehicles'] = len(resp.json()) if resp.status_code == 200 else 0
        
        # Drivers
        resp = requests.get(f"{API_URL}/drivers", headers=headers, timeout=10)
        counts['drivers'] = len(resp.json()) if resp.status_code == 200 else 0
        
        # Loads
        resp = requests.get(f"{API_URL}/loads?pageSize=200", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            counts['loads'] = data.get('total', 0)
        else:
            counts['loads'] = 0
        
        # Companies
        resp = requests.get(f"{API_URL}/companies", headers=headers, timeout=10)
        counts['companies'] = len(resp.json()) if resp.status_code == 200 else 0
        
        # Addresses
        resp = requests.get(f"{API_URL}/addresses", headers=headers, timeout=10)
        counts['addresses'] = len(resp.json()) if resp.status_code == 200 else 0
        
        return counts
    except Exception as e:
        print(f"Error counting data: {e}")
        return {}

def cleanup_test_data(admin_token, planlama_token):
    """Delete all test data created during tests"""
    global test_vehicles, test_drivers, test_loads, test_companies, test_addresses
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    planlama_headers = {"Authorization": f"Bearer {planlama_token}"}
    
    # Delete test loads (as admin)
    for load_id in test_loads:
        try:
            requests.delete(f"{API_URL}/loads/{load_id}", headers=admin_headers, timeout=10)
        except Exception:
            pass
    
    # Delete test vehicles (as planlama)
    for vehicle_id in test_vehicles:
        try:
            requests.delete(f"{API_URL}/vehicles/{vehicle_id}", headers=planlama_headers, timeout=10)
        except Exception:
            pass
    
    # Delete test drivers (as planlama)
    for driver_id in test_drivers:
        try:
            requests.delete(f"{API_URL}/drivers/{driver_id}", headers=planlama_headers, timeout=10)
        except Exception:
            pass
    
    # Delete test addresses (as admin)
    for address_id in test_addresses:
        try:
            requests.delete(f"{API_URL}/addresses/{address_id}", headers=admin_headers, timeout=10)
        except Exception:
            pass
    
    # Delete test companies (as admin)
    for company_id in test_companies:
        try:
            requests.delete(f"{API_URL}/companies/{company_id}", headers=admin_headers, timeout=10)
        except Exception:
            pass

def test_part_a_vehicle_types(admin_token, planlama_token):
    """Part A: Vehicle Type Standardization"""
    print("\n" + "="*80)
    print("PART A: Vehicle Type Standardization")
    print("="*80)
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    planlama_headers = {"Authorization": f"Bearer {planlama_token}"}
    yukler_token = login("yukler", "1234")
    depo_token = login("depo", "1234")
    
    # Test 1: POST with type='tractor'
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "tractor", "plate": "BTEST-1"}, 
                        headers=planlama_headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test_vehicles.append(data['id'])
        log_test("Test 1: POST vehicle type='tractor'", 
                data.get('type') == 'tractor',
                f"Stored type: {data.get('type')}")
    else:
        log_test("Test 1: POST vehicle type='tractor'", False, f"Status: {resp.status_code}, {resp.text}")
    
    # Test 2: POST with type='trailer'
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "trailer", "plate": "BTEST-2"}, 
                        headers=planlama_headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test_vehicles.append(data['id'])
        log_test("Test 2: POST vehicle type='trailer'", 
                data.get('type') == 'trailer',
                f"Stored type: {data.get('type')}")
    else:
        log_test("Test 2: POST vehicle type='trailer'", False, f"Status: {resp.status_code}, {resp.text}")
    
    # Test 3: POST with type='UFO' (invalid)
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "UFO", "plate": "BTEST-3"}, 
                        headers=planlama_headers, timeout=10)
    passed = resp.status_code == 400 and "Geçersiz araç tipi" in resp.text
    log_test("Test 3: POST vehicle type='UFO' returns 400", 
            passed,
            f"Status: {resp.status_code}, Message: {resp.text[:100]}")
    
    # Test 4: POST with type='Tır' (Turkish alias)
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "Tır", "plate": "BTEST-4"}, 
                        headers=planlama_headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test_vehicles.append(data['id'])
        log_test("Test 4: POST vehicle type='Tır' normalized to 'tractor'", 
                data.get('type') == 'tractor',
                f"Stored type: {data.get('type')}")
    else:
        log_test("Test 4: POST vehicle type='Tır'", False, f"Status: {resp.status_code}, {resp.text}")
    
    # Test 5: POST with type='Dorse' (Turkish alias)
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "Dorse", "plate": "BTEST-5"}, 
                        headers=planlama_headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test_vehicles.append(data['id'])
        log_test("Test 5: POST vehicle type='Dorse' normalized to 'trailer'", 
                data.get('type') == 'trailer',
                f"Stored type: {data.get('type')}")
    else:
        log_test("Test 5: POST vehicle type='Dorse'", False, f"Status: {resp.status_code}, {resp.text}")
    
    # Test 6: POST with type='kamyon' (Turkish alias)
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "kamyon", "plate": "BTEST-6"}, 
                        headers=planlama_headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test_vehicles.append(data['id'])
        log_test("Test 6: POST vehicle type='kamyon' normalized to 'truck'", 
                data.get('type') == 'truck',
                f"Stored type: {data.get('type')}")
    else:
        log_test("Test 6: POST vehicle type='kamyon'", False, f"Status: {resp.status_code}, {resp.text}")
    
    # Test 7: POST with type='' (empty string, strict mode)
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "", "plate": "BTEST-7"}, 
                        headers=planlama_headers, timeout=10)
    passed = resp.status_code == 400
    log_test("Test 7: POST vehicle type='' (empty) returns 400", 
            passed,
            f"Status: {resp.status_code}")
    
    # Test 8: POST without type field
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"plate": "BTEST-8"}, 
                        headers=planlama_headers, timeout=10)
    passed = resp.status_code == 400
    log_test("Test 8: POST vehicle without type field returns 400", 
            passed,
            f"Status: {resp.status_code}")
    
    # Test 9: PUT with type='UFO' (invalid)
    if test_vehicles:
        vehicle_id = test_vehicles[0]
        resp = requests.put(f"{API_URL}/vehicles/{vehicle_id}", 
                           json={"type": "UFO"}, 
                           headers=planlama_headers, timeout=10)
        passed = resp.status_code == 400 and "Geçersiz araç tipi" in resp.text
        log_test("Test 9: PUT vehicle type='UFO' returns 400", 
                passed,
                f"Status: {resp.status_code}, Message: {resp.text[:100]}")
    else:
        log_test("Test 9: PUT vehicle type='UFO'", False, "No test vehicle available")
    
    # Test 10: PUT with type='Kamyonet' (Turkish alias)
    if test_vehicles:
        vehicle_id = test_vehicles[0]
        resp = requests.put(f"{API_URL}/vehicles/{vehicle_id}", 
                           json={"type": "Kamyonet"}, 
                           headers=planlama_headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            log_test("Test 10: PUT vehicle type='Kamyonet' normalized to 'van'", 
                    data.get('type') == 'van',
                    f"Stored type: {data.get('type')}")
        else:
            log_test("Test 10: PUT vehicle type='Kamyonet'", False, f"Status: {resp.status_code}, {resp.text}")
    else:
        log_test("Test 10: PUT vehicle type='Kamyonet'", False, "No test vehicle available")
    
    # Test 11: Migration check - all vehicles should have standard types
    resp = requests.get(f"{API_URL}/vehicles", headers=admin_headers, timeout=10)
    if resp.status_code == 200:
        vehicles = resp.json()
        standard_types = ['tractor', 'trailer', 'truck', 'van', 'panel_van', 'minibus', 'bus', 'pickup', 'other']
        invalid_types = [v for v in vehicles if v.get('type') not in standard_types]
        log_test("Test 11: Migration check - all vehicles have standard types", 
                len(invalid_types) == 0,
                f"Total vehicles: {len(vehicles)}, Invalid types: {len(invalid_types)}")
        if invalid_types:
            print(f"   Invalid vehicles: {invalid_types[:3]}")
    else:
        log_test("Test 11: Migration check", False, f"Status: {resp.status_code}")
    
    # Test 12: Non-arac_planlama roles get 403 on vehicle write endpoints
    if yukler_token and depo_token:
        yukler_headers = {"Authorization": f"Bearer {yukler_token}"}
        depo_headers = {"Authorization": f"Bearer {depo_token}"}
        
        # Test yukler POST
        resp1 = requests.post(f"{API_URL}/vehicles", 
                             json={"type": "truck", "plate": "FAIL-1"}, 
                             headers=yukler_headers, timeout=10)
        
        # Test depo POST
        resp2 = requests.post(f"{API_URL}/vehicles", 
                             json={"type": "truck", "plate": "FAIL-2"}, 
                             headers=depo_headers, timeout=10)
        
        passed = resp1.status_code == 403 and resp2.status_code == 403
        log_test("Test 12: Non-arac_planlama roles get 403 on POST /vehicles", 
                passed,
                f"yukler: {resp1.status_code}, depo: {resp2.status_code}")
    else:
        log_test("Test 12: Non-arac_planlama roles get 403", False, "Failed to get tokens")

def test_part_b_dorse_planning(admin_token, planlama_token):
    """Part B: Load Planning with Dorse"""
    print("\n" + "="*80)
    print("PART B: Load Planning with Dorse")
    print("="*80)
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    planlama_headers = {"Authorization": f"Bearer {planlama_token}"}
    
    # Setup: Create test vehicles (truck, tractor, trailer)
    truck_id = None
    tractor_id = None
    trailer_id = None
    driver_id = None
    company_id = None
    address_id = None
    load_id = None
    
    # Create truck
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "truck", "plate": "PTEST-TRUCK"}, 
                        headers=planlama_headers, timeout=10)
    if resp.status_code == 200:
        truck_id = resp.json()['id']
        test_vehicles.append(truck_id)
        print(f"✓ Created truck: {truck_id}")
    else:
        print(f"✗ Failed to create truck: {resp.status_code}")
    
    # Create tractor
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "tractor", "plate": "PTEST-TRACTOR"}, 
                        headers=planlama_headers, timeout=10)
    if resp.status_code == 200:
        tractor_id = resp.json()['id']
        test_vehicles.append(tractor_id)
        print(f"✓ Created tractor: {tractor_id}")
    else:
        print(f"✗ Failed to create tractor: {resp.status_code}")
    
    # Create trailer
    resp = requests.post(f"{API_URL}/vehicles", 
                        json={"type": "trailer", "plate": "PTEST-TRAILER"}, 
                        headers=planlama_headers, timeout=10)
    if resp.status_code == 200:
        trailer_id = resp.json()['id']
        test_vehicles.append(trailer_id)
        print(f"✓ Created trailer: {trailer_id}")
    else:
        print(f"✗ Failed to create trailer: {resp.status_code}")
    
    # Create driver
    resp = requests.post(f"{API_URL}/drivers", 
                        json={"name": "Test Driver", "phone": "905551234567"}, 
                        headers=planlama_headers, timeout=10)
    if resp.status_code == 200:
        driver_id = resp.json()['id']
        test_drivers.append(driver_id)
        print(f"✓ Created driver: {driver_id}")
    else:
        print(f"✗ Failed to create driver: {resp.status_code}")
    
    # Create company
    resp = requests.post(f"{API_URL}/companies", 
                        json={"name": "Test Company for Dorse"}, 
                        headers=admin_headers, timeout=10)
    if resp.status_code == 200:
        company_id = resp.json()['id']
        test_companies.append(company_id)
        print(f"✓ Created company: {company_id}")
    else:
        print(f"✗ Failed to create company: {resp.status_code}")
    
    # Create address
    if company_id:
        resp = requests.post(f"{API_URL}/addresses", 
                            json={"companyId": company_id, "name": "Test Address", "city": "Istanbul"}, 
                            headers=admin_headers, timeout=10)
        if resp.status_code == 200:
            address_id = resp.json()['id']
            test_addresses.append(address_id)
            print(f"✓ Created address: {address_id}")
        else:
            print(f"✗ Failed to create address: {resp.status_code}")
    
    # Create ic_nakliye load
    if company_id and address_id:
        resp = requests.post(f"{API_URL}/loads", 
                            json={
                                "companyId": company_id,
                                "addressId": address_id,
                                "shipmentType": "ic_nakliye",
                                "destCity": "Ankara",
                                "destCountry": "Türkiye"
                            }, 
                            headers=admin_headers, timeout=10)
        if resp.status_code == 200:
            load_id = resp.json()['id']
            test_loads.append(load_id)
            print(f"✓ Created load: {load_id}")
        else:
            print(f"✗ Failed to create load: {resp.status_code}")
    
    print()
    
    # Test 1: Plan with truck (no dorseId) -> 200, dorseId should be null
    if load_id and truck_id and driver_id:
        resp = requests.post(f"{API_URL}/loads/{load_id}/plan", 
                            json={
                                "vehicleId": truck_id,
                                "driverId": driver_id,
                                "plannedDateTime": "2024-01-15T10:00:00Z"
                            }, 
                            headers=planlama_headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            passed = data.get('dorseId') is None and data.get('vehicleId') == truck_id and data.get('status') == 'planned'
            log_test("Test 1: Plan with truck (no dorseId) -> dorseId=null, status=planned", 
                    passed,
                    f"dorseId: {data.get('dorseId')}, vehicleId: {data.get('vehicleId')}, status: {data.get('status')}")
            
            # Check statusHistory
            history = data.get('statusHistory', [])
            if len(history) >= 2:
                last_entry = history[-1]
                print(f"   StatusHistory last entry: status={last_entry.get('status')}, user={last_entry.get('user')}")
        else:
            log_test("Test 1: Plan with truck", False, f"Status: {resp.status_code}, {resp.text}")
    else:
        log_test("Test 1: Plan with truck", False, "Missing setup data")
    
    # Test 2: Plan with tractor (no dorseId) -> 400 "Çeker için dorse seçimi zorunludur"
    if load_id and tractor_id:
        resp = requests.post(f"{API_URL}/loads/{load_id}/plan", 
                            json={
                                "vehicleId": tractor_id,
                                "driverId": driver_id
                            }, 
                            headers=planlama_headers, timeout=10)
        passed = resp.status_code == 400 and "Çeker için dorse seçimi zorunludur" in resp.text
        log_test("Test 2: Plan with tractor (no dorseId) -> 400 with correct message", 
                passed,
                f"Status: {resp.status_code}, Message: {resp.text[:100]}")
    else:
        log_test("Test 2: Plan with tractor (no dorseId)", False, "Missing setup data")
    
    # Test 3: Plan with tractor + truck as dorseId -> 400 "Dorse alanında yalnızca dorse tipinde araç seçilebilir"
    if load_id and tractor_id and truck_id:
        resp = requests.post(f"{API_URL}/loads/{load_id}/plan", 
                            json={
                                "vehicleId": tractor_id,
                                "driverId": driver_id,
                                "dorseId": truck_id
                            }, 
                            headers=planlama_headers, timeout=10)
        passed = resp.status_code == 400 and "Dorse alanında yalnızca dorse tipinde araç seçilebilir" in resp.text
        log_test("Test 3: Plan with tractor + truck as dorseId -> 400 with correct message", 
                passed,
                f"Status: {resp.status_code}, Message: {resp.text[:100]}")
    else:
        log_test("Test 3: Plan with tractor + truck as dorseId", False, "Missing setup data")
    
    # Test 4: Plan with tractor + trailer -> 200, dorseId=trailerId
    if load_id and tractor_id and trailer_id:
        resp = requests.post(f"{API_URL}/loads/{load_id}/plan", 
                            json={
                                "vehicleId": tractor_id,
                                "driverId": driver_id,
                                "dorseId": trailer_id,
                                "plannedDateTime": "2024-01-15T14:00:00Z"
                            }, 
                            headers=planlama_headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            passed = data.get('dorseId') == trailer_id and data.get('vehicleId') == tractor_id
            log_test("Test 4: Plan with tractor + trailer -> dorseId=trailerId", 
                    passed,
                    f"dorseId: {data.get('dorseId')}, vehicleId: {data.get('vehicleId')}")
        else:
            log_test("Test 4: Plan with tractor + trailer", False, f"Status: {resp.status_code}, {resp.text}")
    else:
        log_test("Test 4: Plan with tractor + trailer", False, "Missing setup data")
    
    # Test 5: Plan with tractor + invalid dorseId -> 400 "Seçilen dorse bulunamadı"
    if load_id and tractor_id:
        resp = requests.post(f"{API_URL}/loads/{load_id}/plan", 
                            json={
                                "vehicleId": tractor_id,
                                "driverId": driver_id,
                                "dorseId": "not-a-real-uuid-xyz"
                            }, 
                            headers=planlama_headers, timeout=10)
        passed = resp.status_code == 400 and "Seçilen dorse bulunamadı" in resp.text
        log_test("Test 5: Plan with tractor + invalid dorseId -> 400 with correct message", 
                passed,
                f"Status: {resp.status_code}, Message: {resp.text[:100]}")
    else:
        log_test("Test 5: Plan with tractor + invalid dorseId", False, "Missing setup data")
    
    # Test 6: Re-plan with truck + dorseId (non-tractor with dorseId) -> 200, dorseId ignored (null)
    if load_id and truck_id and trailer_id:
        resp = requests.post(f"{API_URL}/loads/{load_id}/plan", 
                            json={
                                "vehicleId": truck_id,
                                "driverId": driver_id,
                                "dorseId": trailer_id
                            }, 
                            headers=planlama_headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            passed = data.get('dorseId') is None and data.get('vehicleId') == truck_id
            log_test("Test 6: Re-plan with truck + dorseId -> dorseId ignored (null)", 
                    passed,
                    f"dorseId: {data.get('dorseId')}, vehicleId: {data.get('vehicleId')}")
        else:
            log_test("Test 6: Re-plan with truck + dorseId", False, f"Status: {resp.status_code}, {resp.text}")
    else:
        log_test("Test 6: Re-plan with truck + dorseId", False, "Missing setup data")
    
    # Test 7: Plan with invalid vehicleId -> 400 "Seçilen araç bulunamadı"
    if load_id:
        resp = requests.post(f"{API_URL}/loads/{load_id}/plan", 
                            json={
                                "vehicleId": "not-a-real-uuid-xyz",
                                "driverId": driver_id
                            }, 
                            headers=planlama_headers, timeout=10)
        passed = resp.status_code == 400 and "Seçilen araç bulunamadı" in resp.text
        log_test("Test 7: Plan with invalid vehicleId -> 400 with correct message", 
                passed,
                f"Status: {resp.status_code}, Message: {resp.text[:100]}")
    else:
        log_test("Test 7: Plan with invalid vehicleId", False, "Missing setup data")
    
    # Test 8: Verify load status is 'planned' after successful plan
    if load_id:
        resp = requests.get(f"{API_URL}/loads/{load_id}", headers=admin_headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            passed = data.get('status') == 'planned'
            log_test("Test 8: Load status is 'planned' after successful plan", 
                    passed,
                    f"Status: {data.get('status')}")
        else:
            log_test("Test 8: Verify load status", False, f"Status: {resp.status_code}")
    else:
        log_test("Test 8: Verify load status", False, "Missing load_id")
    
    # Test 9: Verify statusHistory has new entry with current user's name
    if load_id:
        resp = requests.get(f"{API_URL}/loads/{load_id}", headers=admin_headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            history = data.get('statusHistory', [])
            if len(history) > 0:
                last_entry = history[-1]
                # Should have user name from planlama token
                passed = last_entry.get('status') == 'planned' and last_entry.get('user') is not None
                log_test("Test 9: StatusHistory has new 'planned' entry with user name", 
                        passed,
                        f"Last entry: status={last_entry.get('status')}, user={last_entry.get('user')}")
            else:
                log_test("Test 9: StatusHistory check", False, "No history entries")
        else:
            log_test("Test 9: StatusHistory check", False, f"Status: {resp.status_code}")
    else:
        log_test("Test 9: StatusHistory check", False, "Missing load_id")

def main():
    print("="*80)
    print("YükTakip Backend Test: Vehicle Types + Tractor/Trailer Planning")
    print("="*80)
    print(f"API URL: {API_URL}\n")
    
    # Login as admin and planlama
    print("Logging in...")
    admin_token = login("admin@yuktakip.local", "admin123")
    if not admin_token:
        admin_token = login("admin", "admin123")
    
    planlama_token = login("planlama", "1234")
    
    if not admin_token or not planlama_token:
        print("❌ Failed to login. Cannot proceed with tests.")
        sys.exit(1)
    
    print(f"✓ Admin token: {admin_token[:20]}...")
    print(f"✓ Planlama token: {planlama_token[:20]}...\n")
    
    # Part C: Count initial data
    print("="*80)
    print("PART C: Data Preservation - Initial Count")
    print("="*80)
    initial_counts = count_data(admin_token)
    print(f"Initial counts:")
    print(f"  Vehicles: {initial_counts.get('vehicles', 0)}")
    print(f"  Drivers: {initial_counts.get('drivers', 0)}")
    print(f"  Loads: {initial_counts.get('loads', 0)}")
    print(f"  Companies: {initial_counts.get('companies', 0)}")
    print(f"  Addresses: {initial_counts.get('addresses', 0)}")
    
    # Run tests
    try:
        test_part_a_vehicle_types(admin_token, planlama_token)
        test_part_b_dorse_planning(admin_token, planlama_token)
    except Exception as e:
        print(f"\n❌ Test execution error: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    print("\n" + "="*80)
    print("Cleaning up test data...")
    print("="*80)
    cleanup_test_data(admin_token, planlama_token)
    print(f"Deleted {len(test_loads)} loads, {len(test_vehicles)} vehicles, {len(test_drivers)} drivers")
    print(f"Deleted {len(test_addresses)} addresses, {len(test_companies)} companies")
    
    # Part C: Verify final counts
    print("\n" + "="*80)
    print("PART C: Data Preservation - Final Count")
    print("="*80)
    final_counts = count_data(admin_token)
    print(f"Final counts:")
    print(f"  Vehicles: {final_counts.get('vehicles', 0)}")
    print(f"  Drivers: {final_counts.get('drivers', 0)}")
    print(f"  Loads: {final_counts.get('loads', 0)}")
    print(f"  Companies: {final_counts.get('companies', 0)}")
    print(f"  Addresses: {final_counts.get('addresses', 0)}")
    
    # Verify preservation
    preservation_ok = True
    for key in initial_counts:
        if initial_counts[key] != final_counts.get(key, 0):
            preservation_ok = False
            print(f"⚠️  {key}: initial={initial_counts[key]}, final={final_counts.get(key, 0)}")
    
    if preservation_ok:
        print("✅ Data preservation verified: all counts match")
    else:
        print("❌ Data preservation failed: counts do not match")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"Total: {tests_passed + tests_failed}")
    
    if tests_failed == 0 and preservation_ok:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed or data preservation issue")
        sys.exit(1)

if __name__ == "__main__":
    main()
