#!/usr/bin/env python3
"""
Backend API Test Suite for YükTakip
Tests all CRUD endpoints and special load workflow endpoints
"""
import requests
import json
from datetime import datetime

# Base URL from .env
BASE_URL = "https://load-management-6.preview.emergentagent.com/api"

def print_test(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"   {details}")
    print()

def test_seed_reset():
    """Test 1: Seed endpoint resets data"""
    print("=" * 60)
    print("TEST 1: Seed Reset")
    print("=" * 60)
    
    try:
        # First seed
        resp = requests.post(f"{BASE_URL}/seed", timeout=10)
        print(f"First seed status: {resp.status_code}")
        data = resp.json()
        print(f"Response: {data}")
        
        passed = resp.status_code == 200 and data.get('ok') == True
        print_test("POST /api/seed returns {ok:true}", passed, f"Status: {resp.status_code}, Data: {data}")
        
        # Second seed (should reset)
        resp2 = requests.post(f"{BASE_URL}/seed", timeout=10)
        data2 = resp2.json()
        passed2 = resp2.status_code == 200 and data2.get('ok') == True
        print_test("POST /api/seed reruns successfully (reset)", passed2, f"Status: {resp2.status_code}")
        
        return passed and passed2
    except Exception as e:
        print_test("Seed endpoint", False, f"Exception: {str(e)}")
        return False

def test_companies_crud():
    """Test 2: Companies CRUD + cascade delete"""
    print("=" * 60)
    print("TEST 2: Companies CRUD")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # GET list
        resp = requests.get(f"{BASE_URL}/companies", timeout=10)
        companies = resp.json()
        print(f"GET /api/companies returned {len(companies)} companies")
        passed = resp.status_code == 200 and isinstance(companies, list)
        print_test("GET /api/companies (list)", passed, f"Count: {len(companies)}")
        all_passed = all_passed and passed
        
        # Verify no _id in response
        if companies and '_id' in companies[0]:
            print_test("Companies response has no _id (UUID only)", False, "Found _id in response")
            all_passed = False
        else:
            print_test("Companies response has no _id (UUID only)", True, "Clean UUID response")
        
        # POST create
        new_company = {
            "name": "Test Şirketi A.Ş.",
            "phone": "02121112233",
            "email": "test@test.com",
            "active": True
        }
        resp = requests.post(f"{BASE_URL}/companies", json=new_company, timeout=10)
        created = resp.json()
        print(f"POST /api/companies response: {created}")
        passed = resp.status_code == 200 and 'id' in created and created['name'] == new_company['name']
        print_test("POST /api/companies creates company with UUID id", passed, f"ID: {created.get('id', 'N/A')}")
        all_passed = all_passed and passed
        company_id = created.get('id')
        
        # Create an address for this company (for cascade test)
        if company_id:
            addr = {
                "companyId": company_id,
                "name": "Test Adres",
                "address": "Test Sokak No:1",
                "city": "İstanbul",
                "district": "Kadıköy",
                "phone": "02121112233",
                "contact": "Test Kişi",
                "coordinate": ""
            }
            resp = requests.post(f"{BASE_URL}/addresses", json=addr, timeout=10)
            addr_created = resp.json()
            print(f"Created test address for cascade: {addr_created.get('id')}")
        
        # PUT update
        if company_id:
            update_data = {"name": "Test Şirketi UPDATED", "phone": "02129999999"}
            resp = requests.put(f"{BASE_URL}/companies/{company_id}", json=update_data, timeout=10)
            updated = resp.json()
            passed = resp.status_code == 200 and updated.get('name') == "Test Şirketi UPDATED"
            print_test("PUT /api/companies/:id updates", passed, f"New name: {updated.get('name')}")
            all_passed = all_passed and passed
        
        # DELETE (cascade test)
        if company_id:
            resp = requests.delete(f"{BASE_URL}/companies/{company_id}", timeout=10)
            del_result = resp.json()
            passed = resp.status_code == 200 and del_result.get('ok') == True
            print_test("DELETE /api/companies/:id", passed, f"Result: {del_result}")
            all_passed = all_passed and passed
            
            # Verify addresses were cascade deleted
            resp = requests.get(f"{BASE_URL}/addresses?companyId={company_id}", timeout=10)
            addrs = resp.json()
            passed = resp.status_code == 200 and len(addrs) == 0
            print_test("Cascade delete: addresses removed", passed, f"Addresses for deleted company: {len(addrs)}")
            all_passed = all_passed and passed
        
        return all_passed
    except Exception as e:
        print_test("Companies CRUD", False, f"Exception: {str(e)}")
        return False

def test_addresses_crud():
    """Test 3: Addresses CRUD + filter by companyId"""
    print("=" * 60)
    print("TEST 3: Company Addresses CRUD")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # Get a company first
        resp = requests.get(f"{BASE_URL}/companies", timeout=10)
        companies = resp.json()
        if not companies:
            print_test("Addresses CRUD", False, "No companies found for testing")
            return False
        company_id = companies[0]['id']
        print(f"Using company ID: {company_id}")
        
        # GET all addresses
        resp = requests.get(f"{BASE_URL}/addresses", timeout=10)
        all_addrs = resp.json()
        passed = resp.status_code == 200 and isinstance(all_addrs, list)
        print_test("GET /api/addresses (all)", passed, f"Count: {len(all_addrs)}")
        all_passed = all_passed and passed
        
        # GET filtered by companyId
        resp = requests.get(f"{BASE_URL}/addresses?companyId={company_id}", timeout=10)
        filtered = resp.json()
        passed = resp.status_code == 200 and isinstance(filtered, list)
        print_test("GET /api/addresses?companyId=X (filter)", passed, f"Filtered count: {len(filtered)}")
        all_passed = all_passed and passed
        
        # POST create
        new_addr = {
            "companyId": company_id,
            "name": "Test Depo",
            "address": "Test Cad. No:42",
            "city": "Ankara",
            "district": "Çankaya",
            "phone": "03121234567",
            "contact": "Ahmet Test",
            "coordinate": "39.9334,32.8597"
        }
        resp = requests.post(f"{BASE_URL}/addresses", json=new_addr, timeout=10)
        created = resp.json()
        passed = resp.status_code == 200 and 'id' in created and created['companyId'] == company_id
        print_test("POST /api/addresses creates address", passed, f"ID: {created.get('id')}")
        all_passed = all_passed and passed
        addr_id = created.get('id')
        
        # PUT update
        if addr_id:
            update_data = {"name": "Test Depo UPDATED", "city": "İzmir"}
            resp = requests.put(f"{BASE_URL}/addresses/{addr_id}", json=update_data, timeout=10)
            updated = resp.json()
            passed = resp.status_code == 200 and updated.get('name') == "Test Depo UPDATED"
            print_test("PUT /api/addresses/:id updates", passed, f"New name: {updated.get('name')}")
            all_passed = all_passed and passed
        
        # DELETE
        if addr_id:
            resp = requests.delete(f"{BASE_URL}/addresses/{addr_id}", timeout=10)
            del_result = resp.json()
            passed = resp.status_code == 200 and del_result.get('ok') == True
            print_test("DELETE /api/addresses/:id", passed, f"Result: {del_result}")
            all_passed = all_passed and passed
        
        return all_passed
    except Exception as e:
        print_test("Addresses CRUD", False, f"Exception: {str(e)}")
        return False

def test_drivers_crud():
    """Test 4: Drivers CRUD"""
    print("=" * 60)
    print("TEST 4: Drivers CRUD")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # GET list
        resp = requests.get(f"{BASE_URL}/drivers", timeout=10)
        drivers = resp.json()
        passed = resp.status_code == 200 and isinstance(drivers, list)
        print_test("GET /api/drivers (list)", passed, f"Count: {len(drivers)}")
        all_passed = all_passed and passed
        
        # POST create
        new_driver = {
            "name": "Mehmet Test Sürücü",
            "phone": "905551234567",
            "active": True
        }
        resp = requests.post(f"{BASE_URL}/drivers", json=new_driver, timeout=10)
        created = resp.json()
        passed = resp.status_code == 200 and 'id' in created and created['name'] == new_driver['name']
        print_test("POST /api/drivers creates driver", passed, f"ID: {created.get('id')}")
        all_passed = all_passed and passed
        driver_id = created.get('id')
        
        # PUT update
        if driver_id:
            update_data = {"name": "Mehmet UPDATED", "active": False}
            resp = requests.put(f"{BASE_URL}/drivers/{driver_id}", json=update_data, timeout=10)
            updated = resp.json()
            passed = resp.status_code == 200 and updated.get('name') == "Mehmet UPDATED"
            print_test("PUT /api/drivers/:id updates", passed, f"New name: {updated.get('name')}")
            all_passed = all_passed and passed
        
        # DELETE
        if driver_id:
            resp = requests.delete(f"{BASE_URL}/drivers/{driver_id}", timeout=10)
            del_result = resp.json()
            passed = resp.status_code == 200 and del_result.get('ok') == True
            print_test("DELETE /api/drivers/:id", passed, f"Result: {del_result}")
            all_passed = all_passed and passed
        
        return all_passed
    except Exception as e:
        print_test("Drivers CRUD", False, f"Exception: {str(e)}")
        return False

def test_vehicles_crud():
    """Test 5: Vehicles CRUD"""
    print("=" * 60)
    print("TEST 5: Vehicles CRUD")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # GET list
        resp = requests.get(f"{BASE_URL}/vehicles", timeout=10)
        vehicles = resp.json()
        passed = resp.status_code == 200 and isinstance(vehicles, list)
        print_test("GET /api/vehicles (list)", passed, f"Count: {len(vehicles)}")
        all_passed = all_passed and passed
        
        # POST create
        new_vehicle = {
            "type": "Kamyon",
            "plate": "34 TEST 999",
            "active": True
        }
        resp = requests.post(f"{BASE_URL}/vehicles", json=new_vehicle, timeout=10)
        created = resp.json()
        passed = resp.status_code == 200 and 'id' in created and created['plate'] == new_vehicle['plate']
        print_test("POST /api/vehicles creates vehicle", passed, f"ID: {created.get('id')}")
        all_passed = all_passed and passed
        vehicle_id = created.get('id')
        
        # PUT update
        if vehicle_id:
            update_data = {"type": "Tır", "plate": "06 TEST 888"}
            resp = requests.put(f"{BASE_URL}/vehicles/{vehicle_id}", json=update_data, timeout=10)
            updated = resp.json()
            passed = resp.status_code == 200 and updated.get('plate') == "06 TEST 888"
            print_test("PUT /api/vehicles/:id updates", passed, f"New plate: {updated.get('plate')}")
            all_passed = all_passed and passed
        
        # DELETE
        if vehicle_id:
            resp = requests.delete(f"{BASE_URL}/vehicles/{vehicle_id}", timeout=10)
            del_result = resp.json()
            passed = resp.status_code == 200 and del_result.get('ok') == True
            print_test("DELETE /api/vehicles/:id", passed, f"Result: {del_result}")
            all_passed = all_passed and passed
        
        return all_passed
    except Exception as e:
        print_test("Vehicles CRUD", False, f"Exception: {str(e)}")
        return False

def test_loads_crud_and_workflow():
    """Test 6: Loads CRUD + status transitions + planning (CRITICAL)"""
    print("=" * 60)
    print("TEST 6: Loads CRUD & Workflow (CRITICAL)")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # Get prerequisites
        companies = requests.get(f"{BASE_URL}/companies", timeout=10).json()
        addresses = requests.get(f"{BASE_URL}/addresses", timeout=10).json()
        drivers = requests.get(f"{BASE_URL}/drivers", timeout=10).json()
        vehicles = requests.get(f"{BASE_URL}/vehicles", timeout=10).json()
        
        if not companies or not addresses or not drivers or not vehicles:
            print_test("Loads workflow", False, "Missing prerequisites (companies/addresses/drivers/vehicles)")
            return False
        
        company_id = companies[0]['id']
        address_id = addresses[0]['id']
        driver_id = drivers[0]['id']
        vehicle_id = vehicles[0]['id']
        
        print(f"Using: company={company_id}, address={address_id}, driver={driver_id}, vehicle={vehicle_id}")
        
        # Test 6a: POST load with shipmentType='ic_nakliye' -> status='planning'
        load_ic = {
            "companyId": company_id,
            "addressId": address_id,
            "shipmentType": "ic_nakliye",
            "phone": "905551234567",
            "packages": "10 koli",
            "kg": "500",
            "m3": "2.5",
            "dimensions": "120x80x100",
            "destCity": "Ankara",
            "destCountry": "Türkiye",
            "note": "Test yük - iç nakliye",
            "user": "test_user"
        }
        resp = requests.post(f"{BASE_URL}/loads", json=load_ic, timeout=10)
        load1 = resp.json()
        print(f"Created ic_nakliye load: {load1.get('id')}, status: {load1.get('status')}")
        
        passed = (resp.status_code == 200 and 
                 'id' in load1 and 
                 load1.get('status') == 'planning' and
                 'statusHistory' in load1 and
                 len(load1['statusHistory']) == 1 and
                 load1['statusHistory'][0]['status'] == 'planning')
        print_test("POST /api/loads with shipmentType='ic_nakliye' -> status='planning'", 
                  passed, 
                  f"Status: {load1.get('status')}, History entries: {len(load1.get('statusHistory', []))}")
        all_passed = all_passed and passed
        load1_id = load1.get('id')
        
        # Test 6b: POST load with shipmentType='musteri_kendisi' -> status='created'
        load_mk = {
            "companyId": company_id,
            "addressId": address_id,
            "shipmentType": "musteri_kendisi",
            "phone": "905559876543",
            "packages": "5 palet",
            "kg": "1000",
            "m3": "5",
            "dimensions": "200x120x150",
            "destCity": "İzmir",
            "destCountry": "Türkiye",
            "note": "Test yük - müşteri kendisi",
            "user": "test_user"
        }
        resp = requests.post(f"{BASE_URL}/loads", json=load_mk, timeout=10)
        load2 = resp.json()
        print(f"Created musteri_kendisi load: {load2.get('id')}, status: {load2.get('status')}")
        
        passed = (resp.status_code == 200 and 
                 'id' in load2 and 
                 load2.get('status') == 'created' and
                 len(load2.get('statusHistory', [])) == 1)
        print_test("POST /api/loads with shipmentType='musteri_kendisi' -> status='created'", 
                  passed,
                  f"Status: {load2.get('status')}, History entries: {len(load2.get('statusHistory', []))}")
        all_passed = all_passed and passed
        load2_id = load2.get('id')
        
        # Test 6c: GET /api/loads (list)
        resp = requests.get(f"{BASE_URL}/loads", timeout=10)
        loads_list = resp.json()
        passed = resp.status_code == 200 and isinstance(loads_list, list) and len(loads_list) >= 2
        print_test("GET /api/loads returns list", passed, f"Count: {len(loads_list)}")
        all_passed = all_passed and passed
        
        # Test 6d: GET /api/loads/:id (single)
        if load1_id:
            resp = requests.get(f"{BASE_URL}/loads/{load1_id}", timeout=10)
            single_load = resp.json()
            passed = resp.status_code == 200 and single_load.get('id') == load1_id
            print_test("GET /api/loads/:id returns single load", passed, f"ID: {single_load.get('id')}")
            all_passed = all_passed and passed
        
        # Test 6e: PUT /api/loads/:id (should NOT modify statusHistory or createdAt)
        if load1_id:
            original_history = load1.get('statusHistory', [])
            original_created = load1.get('createdAt')
            
            update_data = {
                "note": "UPDATED NOTE",
                "kg": "600",
                "statusHistory": [{"fake": "data"}],  # Should be ignored
                "createdAt": "2020-01-01T00:00:00Z"  # Should be ignored
            }
            resp = requests.put(f"{BASE_URL}/loads/{load1_id}", json=update_data, timeout=10)
            updated_load = resp.json()
            
            passed = (resp.status_code == 200 and 
                     updated_load.get('note') == "UPDATED NOTE" and
                     updated_load.get('kg') == "600" and
                     updated_load.get('statusHistory') == original_history and
                     updated_load.get('createdAt') == original_created)
            print_test("PUT /api/loads/:id updates fields but preserves statusHistory & createdAt", 
                      passed,
                      f"Note updated: {updated_load.get('note') == 'UPDATED NOTE'}, History preserved: {updated_load.get('statusHistory') == original_history}")
            all_passed = all_passed and passed
        
        # Test 6f: POST /api/loads/:id/plan (assign driver/vehicle -> status='planned')
        if load1_id:
            plan_data = {
                "driverId": driver_id,
                "vehicleId": vehicle_id,
                "plannedDateTime": "2024-12-20T14:00:00Z",
                "user": "test_planner"
            }
            resp = requests.post(f"{BASE_URL}/loads/{load1_id}/plan", json=plan_data, timeout=10)
            planned_load = resp.json()
            
            passed = (resp.status_code == 200 and
                     planned_load.get('status') == 'planned' and
                     planned_load.get('driverId') == driver_id and
                     planned_load.get('vehicleId') == vehicle_id and
                     len(planned_load.get('statusHistory', [])) == 2 and
                     planned_load['statusHistory'][-1]['status'] == 'planned')
            print_test("POST /api/loads/:id/plan sets status='planned' & appends history", 
                      passed,
                      f"Status: {planned_load.get('status')}, History entries: {len(planned_load.get('statusHistory', []))}, Driver: {planned_load.get('driverId')}")
            all_passed = all_passed and passed
        
        # Test 6g: POST /api/loads/:id/status (change status with note)
        if load1_id:
            status_data = {
                "status": "in_transit",
                "note": "Yük yola çıktı",
                "user": "test_dispatcher"
            }
            resp = requests.post(f"{BASE_URL}/loads/{load1_id}/status", json=status_data, timeout=10)
            status_changed = resp.json()
            
            passed = (resp.status_code == 200 and
                     status_changed.get('status') == 'in_transit' and
                     len(status_changed.get('statusHistory', [])) == 3 and
                     status_changed['statusHistory'][-1]['status'] == 'in_transit' and
                     status_changed['statusHistory'][-1]['note'] == "Yük yola çıktı")
            print_test("POST /api/loads/:id/status changes status & appends history", 
                      passed,
                      f"Status: {status_changed.get('status')}, History entries: {len(status_changed.get('statusHistory', []))}")
            all_passed = all_passed and passed
        
        # Test 6h: POST /api/loads/:id/status with invalid status -> 400
        if load1_id:
            invalid_status = {
                "status": "invalid_status_xyz",
                "note": "Should fail",
                "user": "test_user"
            }
            resp = requests.post(f"{BASE_URL}/loads/{load1_id}/status", json=invalid_status, timeout=10)
            passed = resp.status_code == 400
            print_test("POST /api/loads/:id/status with invalid status returns 400", 
                      passed,
                      f"Status code: {resp.status_code}")
            all_passed = all_passed and passed
        
        # Test 6i: DELETE /api/loads/:id
        if load2_id:
            resp = requests.delete(f"{BASE_URL}/loads/{load2_id}", timeout=10)
            del_result = resp.json()
            passed = resp.status_code == 200 and del_result.get('ok') == True
            print_test("DELETE /api/loads/:id", passed, f"Result: {del_result}")
            all_passed = all_passed and passed
        
        return all_passed
    except Exception as e:
        print_test("Loads CRUD & Workflow", False, f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard():
    """Test 7: Dashboard counts"""
    print("=" * 60)
    print("TEST 7: Dashboard Counts")
    print("=" * 60)
    
    try:
        # Get dashboard
        resp = requests.get(f"{BASE_URL}/dashboard", timeout=10)
        dashboard = resp.json()
        print(f"Dashboard response: {dashboard}")
        
        # Verify structure
        required_keys = ['total', 'pending', 'planning', 'planned', 'delivered']
        has_all_keys = all(key in dashboard for key in required_keys)
        
        passed = resp.status_code == 200 and has_all_keys
        print_test("GET /api/dashboard returns correct structure", 
                  passed,
                  f"Keys: {list(dashboard.keys())}")
        
        # Verify counts are numbers
        all_numbers = all(isinstance(dashboard.get(key), int) for key in required_keys)
        print_test("Dashboard counts are integers", all_numbers, f"Values: {dashboard}")
        
        # Get actual loads to verify counts
        loads_resp = requests.get(f"{BASE_URL}/loads", timeout=10)
        loads = loads_resp.json()
        
        actual_total = len(loads)
        actual_pending = len([l for l in loads if l.get('status') == 'created'])
        actual_planning = len([l for l in loads if l.get('status') == 'planning'])
        actual_planned = len([l for l in loads if l.get('status') in ['planned', 'in_transit']])
        actual_delivered = len([l for l in loads if l.get('status') in ['delivered', 'shipped']])
        
        print(f"Expected counts: total={actual_total}, pending={actual_pending}, planning={actual_planning}, planned={actual_planned}, delivered={actual_delivered}")
        print(f"Dashboard counts: total={dashboard.get('total')}, pending={dashboard.get('pending')}, planning={dashboard.get('planning')}, planned={dashboard.get('planned')}, delivered={dashboard.get('delivered')}")
        
        counts_match = (dashboard.get('total') == actual_total and
                       dashboard.get('pending') == actual_pending and
                       dashboard.get('planning') == actual_planning and
                       dashboard.get('planned') == actual_planned and
                       dashboard.get('delivered') == actual_delivered)
        
        print_test("Dashboard counts match actual load statuses", 
                  counts_match,
                  f"Match: {counts_match}")
        
        return passed and all_numbers and counts_match
    except Exception as e:
        print_test("Dashboard", False, f"Exception: {str(e)}")
        return False

def main():
    print("\n" + "=" * 60)
    print("YükTakip Backend API Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Database: yuktakip")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Run all tests in sequence
    results['seed'] = test_seed_reset()
    results['companies'] = test_companies_crud()
    results['addresses'] = test_addresses_crud()
    results['drivers'] = test_drivers_crud()
    results['vehicles'] = test_vehicles_crud()
    results['loads'] = test_loads_crud_and_workflow()
    results['dashboard'] = test_dashboard()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed_count = sum(1 for p in results.values() if p)
    print(f"\nTotal: {passed_count}/{total} tests passed")
    print("=" * 60 + "\n")
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
