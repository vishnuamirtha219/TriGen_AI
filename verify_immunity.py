import requests
import json

url = 'http://127.0.0.1:5000/api/predict/immunity'

# Sample Data for a healthy individual
payload = {
    'wbc': 6000,
    'neutrophils': 55,
    'lymphocytes': 30,
    'monocytes': 5,
    'igg': 1000,
    'igm': 100,
    'iga': 200,
    'bmi': 22,
    'vaccination': 1,
    'past_infections': 1,
    'age': 30
}

try:
    print(f"Sending POST request to {url}...")
    print(f"Data: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("\n✅ Success! Response:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\n❌ Exception: {e}")
    print("Ensure the Flask app is running on port 5000.")
