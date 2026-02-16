import requests
import json

def test_optimize():
    url = "http://localhost:8080/api/optimize"
    try:
        # First ensure we have apps
        apps = requests.get("http://localhost:8080/api/appliances").json()
        print(f"Testing with {len(apps)} apps...")
        
        response = requests.post(url, json={})
        data = response.json()
        print(f"Status: {data.get('status')}")
        if data.get('status') == "Success":
            print(f"Total Cost: ${data.get('total_cost')}")
            print(f"Battery Discharge Total: {data.get('battery_total')} kWh")
            print("Successfully optimized!")
            return True
        else:
            print(f"Failed: {data.get('suggestions')}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_optimize()
