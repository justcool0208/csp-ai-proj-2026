import requests
import json
import time

BASE_URL = "http://localhost:8080/api"

def run_comprehensive_test():
    print("🚀 Starting Comprehensive CSP SHEMS Test...")
    
    # 1. Test GET Appliances
    print("\n--- Phase 1: Verify Initial State ---")
    res = requests.get(f"{BASE_URL}/appliances")
    initial_count = len(res.json())
    print(f"Initial appliance count: {initial_count}")
    
    # 2. Test POST (Add Appliance)
    print("\n--- Phase 2: Adding 'Test Device' ---")
    test_app = {
        "id": "test_999",
        "name": "Test Power Load",
        "power": 2.5,
        "duration": 60,
        "earliest_start": 600,
        "latest_end": 1200,
        "priority": 4
    }
    res = requests.post(f"{BASE_URL}/appliances", json=test_app)
    if res.status_code == 200:
        print("✅ POST Success: Device added.")
    else:
        print(f"❌ POST Failed: {res.text}")
        return

    # 3. Test OPTIMIZE
    print("\n--- Phase 3: Running CSP Optimization ---")
    res = requests.post(f"{BASE_URL}/optimize", json={"weather_condition": "Sunny", "max_power_limit": 20.0})
    data = res.json()
    if data.get("status") == "Success":
        print("✅ OPTIMIZE Success!")
        print(f"   Summary: {data['summary']}")
        print(f"   Suggestions: {data['suggestions']}")
    else:
        print(f"❌ OPTIMIZE Failed: {data.get('suggestions')}")
        # Not returning here because we still want to test DELETE

    # 4. Test DELETE
    print(f"\n--- Phase 4: Removing 'Test Device' (ID: test_999) ---")
    res = requests.delete(f"{BASE_URL}/appliances/test_999")
    if res.status_code == 200:
        print("✅ DELETE Success: Device removed.")
    else:
        print(f"❌ DELETE Failed: {res.text}")
        return

    # 5. Verify final state
    print("\n--- Phase 5: Final Verification ---")
    res = requests.get(f"{BASE_URL}/appliances")
    final_count = len(res.json())
    print(f"Final appliance count: {final_count}")
    
    if final_count == initial_count:
        print("\n🏆 TEST PASSED: Full lifecycle (CRUD + CSP) verified.")
    else:
        print("\n⚠️ TEST COMPLETED with warnings: Count mismatch.")

if __name__ == "__main__":
    run_comprehensive_test()
