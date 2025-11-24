"""
Test models that are known to work with Hugging Face Inference API.
"""

import requests
import json

api_key = "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"

# Models that typically work with Inference API
models_to_test = [
    ("microsoft/DialoGPT-medium", "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"),
    ("gpt2", "https://api-inference.huggingface.co/models/gpt2"),
    ("distilgpt2", "https://api-inference.huggingface.co/models/distilgpt2"),
    ("google/flan-t5-base", "https://api-inference.huggingface.co/models/google/flan-t5-base"),
]

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

test_data = {
    'inputs': 'Hello, how are you?',
    'parameters': {
        'max_new_tokens': 50
    }
}

print("="*70)
print("Testing Models with Hugging Face Inference API")
print("="*70)
print("\nNOTE: Even if endpoints return 410 (deprecated), we'll check")
print("the model pages for the correct new URL format.")
print("\n" + "="*70)

working_models = []

for model_name, url in models_to_test:
    print(f"\nTesting: {model_name}")
    print(f"URL: {url}")
    print("-" * 70)
    
    try:
        response = requests.post(url, headers=headers, json=test_data, timeout=10)
        status = response.status_code
        
        print(f"Status: {status}")
        
        if status == 200:
            print("[SUCCESS] This model works!")
            working_models.append((model_name, url))
        elif status == 410:
            error = response.json() if 'application/json' in response.headers.get('content-type', '') else {}
            if 'router.huggingface.co' in str(error):
                new_url = url.replace('api-inference.huggingface.co', 'router.huggingface.co')
                print(f"[INFO] Deprecated - try new URL: {new_url}")
                # Test the new URL
                try:
                    new_response = requests.post(new_url, headers=headers, json=test_data, timeout=10)
                    if new_response.status_code in [200, 503]:
                        print(f"[SUCCESS] New URL works! Status: {new_response.status_code}")
                        working_models.append((model_name, new_url))
                except:
                    pass
        elif status == 503:
            print("[INFO] Model is loading - endpoint exists!")
            working_models.append((model_name, url))
        elif status == 401:
            print("[ERROR] Unauthorized - check API key permissions")
        elif status == 404:
            print("[INFO] Model not found on this endpoint")
        else:
            print(f"[INFO] Status {status}")
    
    except Exception as e:
        print(f"[ERROR] {str(e)[:100]}")

print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)

if working_models:
    print("\nWorking models found:")
    for model, url in working_models:
        print(f"  ✓ {model}")
        print(f"    URL: {url}")
    print("\nUse this in your .env file:")
    print(f"AI_API_URL={working_models[0][1]}")
else:
    print("\nNo working models found with standard endpoints.")
    print("\nHOW TO FIND THE CORRECT URL:")
    print("="*70)
    print("\n1. Go to Hugging Face: https://huggingface.co/")
    print("2. Search for a model (e.g., 'gpt2' or 'text-generation')")
    print("3. Click on a model page")
    print("4. Look for 'Inference' or 'API' tab/section")
    print("5. Find the 'Use this model' section")
    print("6. Look for 'cURL' or 'Python' code examples")
    print("7. The URL will be in the example code")
    print("\nExample model pages to check:")
    print("  - https://huggingface.co/gpt2")
    print("  - https://huggingface.co/distilgpt2")
    print("  - https://huggingface.co/microsoft/DialoGPT-medium")
    print("\nOr check the Inference API docs:")
    print("  - https://huggingface.co/docs/api-inference")

print("\n" + "="*70)

