"""
Test different Hugging Face models to find one that works.
"""

import os
import sys
import django
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codereview.settings')
django.setup()

from django.conf import settings

api_key = settings.AI_API_KEY

# Test different model endpoints
models_to_test = [
    "https://api-inference.huggingface.co/models/microsoft/CodeGPT-small-py",
    "https://router.huggingface.co/models/microsoft/CodeGPT-small-py",
    "https://api-inference.huggingface.co/models/bigcode/starcoder",
    "https://router.huggingface.co/models/bigcode/starcoder",
]

test_prompt = "Review this Python code: def hello(): print('world')"

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

print("Testing different Hugging Face model endpoints...")
print("="*60)

for url in models_to_test:
    print(f"\nTesting: {url}")
    print("-" * 60)
    
    data = {
        'inputs': test_prompt,
        'parameters': {
            'max_new_tokens': 100,
            'temperature': 0.3,
            'return_full_text': False
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[SUCCESS] Model is working!")
            if isinstance(result, list) and len(result) > 0:
                if 'generated_text' in result[0]:
                    print(f"Response: {result[0]['generated_text'][:100]}...")
            break
        elif response.status_code == 503:
            print("[INFO] Model is loading (free tier - wait 10-20 seconds)")
        elif response.status_code == 404:
            print("[SKIP] Model not found on this endpoint")
        else:
            print(f"[ERROR] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")

print("\n" + "="*60)
print("RECOMMENDATION:")
print("For code analysis, the system will work best with:")
print("1. OpenAI API (gpt-3.5-turbo or gpt-4)")
print("2. Groq API (free tier, fast responses)")
print("3. Hugging Face CodeGPT or StarCoder (if available)")
print("\nThe current DialoGPT model is for conversations, not code analysis.")
print("The system will fall back to intelligent pattern-based feedback if AI fails.")

