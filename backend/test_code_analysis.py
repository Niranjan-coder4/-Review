"""
Test the complete code analysis flow including fallback.
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codereview.settings')
django.setup()

from api.services import CodeAnalysisService

# Test with actual Python code
test_code = """def calculate_factorial(n):
    if n == 0:
        return 1
    else:
        return n * calculate_factorial(n - 1)

print(calculate_factorial(5))"""

print("="*60)
print("Testing Code Analysis Service")
print("="*60)
print("\nTest Code:")
print("-" * 60)
print(test_code)
print("-" * 60)

service = CodeAnalysisService()

print(f"\nAI API Key: {'Set' if service.ai_api_key else 'Not Set'}")
print(f"AI API URL: {service.ai_api_url}")
print()

print("Running analysis...")
result = service.analyze_code(test_code, 'py')

print("\n" + "="*60)
print("ANALYSIS RESULT")
print("="*60)
print(f"Success: {result.get('success', False)}")

if result.get('success'):
    feedback = result.get('feedback', [])
    print(f"Feedback Items: {len(feedback)}")
    print()
    
    if len(feedback) > 0:
        print("Feedback Details:")
        print("-" * 60)
        for i, item in enumerate(feedback, 1):
            print(f"{i}. Line {item.get('line', 'N/A')} [{item.get('severity', 'N/A').upper()}]")
            print(f"   Category: {item.get('category', 'N/A')}")
            print(f"   Message: {item.get('message', 'N/A')}")
            print()
    else:
        print("No feedback generated")
else:
    print("Analysis failed - check error messages above")

print("="*60)
print("\nNOTE: If AI API is not working, the system uses intelligent")
print("pattern-based feedback (mock feedback) which still provides")
print("useful code analysis based on code patterns.")
print("="*60)

