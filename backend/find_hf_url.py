"""
Script to help find the correct Hugging Face API URL.
Tests different URL formats and provides guidance.
"""

import requests
import json

api_key = "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"

# Different URL formats to test
url_formats = [
    # Format 1: Direct model inference (old format - deprecated)
    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
    
    # Format 2: Router endpoint (new format)
    "https://router.huggingface.co/models/microsoft/DialoGPT-medium",
    
    # Format 3: Inference API v1
    "https://api-inference.huggingface.co/v1/models/microsoft/DialoGPT-medium",
    
    # Format 4: Direct inference endpoint
    "https://inference.huggingface.co/models/microsoft/DialoGPT-medium",
    
    # Format 5: Text generation endpoint
    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium/generate",
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
print("Finding Correct Hugging Face API URL")
print("="*70)
print(f"\nTesting with API Key: {api_key[:20]}...")
print(f"Model: microsoft/DialoGPT-medium")
print("\n" + "="*70)

working_urls = []

for i, url in enumerate(url_formats, 1):
    print(f"\n[{i}/{len(url_formats)}] Testing: {url}")
    print("-" * 70)
    
    try:
        response = requests.post(url, headers=headers, json=test_data, timeout=10)
        status = response.status_code
        
        print(f"Status Code: {status}")
        
        if status == 200:
            print("[SUCCESS] This URL works!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:200]}...")
            working_urls.append(url)
        elif status == 401:
            print("[ERROR] Unauthorized - API key might be invalid")
        elif status == 404:
            print("[INFO] Not found - endpoint doesn't exist")
        elif status == 410:
            error = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"[INFO] Deprecated - {error}")
        elif status == 503:
            print("[INFO] Model loading - this endpoint exists but model needs to wake up")
            working_urls.append(url)
        else:
            print(f"[INFO] Status {status}: {response.text[:200]}")
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {str(e)[:100]}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

if working_urls:
    print("\n[SUCCESS] Working URLs found:")
    for url in working_urls:
        print(f"  ✓ {url}")
    print("\nUse one of these URLs in your .env file:")
    print(f"AI_API_URL={working_urls[0]}")
else:
    print("\n[INFO] No working URLs found with current formats.")
    print("\nNext steps:")
    print("1. Check Hugging Face documentation: https://huggingface.co/docs/api-inference")
    print("2. Visit your model page: https://huggingface.co/microsoft/DialoGPT-medium")
    print("3. Look for 'API' or 'Inference' section on the model page")
    print("4. Check your API token permissions at: https://huggingface.co/settings/tokens")
    print("\nAlternative: Use a different model that's known to work:")
    print("  - Try: https://huggingface.co/models?pipeline_tag=text-generation")
    print("  - Look for models with 'Inference API' enabled")

print("\n" + "="*70)

