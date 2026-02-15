import requests
import time

BASE_URL = "http://localhost:8000/api"

def test_advance_day():
    print("Testing /api/simulation/time/advance-day...")
    try:
        res = requests.post(f"{BASE_URL}/simulation/time/advance-day", timeout=30)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print("Success!")
            print(res.json())
        else:
            print(f"Failed: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_advance_day()
