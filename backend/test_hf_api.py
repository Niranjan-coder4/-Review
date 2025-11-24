"""
Quick test script to verify Hugging Face API connection.
Run this from the backend directory: python test_hf_api.py
"""

import os
import sys
import django
import requests
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codereview.settings')
django.setup()

from django.conf import settings

# Get API credentials
api_key = settings.AI_API_KEY
api_url = settings.AI_API_URL

print("="*60)
print("Testing Hugging Face API Connection")
print("="*60)
print(f"API URL: {api_url}")
print(f"API Key: {'Set' if api_key else 'NOT SET'}")
print()

if not api_key:
    print("[ERROR] AI_API_KEY not set in settings!")
    sys.exit(1)

# Test with a simple prompt
test_prompt = "Review this Python code: def hello(): print('world')"

print("Sending test request...")
print(f"Prompt: {test_prompt[:50]}...")
print()

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Hugging Face format
data = {
    'inputs': test_prompt,
    'parameters': {
        'max_new_tokens': 200,
        'temperature': 0.3,
        'return_full_text': False
    }
}

try:
    print("Making API request...")
    response = requests.post(api_url, headers=headers, json=data, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print()
    
    # Print error response for debugging
    if response.status_code != 200:
        print("Error Response:")
        try:
            error_detail = response.json()
            print(json.dumps(error_detail, indent=2))
        except:
            print(response.text[:500])
        print()
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS! API is working!")
        print()
        print("Response:")
        if isinstance(result, list) and len(result) > 0:
            if 'generated_text' in result[0]:
                print(result[0]['generated_text'])
            else:
                print(json.dumps(result, indent=2))
        else:
            print(json.dumps(result, indent=2))
    elif response.status_code == 503:
        print("⚠️  WARNING: Model is loading. Hugging Face free tier models need to be woken up.")
        print("   Try again in 10-20 seconds.")
        print()
        print("Response:", response.text[:200])
    else:
        print(f"❌ ERROR: API returned status {response.status_code}")
        print()
        try:
            error_detail = response.json()
            print("Error details:")
            print(json.dumps(error_detail, indent=2))
        except:
            print("Error response:", response.text[:500])
    
except requests.exceptions.Timeout:
    print("[ERROR] Request timed out (30 seconds)")
except requests.exceptions.RequestException as e:
    print(f"[ERROR] Request failed - {str(e)}")
except Exception as e:
    print(f"[ERROR] Unexpected error - {str(e)}")

print()
print("="*60)
print("NOTE: DialoGPT-medium is a conversational model.")
print("For better code analysis, consider using:")
print("  - microsoft/CodeGPT-small-py")
print("  - bigcode/starcoder")
print("  - Or OpenAI/Groq models")
print("="*60)

