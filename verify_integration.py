import requests
import json
import time

BASE_URL = 'http://127.0.0.1:5000/api'

# Use a session to maintain user login state if needed, 
# but for API testing we might need to handle cookies manually or simulate session.
session = requests.Session()

def test_integration():
    print("🚀 Starting Integration Test: Immunity -> Sickle Cell -> LSD")
    
    # 0. Login/Register if necessary (assuming guest or existing user for simple test)
    # For now, we'll assume the endpoints work without strict session for this test
    # or we can try to hit the login if we had credentials.
    
    # 1. Immunity Analysis
    print("\n--- Step 1: Performing Immunity Analysis ---")
    imm_payload = {
        'wbc': 6000,
        'neutrophils': 55,
        'lymphocytes': 30,
        'monocytes': 5,
        'igg': 1000,
        'age': 30,
        'patient_name': 'Test Integration User'
    }
    resp = session.post(f"{BASE_URL}/predict/immunity", json=imm_payload)
    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ Immunity Score: {result.get('immunity_score')} ({result.get('immunity_class')})")
    else:
        print(f"❌ Immunity Analysis Failed: {resp.text}")
        return

    # 2. Sickle Cell Analysis
    print("\n--- Step 2: Performing Sickle Cell Analysis (Should show linked immunity) ---")
    sickle_payload = {
        'hba': 60,
        'hbs': 38,
        'hbf': 2,
        'age': 30,
        'patient_name': 'Test Integration User'
    }
    resp = session.post(f"{BASE_URL}/predict/sickle_cell", json=sickle_payload)
    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ Prediction: {result.get('prediction')}")
        print(f"✅ Linked Immunity Found: {result.get('linked_immunity')}")
        if result.get('linked_immunity'):
            print(f"✅ Versatility Check: {result.get('linked_immunity').get('class')}")
        else:
            print("⚠️ No linked immunity found in response!")
    else:
        print(f"❌ Sickle Cell Analysis Failed: {resp.text}")
        return

    # 3. LSD Analysis
    print("\n--- Step 3: Performing LSD Analysis (Should show linked immunity) ---")
    lsd_payload = {
        'b_glucosidase': 5.2,
        'a_galactosidase': 4.8,
        'liver_size': 14,
        'spleen_size': 10,
        'age': 30,
        'patient_name': 'Test Integration User'
    }
    resp = session.post(f"{BASE_URL}/predict/lsd", json=lsd_payload)
    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ Risk Level: {result.get('risk_level')}")
        print(f"✅ Linked Immunity Found: {result.get('linked_immunity')}")
        if result.get('linked_immunity'):
            print(f"✅ Versatility Check: {result.get('linked_immunity').get('class')}")
        else:
            print("⚠️ No linked immunity found in response!")
    else:
        print(f"❌ LSD Analysis Failed: {resp.text}")
        return

    # 4. Chat/LLM Versatility Test
    print("\n--- Step 4: Chatbot Versatility Test ---")
    chat_payload = {
        'message': "How does my immunity affect my risk for sickle cell and LSD?",
        'context': {
            'analysis': "Patient has Sickle Cell Trait and Strong Immunity (Score 85). LSD risk is Low.",
            'page': '/sickle_cell'
        }
    }
    resp = session.post(f"{BASE_URL}/chat", json=chat_payload)
    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ Chatbot Response:\n{result.get('response')}")
    else:
        print(f"❌ Chat Test Failed: {resp.text}")

if __name__ == "__main__":
    test_integration()
