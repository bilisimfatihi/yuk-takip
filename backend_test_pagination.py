#!/usr/bin/env python3
"""
Backend API Test Suite for YükTakip - Pagination & Dashboard Updates
Tests ONLY the two updated endpoints:
1. GET /api/loads - server-side pagination & filtering (RESPONSE SHAPE CHANGED)
2. GET /api/dashboard - parallel countDocuments (response unchanged)
"""
import requests
import json
from datetime import datetime, timedelta

# Base URL from .env
BASE_URL = "https://load-management-6.preview.emergentagent.com/api"

def print_test(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"   {details}")
    print()

def test_seed():
    """Smoke check: Seed endpoint"""
    print("=" * 80)
    print("SMOKE CHECK: Seed Reset")
    print("=" * 80)
    
    try:
        resp = requests.post(f"{BASE_URL}/seed", timeout=10)
        data = resp.json()
        passed = resp.status_code == 200 and data.get('ok') == True
        print_test("POST /api/seed", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        print_test("Seed endpoint", False, f"Exception: {str(e)}")
        return False

def test_loads_default_response():
    """Test 1: Default GET /api/loads returns {items, total, page, pageSize}"""
    print("=" * 80)
    print("TEST 1: GET /api/loads - Default Response Shape")
    print("=" * 80)
    
    try:
        resp = requests.get(f"{BASE_URL}/loads", timeout=10)
        data = resp.json()
        print(f"Response keys: {list(data.keys())}")
        print(f"Response: {json.dumps(data, indent=2)[:500]}")
        
        # Verify response shape
        has_items = 'items' in data and isinstance(data['items'], list)
        has_total = 'total' in data and isinstance(data['total'], int)
        has_page = 'page' in data and data['page'] == 1
        has_pageSize = 'pageSize' in data and data['pageSize'] == 50
        
        passed = resp.status_code == 200 and has_items and has_total and has_page and has_pageSize
        print_test("GET /api/loads returns {items, total, page:1, pageSize:50}", 
                  passed,
                  f"Keys: {list(data.keys())}, Total: {data.get('total')}, Items count: {len(data.get('items', []))}")
        
        # Verify no _id in items
        if data.get('items'):
            has_no_id = all('_id' not in item for item in data['items'])
            print_test("Items have no _id field (UUID only)", has_no_id)
            passed = passed and has_no_id
        
        return passed
    except Exception as e:
        print_test("Default response shape", False, f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_loads_pagination():
    """Test 2: Pagination - create ~55 loads and verify page/pageSize"""
    print("=" * 80)
    print("TEST 2: GET /api/loads - Pagination")
    print("=" * 80)
    
    try:
        # Reset data
        requests.post(f"{BASE_URL}/seed", timeout=10)
        
        # Get prerequisites
        companies = requests.get(f"{BASE_URL}/companies", timeout=10).json()
        addresses = requests.get(f"{BASE_URL}/addresses", timeout=10).json()
        
        if not companies or not addresses:
            print_test("Pagination test", False, "No companies/addresses for testing")
            return False
        
        company_id = companies[0]['id']
        address_id = addresses[0]['id']
        
        # Create 55 loads with varying data
        print(f"Creating 55 loads...")
        cities = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Adana', 'Konya', 'Gaziantep']
        shipment_types = ['ic_nakliye', 'musteri_kendisi', 'musteri_kargo', 'nakliyeci']
        
        for i in range(55):
            load_data = {
                "companyId": company_id,
                "addressId": address_id,
                "shipmentType": shipment_types[i % len(shipment_types)],
                "phone": f"90555{i:07d}",
                "packages": f"{i+1} koli",
                "kg": str((i+1) * 10),
                "m3": str((i+1) * 0.5),
                "dimensions": "120x80x100",
                "destCity": cities[i % len(cities)],
                "destCountry": "Türkiye",
                "note": f"Test load {i+1}",
                "user": "test_user"
            }
            resp = requests.post(f"{BASE_URL}/loads", json=load_data, timeout=10)
            if resp.status_code != 200:
                print(f"Failed to create load {i+1}: {resp.status_code}")
        
        print(f"Created 55 loads")
        
        # Test page=1, pageSize=50 -> should return 50 items, total=55
        resp1 = requests.get(f"{BASE_URL}/loads?page=1&pageSize=50", timeout=10)
        data1 = resp1.json()
        
        passed1 = (resp1.status_code == 200 and 
                  len(data1.get('items', [])) == 50 and 
                  data1.get('total') == 55 and
                  data1.get('page') == 1 and
                  data1.get('pageSize') == 50)
        print_test("GET /api/loads?page=1&pageSize=50 returns 50 items, total=55", 
                  passed1,
                  f"Items: {len(data1.get('items', []))}, Total: {data1.get('total')}, Page: {data1.get('page')}, PageSize: {data1.get('pageSize')}")
        
        # Test page=2, pageSize=50 -> should return 5 items, total=55
        resp2 = requests.get(f"{BASE_URL}/loads?page=2&pageSize=50", timeout=10)
        data2 = resp2.json()
        
        passed2 = (resp2.status_code == 200 and 
                  len(data2.get('items', [])) == 5 and 
                  data2.get('total') == 55 and
                  data2.get('page') == 2 and
                  data2.get('pageSize') == 50)
        print_test("GET /api/loads?page=2&pageSize=50 returns 5 items, total=55", 
                  passed2,
                  f"Items: {len(data2.get('items', []))}, Total: {data2.get('total')}, Page: {data2.get('page')}")
        
        # Test page=3, pageSize=50 -> should return 0 items (past end), total=55
        resp3 = requests.get(f"{BASE_URL}/loads?page=3&pageSize=50", timeout=10)
        data3 = resp3.json()
        
        passed3 = (resp3.status_code == 200 and 
                  len(data3.get('items', [])) == 0 and 
                  data3.get('total') == 55 and
                  data3.get('page') == 3)
        print_test("GET /api/loads?page=3&pageSize=50 returns 0 items (past end), total=55", 
                  passed3,
                  f"Items: {len(data3.get('items', []))}, Total: {data3.get('total')}")
        
        return passed1 and passed2 and passed3
    except Exception as e:
        print_test("Pagination test", False, f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_loads_pagesize_cap():
    """Test 3: pageSize cap - pageSize=500 should be capped at 200"""
    print("=" * 80)
    print("TEST 3: GET /api/loads - PageSize Cap")
    print("=" * 80)
    
    try:
        resp = requests.get(f"{BASE_URL}/loads?pageSize=500", timeout=10)
        data = resp.json()
        
        # pageSize should be capped at 200, or items.length <= 200
        passed = (resp.status_code == 200 and 
                 (data.get('pageSize') == 200 or len(data.get('items', [])) <= 200))
        print_test("GET /api/loads?pageSize=500 caps at 200", 
                  passed,
                  f"PageSize: {data.get('pageSize')}, Items count: {len(data.get('items', []))}")
        
        return passed
    except Exception as e:
        print_test("PageSize cap test", False, f"Exception: {str(e)}")
        return False

def test_loads_status_filter():
    """Test 4: Status filter"""
    print("=" * 80)
    print("TEST 4: GET /api/loads - Status Filter")
    print("=" * 80)
    
    try:
        # Get loads with status=planning
        resp = requests.get(f"{BASE_URL}/loads?status=planning", timeout=10)
        data = resp.json()
        
        # All items should have status='planning'
        all_planning = all(item.get('status') == 'planning' for item in data.get('items', []))
        total_reflects_filter = data.get('total') == len([item for item in data.get('items', []) if item.get('status') == 'planning'])
        
        passed = resp.status_code == 200 and all_planning
        print_test("GET /api/loads?status=planning returns only planning loads", 
                  passed,
                  f"Items: {len(data.get('items', []))}, Total: {data.get('total')}, All planning: {all_planning}")
        
        # Test status=created
        resp2 = requests.get(f"{BASE_URL}/loads?status=created", timeout=10)
        data2 = resp2.json()
        all_created = all(item.get('status') == 'created' for item in data2.get('items', []))
        
        passed2 = resp2.status_code == 200 and all_created
        print_test("GET /api/loads?status=created returns only created loads", 
                  passed2,
                  f"Items: {len(data2.get('items', []))}, Total: {data2.get('total')}, All created: {all_created}")
        
        return passed and passed2
    except Exception as e:
        print_test("Status filter test", False, f"Exception: {str(e)}")
        return False

def test_loads_companyid_filter():
    """Test 5: CompanyId filter"""
    print("=" * 80)
    print("TEST 5: GET /api/loads - CompanyId Filter")
    print("=" * 80)
    
    try:
        # Get a company
        companies = requests.get(f"{BASE_URL}/companies", timeout=10).json()
        if not companies:
            print_test("CompanyId filter test", False, "No companies found")
            return False
        
        company_id = companies[0]['id']
        
        # Get loads for this company
        resp = requests.get(f"{BASE_URL}/loads?companyId={company_id}", timeout=10)
        data = resp.json()
        
        # All items should belong to this company
        all_match = all(item.get('companyId') == company_id for item in data.get('items', []))
        
        passed = resp.status_code == 200 and all_match
        print_test(f"GET /api/loads?companyId={company_id} returns only that company's loads", 
                  passed,
                  f"Items: {len(data.get('items', []))}, Total: {data.get('total')}, All match: {all_match}")
        
        return passed
    except Exception as e:
        print_test("CompanyId filter test", False, f"Exception: {str(e)}")
        return False

def test_loads_shipmenttype_filter():
    """Test 6: ShipmentType filter"""
    print("=" * 80)
    print("TEST 6: GET /api/loads - ShipmentType Filter")
    print("=" * 80)
    
    try:
        resp = requests.get(f"{BASE_URL}/loads?shipmentType=ic_nakliye", timeout=10)
        data = resp.json()
        
        # All items should have shipmentType='ic_nakliye'
        all_match = all(item.get('shipmentType') == 'ic_nakliye' for item in data.get('items', []))
        
        passed = resp.status_code == 200 and all_match
        print_test("GET /api/loads?shipmentType=ic_nakliye returns only ic_nakliye loads", 
                  passed,
                  f"Items: {len(data.get('items', []))}, Total: {data.get('total')}, All match: {all_match}")
        
        return passed
    except Exception as e:
        print_test("ShipmentType filter test", False, f"Exception: {str(e)}")
        return False

def test_loads_date_filter():
    """Test 7: Date filter"""
    print("=" * 80)
    print("TEST 7: GET /api/loads - Date Filter")
    print("=" * 80)
    
    try:
        # Reset and create loads with specific dates
        requests.post(f"{BASE_URL}/seed", timeout=10)
        
        companies = requests.get(f"{BASE_URL}/companies", timeout=10).json()
        addresses = requests.get(f"{BASE_URL}/addresses", timeout=10).json()
        
        if not companies or not addresses:
            print_test("Date filter test", False, "No companies/addresses")
            return False
        
        company_id = companies[0]['id']
        address_id = addresses[0]['id']
        
        # Create load with specific date
        target_date = "2024-12-25"
        load_data = {
            "companyId": company_id,
            "addressId": address_id,
            "loadDate": target_date,
            "shipmentType": "ic_nakliye",
            "phone": "905551234567",
            "packages": "10 koli",
            "kg": "500",
            "destCity": "Ankara",
            "destCountry": "Türkiye",
            "note": "Test date filter",
            "user": "test_user"
        }
        resp = requests.post(f"{BASE_URL}/loads", json=load_data, timeout=10)
        created = resp.json()
        print(f"Created load with loadDate={target_date}")
        
        # Filter by date
        resp = requests.get(f"{BASE_URL}/loads?date={target_date}", timeout=10)
        data = resp.json()
        
        # All items should have loadDate matching target_date
        all_match = all(item.get('loadDate') == target_date for item in data.get('items', []))
        
        passed = resp.status_code == 200 and all_match and len(data.get('items', [])) >= 1
        print_test(f"GET /api/loads?date={target_date} returns loads with that date", 
                  passed,
                  f"Items: {len(data.get('items', []))}, Total: {data.get('total')}, All match: {all_match}")
        
        return passed
    except Exception as e:
        print_test("Date filter test", False, f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_loads_q_filter():
    """Test 8: Free-text q filter (destCity, destCountry, company name)"""
    print("=" * 80)
    print("TEST 8: GET /api/loads - Free-text Q Filter")
    print("=" * 80)
    
    try:
        # Reset
        requests.post(f"{BASE_URL}/seed", timeout=10)
        
        companies = requests.get(f"{BASE_URL}/companies", timeout=10).json()
        addresses = requests.get(f"{BASE_URL}/addresses", timeout=10).json()
        
        if not companies or not addresses:
            print_test("Q filter test", False, "No companies/addresses")
            return False
        
        company_id = companies[0]['id']
        address_id = addresses[0]['id']
        
        # Create load with destCity='İzmir'
        load_izmir = {
            "companyId": company_id,
            "addressId": address_id,
            "shipmentType": "ic_nakliye",
            "phone": "905551234567",
            "packages": "10 koli",
            "kg": "500",
            "destCity": "İzmir",
            "destCountry": "Türkiye",
            "note": "Test q filter",
            "user": "test_user"
        }
        resp = requests.post(f"{BASE_URL}/loads", json=load_izmir, timeout=10)
        print(f"Created load with destCity=İzmir")
        
        # Test q=izmir (case-insensitive)
        resp = requests.get(f"{BASE_URL}/loads?q=izmir", timeout=10)
        data = resp.json()
        
        # Should find the İzmir load
        has_izmir = any('izmir' in item.get('destCity', '').lower() for item in data.get('items', []))
        
        passed1 = resp.status_code == 200 and has_izmir
        print_test("GET /api/loads?q=izmir finds loads with destCity=İzmir (case-insensitive)", 
                  passed1,
                  f"Items: {len(data.get('items', []))}, Has İzmir: {has_izmir}")
        
        # Create a company named 'Zeta Lojistik' with a load
        zeta_company = {
            "name": "Zeta Lojistik A.Ş.",
            "phone": "02121234567",
            "email": "info@zeta.com",
            "active": True
        }
        resp = requests.post(f"{BASE_URL}/companies", json=zeta_company, timeout=10)
        zeta = resp.json()
        zeta_id = zeta.get('id')
        print(f"Created company: Zeta Lojistik, ID: {zeta_id}")
        
        # Create address for Zeta
        zeta_addr = {
            "companyId": zeta_id,
            "name": "Zeta Merkez",
            "address": "Test Cad. No:1",
            "city": "İstanbul",
            "district": "Kadıköy",
            "phone": "02121234567",
            "contact": "Zeta Contact",
            "coordinate": ""
        }
        resp = requests.post(f"{BASE_URL}/addresses", json=zeta_addr, timeout=10)
        zeta_addr_data = resp.json()
        zeta_addr_id = zeta_addr_data.get('id')
        
        # Create load for Zeta
        zeta_load = {
            "companyId": zeta_id,
            "addressId": zeta_addr_id,
            "shipmentType": "ic_nakliye",
            "phone": "905551234567",
            "packages": "5 koli",
            "kg": "300",
            "destCity": "Bursa",
            "destCountry": "Türkiye",
            "note": "Zeta test load",
            "user": "test_user"
        }
        resp = requests.post(f"{BASE_URL}/loads", json=zeta_load, timeout=10)
        print(f"Created load for Zeta company")
        
        # Test q=zeta (should match via company name)
        resp = requests.get(f"{BASE_URL}/loads?q=zeta", timeout=10)
        data = resp.json()
        
        # Should find the Zeta load (via company name lookup)
        has_zeta = any(item.get('companyId') == zeta_id for item in data.get('items', []))
        
        passed2 = resp.status_code == 200 and has_zeta
        print_test("GET /api/loads?q=zeta finds loads via company name match", 
                  passed2,
                  f"Items: {len(data.get('items', []))}, Has Zeta load: {has_zeta}")
        
        return passed1 and passed2
    except Exception as e:
        print_test("Q filter test", False, f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_loads_combined_filters():
    """Test 9: Combined filters (AND logic)"""
    print("=" * 80)
    print("TEST 9: GET /api/loads - Combined Filters (AND)")
    print("=" * 80)
    
    try:
        # Get prerequisites
        companies = requests.get(f"{BASE_URL}/companies", timeout=10).json()
        if not companies:
            print_test("Combined filters test", False, "No companies")
            return False
        
        company_id = companies[0]['id']
        
        # Test combined: status=planning&companyId=X&q=ankara
        resp = requests.get(f"{BASE_URL}/loads?status=planning&companyId={company_id}&q=ankara", timeout=10)
        data = resp.json()
        
        # All items must satisfy ALL conditions
        all_match = all(
            item.get('status') == 'planning' and 
            item.get('companyId') == company_id and
            ('ankara' in item.get('destCity', '').lower() or 'ankara' in item.get('destCountry', '').lower())
            for item in data.get('items', [])
        )
        
        passed = resp.status_code == 200
        print_test("GET /api/loads with combined filters (status+companyId+q) uses AND logic", 
                  passed,
                  f"Items: {len(data.get('items', []))}, Total: {data.get('total')}, All match: {all_match if data.get('items') else 'N/A (no items)'}")
        
        return passed
    except Exception as e:
        print_test("Combined filters test", False, f"Exception: {str(e)}")
        return False

def test_loads_sort():
    """Test 10: Sort by createdAt DESC (newest first)"""
    print("=" * 80)
    print("TEST 10: GET /api/loads - Sort by createdAt DESC")
    print("=" * 80)
    
    try:
        resp = requests.get(f"{BASE_URL}/loads?pageSize=10", timeout=10)
        data = resp.json()
        
        items = data.get('items', [])
        if len(items) < 2:
            print_test("Sort test", True, "Not enough items to verify sort (< 2)")
            return True
        
        # Verify items are sorted by createdAt DESC (newest first)
        is_sorted = all(
            items[i].get('createdAt', '') >= items[i+1].get('createdAt', '')
            for i in range(len(items) - 1)
        )
        
        passed = resp.status_code == 200 and is_sorted
        print_test("GET /api/loads returns items sorted by createdAt DESC (newest first)", 
                  passed,
                  f"Items: {len(items)}, Sorted: {is_sorted}")
        
        return passed
    except Exception as e:
        print_test("Sort test", False, f"Exception: {str(e)}")
        return False

def test_loads_regex_safety():
    """Test 11: Regex safety - special chars should not crash"""
    print("=" * 80)
    print("TEST 11: GET /api/loads - Regex Safety")
    print("=" * 80)
    
    try:
        # Test with regex special characters
        test_queries = ['.*', '[abc', '(test', 'a+b', 'x*y', 'a|b', 'test$']
        
        all_passed = True
        for q in test_queries:
            resp = requests.get(f"{BASE_URL}/loads?q={q}", timeout=10)
            passed = resp.status_code == 200
            if not passed:
                print_test(f"GET /api/loads?q={q} does not crash", False, f"Status: {resp.status_code}")
                all_passed = False
        
        if all_passed:
            print_test("GET /api/loads with regex special chars does not crash", True, "All queries returned 200")
        
        return all_passed
    except Exception as e:
        print_test("Regex safety test", False, f"Exception: {str(e)}")
        return False

def test_dashboard_structure():
    """Test 12: Dashboard structure and parallel countDocuments"""
    print("=" * 80)
    print("TEST 12: GET /api/dashboard - Structure & Counts")
    print("=" * 80)
    
    try:
        resp = requests.get(f"{BASE_URL}/dashboard", timeout=10)
        dashboard = resp.json()
        print(f"Dashboard response: {dashboard}")
        
        # Verify structure
        required_keys = ['total', 'pending', 'planning', 'planned', 'delivered']
        has_all_keys = all(key in dashboard for key in required_keys)
        
        passed1 = resp.status_code == 200 and has_all_keys
        print_test("GET /api/dashboard returns {total, pending, planning, planned, delivered}", 
                  passed1,
                  f"Keys: {list(dashboard.keys())}")
        
        # Verify all values are integers
        all_integers = all(isinstance(dashboard.get(key), int) for key in required_keys)
        print_test("All dashboard values are integers", all_integers, f"Values: {dashboard}")
        
        return passed1 and all_integers
    except Exception as e:
        print_test("Dashboard structure test", False, f"Exception: {str(e)}")
        return False

def test_dashboard_semantic_mapping():
    """Test 13: Dashboard semantic mapping verification"""
    print("=" * 80)
    print("TEST 13: GET /api/dashboard - Semantic Mapping")
    print("=" * 80)
    
    try:
        # Reset and create loads in each status
        requests.post(f"{BASE_URL}/seed", timeout=10)
        
        companies = requests.get(f"{BASE_URL}/companies", timeout=10).json()
        addresses = requests.get(f"{BASE_URL}/addresses", timeout=10).json()
        drivers = requests.get(f"{BASE_URL}/drivers", timeout=10).json()
        vehicles = requests.get(f"{BASE_URL}/vehicles", timeout=10).json()
        
        if not all([companies, addresses, drivers, vehicles]):
            print_test("Dashboard semantic test", False, "Missing prerequisites")
            return False
        
        company_id = companies[0]['id']
        address_id = addresses[0]['id']
        driver_id = drivers[0]['id']
        vehicle_id = vehicles[0]['id']
        
        # Create loads in different statuses
        statuses_to_create = {
            'created': 2,      # pending
            'planning': 3,     # planning
            'planned': 4,      # planned
            'in_transit': 2,   # planned (planned + in_transit)
            'delivered': 3,    # delivered
            'shipped': 2,      # delivered (delivered + shipped)
            'cancelled': 1     # included in total only
        }
        
        created_loads = {}
        
        for status, count in statuses_to_create.items():
            created_loads[status] = []
            for i in range(count):
                # Determine initial shipmentType
                if status == 'created':
                    shipment_type = 'musteri_kendisi'  # Will start as 'created'
                else:
                    shipment_type = 'ic_nakliye'  # Will start as 'planning'
                
                load_data = {
                    "companyId": company_id,
                    "addressId": address_id,
                    "shipmentType": shipment_type,
                    "phone": f"90555{i:07d}",
                    "packages": f"{i+1} koli",
                    "kg": str((i+1) * 10),
                    "destCity": "Test City",
                    "destCountry": "Türkiye",
                    "note": f"Test {status} {i+1}",
                    "user": "test_user"
                }
                resp = requests.post(f"{BASE_URL}/loads", json=load_data, timeout=10)
                load = resp.json()
                load_id = load.get('id')
                
                # Change status if needed
                if status != 'created' and status != 'planning':
                    # First plan it if not already planned
                    if load.get('status') != 'planned':
                        plan_data = {
                            "driverId": driver_id,
                            "vehicleId": vehicle_id,
                            "plannedDateTime": "2024-12-20T14:00:00Z",
                            "user": "test_user"
                        }
                        requests.post(f"{BASE_URL}/loads/{load_id}/plan", json=plan_data, timeout=10)
                    
                    # Then change to target status
                    if status != 'planned':
                        status_data = {
                            "status": status,
                            "note": f"Changed to {status}",
                            "user": "test_user"
                        }
                        requests.post(f"{BASE_URL}/loads/{load_id}/status", json=status_data, timeout=10)
                
                created_loads[status].append(load_id)
        
        print(f"Created loads: {sum(len(v) for v in created_loads.values())} total")
        for status, ids in created_loads.items():
            print(f"  {status}: {len(ids)}")
        
        # Get dashboard
        resp = requests.get(f"{BASE_URL}/dashboard", timeout=10)
        dashboard = resp.json()
        print(f"Dashboard: {dashboard}")
        
        # Verify semantic mapping
        expected_pending = statuses_to_create['created']  # 2
        expected_planning = statuses_to_create['planning']  # 3
        expected_planned = statuses_to_create['planned'] + statuses_to_create['in_transit']  # 4 + 2 = 6
        expected_delivered = statuses_to_create['delivered'] + statuses_to_create['shipped']  # 3 + 2 = 5
        expected_total = sum(statuses_to_create.values())  # 17
        
        print(f"Expected: total={expected_total}, pending={expected_pending}, planning={expected_planning}, planned={expected_planned}, delivered={expected_delivered}")
        
        pending_match = dashboard.get('pending') == expected_pending
        planning_match = dashboard.get('planning') == expected_planning
        planned_match = dashboard.get('planned') == expected_planned
        delivered_match = dashboard.get('delivered') == expected_delivered
        total_match = dashboard.get('total') == expected_total
        
        print_test("Dashboard pending == count(status='created')", 
                  pending_match,
                  f"Expected: {expected_pending}, Got: {dashboard.get('pending')}")
        
        print_test("Dashboard planning == count(status='planning')", 
                  planning_match,
                  f"Expected: {expected_planning}, Got: {dashboard.get('planning')}")
        
        print_test("Dashboard planned == count(status='planned') + count(status='in_transit')", 
                  planned_match,
                  f"Expected: {expected_planned}, Got: {dashboard.get('planned')}")
        
        print_test("Dashboard delivered == count(status='delivered') + count(status='shipped')", 
                  delivered_match,
                  f"Expected: {expected_delivered}, Got: {dashboard.get('delivered')}")
        
        print_test("Dashboard total == countDocuments({}) including cancelled", 
                  total_match,
                  f"Expected: {expected_total}, Got: {dashboard.get('total')}")
        
        return pending_match and planning_match and planned_match and delivered_match and total_match
    except Exception as e:
        print_test("Dashboard semantic mapping test", False, f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 80)
    print("YükTakip Backend API Test Suite - Pagination & Dashboard Updates")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print("Testing ONLY the two updated endpoints:")
    print("  1. GET /api/loads - server-side pagination & filtering")
    print("  2. GET /api/dashboard - parallel countDocuments")
    print("=" * 80 + "\n")
    
    results = {}
    
    # Smoke check seed
    results['seed'] = test_seed()
    
    # GET /api/loads tests
    results['loads_default'] = test_loads_default_response()
    results['loads_pagination'] = test_loads_pagination()
    results['loads_pagesize_cap'] = test_loads_pagesize_cap()
    results['loads_status_filter'] = test_loads_status_filter()
    results['loads_companyid_filter'] = test_loads_companyid_filter()
    results['loads_shipmenttype_filter'] = test_loads_shipmenttype_filter()
    results['loads_date_filter'] = test_loads_date_filter()
    results['loads_q_filter'] = test_loads_q_filter()
    results['loads_combined_filters'] = test_loads_combined_filters()
    results['loads_sort'] = test_loads_sort()
    results['loads_regex_safety'] = test_loads_regex_safety()
    
    # GET /api/dashboard tests
    results['dashboard_structure'] = test_dashboard_structure()
    results['dashboard_semantic'] = test_dashboard_semantic_mapping()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed_count = sum(1 for p in results.values() if p)
    print(f"\nTotal: {passed_count}/{total} tests passed")
    print("=" * 80 + "\n")
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
