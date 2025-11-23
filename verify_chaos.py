import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_normal_order():
    print("\n--- Testing Normal Order ---")
    payload = {
        "user_id": 123,
        "product_name": "Laptop",
        "quantity": 1,
        "address": "123 Test St"
    }
    try:
        response = requests.post(f"{BASE_URL}/orders", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_fraud_detection():
    print("\n--- Testing Fraud Detection (User ID starts with 4) ---")
    payload = {
        "user_id": 404,
        "product_name": "Laptop",
        "quantity": 1,
        "address": "123 Test St"
    }
    try:
        response = requests.post(f"{BASE_URL}/orders", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_payment_failure():
    print("\n--- Testing Payment Failure (Card ends in 00) ---")
    payload = {
        "user_id": 123,
        "product_name": "Laptop",
        "quantity": 1,
        "address": "123 Test St",
        "card_number": "1234567890123400"
    }
    try:
        response = requests.post(f"{BASE_URL}/orders", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_black_friday_chaos():
    print("\n--- Testing Black Friday Chaos (Payment Timeout) ---")
    payload = {
        "user_id": 123,
        "product_name": "Laptop",
        "quantity": 1,
        "address": "123 Test St"
    }
    headers = {"X-Chaos-Scenario": "black-friday"}
    try:
        response = requests.post(f"{BASE_URL}/orders", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Wait for services to be ready (manual check usually required, but we'll just run the tests)
    test_normal_order()
    test_fraud_detection()
    test_payment_failure()
    test_black_friday_chaos()
