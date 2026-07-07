"""
Test Strands SDK with cachePoint to reproduce the reported issue.

This script tests:
1. cachePoint in system prompts (expected to fail with current SDK)
2. cachePoint in messages (expected to fail with current SDK)
3. Regular system prompt without cachePoint (should work)

Run with: python reviews/pr-1305-cache-analysis/test_strands_sdk.py
"""

import sys
import traceback
from pprint import pprint

# Import Strands SDK
try:
    from strands import Agent
    from strands.models import BedrockModel
    print(f"Strands SDK imported successfully")
except ImportError as e:
    print(f"Error importing Strands SDK: {e}")
    print("Make sure you have strands-agents installed: pip install strands-agents")
    sys.exit(1)


def generate_long_text(word_count: int = 1500) -> str:
    """Generate text that's approximately 1000+ tokens (Nova minimum requirement)."""
    base_text = (
        "This is a comprehensive system prompt for an AI assistant. "
        "The assistant should be helpful, harmless, and honest. "
        "It should provide accurate information and acknowledge when it doesn't know something. "
        "The assistant should maintain a professional tone while being friendly and approachable. "
    )
    return (base_text * (word_count // 20))[:word_count * 4]


def test_nova_system_prompt_with_cache_point():
    """Test 1: Nova Lite with cachePoint in system_prompt_content."""
    print("\n" + "="*80)
    print("TEST 1: Strands SDK - Nova Lite with cachePoint in system prompt")
    print("="*80)

    long_system_prompt = generate_long_text(1500)
    print(f"System prompt length: {len(long_system_prompt)} chars (~{len(long_system_prompt)//4} tokens)")

    system_prompt_content = [
        {"text": long_system_prompt},
        {"cachePoint": {"type": "default"}},
    ]

    try:
        model = BedrockModel(
            model_id="amazon.nova-lite-v1:0",
            region_name="us-east-1"
        )

        agent = Agent(
            model=model,
            system_prompt=system_prompt_content,
            load_tools_from_directory=False,
        )

        result = agent("Hello! What are you?")
        print(f"\nResponse received: {str(result)[:200]}...")

        # Check for cache metrics
        if hasattr(result, 'metrics'):
            print("\nMetrics:")
            pprint(result.metrics)

        print("\nTEST PASSED - No error occurred")
        return True

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}")
        print(f"Message: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False


def test_claude_message_with_cache_point():
    """Test 2: Claude Sonnet with cachePoint in messages."""
    print("\n" + "="*80)
    print("TEST 2: Strands SDK - Claude Sonnet with cachePoint in messages")
    print("="*80)

    long_text = generate_long_text(1500)
    print(f"Message text length: {len(long_text)} chars (~{len(long_text)//4} tokens)")

    messages = [
        {
            "role": "user",
            "content": [
                {"text": long_text},
                {"cachePoint": {"type": "default"}},
            ],
        },
        {"role": "assistant", "content": [{"text": "I understand."}]},
    ]

    try:
        model = BedrockModel(
            model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="us-east-1"
        )

        agent = Agent(
            model=model,
            messages=messages,
            load_tools_from_directory=False,
        )

        result = agent("What was the text about?")
        print(f"\nResponse received: {str(result)[:200]}...")

        if hasattr(result, 'metrics'):
            print("\nMetrics:")
            pprint(result.metrics)

        print("\nTEST PASSED - No error occurred")
        return True

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}")
        print(f"Message: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False


def test_nova_without_cache_point():
    """Test 3: Nova Lite WITHOUT cachePoint (should work)."""
    print("\n" + "="*80)
    print("TEST 3: Strands SDK - Nova Lite WITHOUT cachePoint (baseline)")
    print("="*80)

    long_system_prompt = generate_long_text(1500)
    print(f"System prompt length: {len(long_system_prompt)} chars (~{len(long_system_prompt)//4} tokens)")

    try:
        model = BedrockModel(
            model_id="amazon.nova-lite-v1:0",
            region_name="us-east-1"
        )

        agent = Agent(
            model=model,
            system_prompt=long_system_prompt,  # Simple string, no cachePoint
            load_tools_from_directory=False,
        )

        result = agent("Hello! What are you?")
        print(f"\nResponse received: {str(result)[:200]}...")

        if hasattr(result, 'metrics'):
            print("\nMetrics:")
            pprint(result.metrics)

        print("\nTEST PASSED - No error occurred")
        return True

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}")
        print(f"Message: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False


def test_deprecated_cache_prompt_config():
    """Test 4: Using deprecated cache_prompt config option."""
    print("\n" + "="*80)
    print("TEST 4: Strands SDK - Using deprecated cache_prompt config")
    print("="*80)

    long_system_prompt = generate_long_text(1500)
    print(f"System prompt length: {len(long_system_prompt)} chars (~{len(long_system_prompt)//4} tokens)")

    try:
        model = BedrockModel(
            model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="us-east-1",
            cache_prompt="default",  # Deprecated config option
        )

        agent = Agent(
            model=model,
            system_prompt=long_system_prompt,
            load_tools_from_directory=False,
        )

        result = agent("Hello!")
        print(f"\nResponse received: {str(result)[:200]}...")

        if hasattr(result, 'metrics'):
            print("\nMetrics:")
            pprint(result.metrics)

        print("\nTEST PASSED (with deprecation warning expected)")
        return True

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}")
        print(f"Message: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*80)
    print("STRANDS SDK CACHE POINT TESTING")
    print("Testing with current SDK to reproduce reported issues")
    print("="*80)

    results = {}

    # Test 3 first (baseline - should work)
    results["nova_no_cache"] = test_nova_without_cache_point()

    # Tests that might fail with current SDK
    results["nova_system_cache"] = test_nova_system_prompt_with_cache_point()
    results["claude_message_cache"] = test_claude_message_with_cache_point()
    results["deprecated_cache_prompt"] = test_deprecated_cache_prompt_config()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")

    print("\n" + "="*80)
    print("EXPECTED BEHAVIOR:")
    print("="*80)
    print("  - nova_no_cache: PASS (baseline, no cachePoint)")
    print("  - nova_system_cache: FAIL (bug - cachePoint in system prompt)")
    print("  - claude_message_cache: FAIL (bug - cachePoint in messages)")
    print("  - deprecated_cache_prompt: PASS (with deprecation warning)")
    print("\nIf nova_system_cache and claude_message_cache FAIL, PR #1305 is needed.")
