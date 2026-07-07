"""
Test Bedrock Converse API directly (without Strands SDK) to isolate caching behavior.

This script tests:
1. cachePoint in system blocks with Nova models
2. cachePoint in messages with Claude models
3. Whether cache metrics are returned correctly

Run with: python reviews/pr-1305-cache-analysis/test_bedrock_direct.py
"""

import boto3
import json
from pprint import pprint

# Initialize Bedrock client
client = boto3.client("bedrock-runtime", region_name="us-east-1")

def generate_long_text(word_count: int = 1500) -> str:
    """Generate text that's approximately 1000+ tokens (Nova minimum requirement)."""
    base_text = (
        "This is a comprehensive system prompt for an AI assistant. "
        "The assistant should be helpful, harmless, and honest. "
        "It should provide accurate information and acknowledge when it doesn't know something. "
        "The assistant should maintain a professional tone while being friendly and approachable. "
    )
    # Repeat to get enough tokens (roughly 1 token per 4 characters, so ~6000 chars = ~1500 tokens)
    return (base_text * (word_count // 20))[:word_count * 4]


def test_nova_system_cache_point():
    """Test 1: Nova Lite with cachePoint in system blocks."""
    print("\n" + "="*80)
    print("TEST 1: Nova Lite - cachePoint in system blocks")
    print("="*80)

    long_system_prompt = generate_long_text(1500)
    print(f"System prompt length: {len(long_system_prompt)} chars (~{len(long_system_prompt)//4} tokens)")

    try:
        response = client.converse(
            modelId="amazon.nova-lite-v1:0",
            system=[
                {"text": long_system_prompt},
                {"cachePoint": {"type": "default"}},
            ],
            messages=[
                {"role": "user", "content": [{"text": "Hello! What are you?"}]}
            ]
        )

        print("\nResponse received successfully!")
        print(f"Stop reason: {response.get('stopReason')}")

        usage = response.get("usage", {})
        print("\nUsage metrics:")
        pprint(usage)

        if "cacheWriteInputTokens" in usage or "cacheReadInputTokens" in usage:
            print("\nCache metrics found!")
            print(f"  cacheWriteInputTokens: {usage.get('cacheWriteInputTokens', 0)}")
            print(f"  cacheReadInputTokens: {usage.get('cacheReadInputTokens', 0)}")
        else:
            print("\nNo cache metrics in response (automatic caching may still provide latency benefits)")

        return True

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        return False


def test_nova_without_cache_point():
    """Test 2: Nova Lite WITHOUT explicit cachePoint (test automatic caching)."""
    print("\n" + "="*80)
    print("TEST 2: Nova Lite - WITHOUT explicit cachePoint (automatic caching)")
    print("="*80)

    long_system_prompt = generate_long_text(1500)
    print(f"System prompt length: {len(long_system_prompt)} chars (~{len(long_system_prompt)//4} tokens)")

    try:
        response = client.converse(
            modelId="amazon.nova-lite-v1:0",
            system=[
                {"text": long_system_prompt},
                # No cachePoint - testing automatic caching
            ],
            messages=[
                {"role": "user", "content": [{"text": "Hello! What are you?"}]}
            ]
        )

        print("\nResponse received successfully!")
        print(f"Stop reason: {response.get('stopReason')}")

        usage = response.get("usage", {})
        print("\nUsage metrics:")
        pprint(usage)

        if "cacheWriteInputTokens" in usage or "cacheReadInputTokens" in usage:
            print("\nCache metrics found (automatic caching reporting)!")
            print(f"  cacheWriteInputTokens: {usage.get('cacheWriteInputTokens', 0)}")
            print(f"  cacheReadInputTokens: {usage.get('cacheReadInputTokens', 0)}")
        else:
            print("\nNo cache metrics in response (expected for automatic caching)")

        return True

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        return False


def test_claude_message_cache_point():
    """Test 3: Claude Sonnet with cachePoint in messages."""
    print("\n" + "="*80)
    print("TEST 3: Claude Sonnet - cachePoint in messages")
    print("="*80)

    long_text = generate_long_text(1500)
    print(f"Message text length: {len(long_text)} chars (~{len(long_text)//4} tokens)")

    try:
        response = client.converse(
            modelId="us.anthropic.claude-sonnet-4-20250514-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"text": long_text},
                        {"cachePoint": {"type": "default"}},
                        {"text": "What is this text about?"},
                    ]
                }
            ]
        )

        print("\nResponse received successfully!")
        print(f"Stop reason: {response.get('stopReason')}")

        usage = response.get("usage", {})
        print("\nUsage metrics:")
        pprint(usage)

        if "cacheWriteInputTokens" in usage or "cacheReadInputTokens" in usage:
            print("\nCache metrics found!")
            print(f"  cacheWriteInputTokens: {usage.get('cacheWriteInputTokens', 0)}")
            print(f"  cacheReadInputTokens: {usage.get('cacheReadInputTokens', 0)}")
        else:
            print("\nNo cache metrics in response")

        return True

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        return False


def test_nova_cache_hit():
    """Test 4: Nova Lite - verify cache hit on second request."""
    print("\n" + "="*80)
    print("TEST 4: Nova Lite - Cache hit verification (two sequential requests)")
    print("="*80)

    long_system_prompt = generate_long_text(1500)

    system_blocks = [
        {"text": long_system_prompt},
        {"cachePoint": {"type": "default"}},
    ]

    # First request - should write to cache
    print("\nFirst request (cache write)...")
    try:
        response1 = client.converse(
            modelId="amazon.nova-lite-v1:0",
            system=system_blocks,
            messages=[{"role": "user", "content": [{"text": "Hello!"}]}]
        )
        usage1 = response1.get("usage", {})
        print(f"  cacheWriteInputTokens: {usage1.get('cacheWriteInputTokens', 0)}")
        print(f"  cacheReadInputTokens: {usage1.get('cacheReadInputTokens', 0)}")

    except Exception as e:
        print(f"\nFirst request ERROR: {type(e).__name__}: {e}")
        return False

    # Second request - should read from cache
    print("\nSecond request (cache read)...")
    try:
        response2 = client.converse(
            modelId="amazon.nova-lite-v1:0",
            system=system_blocks,
            messages=[{"role": "user", "content": [{"text": "Hello again!"}]}]
        )
        usage2 = response2.get("usage", {})
        print(f"  cacheWriteInputTokens: {usage2.get('cacheWriteInputTokens', 0)}")
        print(f"  cacheReadInputTokens: {usage2.get('cacheReadInputTokens', 0)}")

        if usage2.get('cacheReadInputTokens', 0) > 0:
            print("\nCache HIT confirmed!")
        else:
            print("\nNo cache hit detected")

        return True

    except Exception as e:
        print(f"\nSecond request ERROR: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("="*80)
    print("BEDROCK CONVERSE API CACHE POINT TESTING")
    print("Testing directly with boto3 (no Strands SDK)")
    print("="*80)

    results = {}

    results["nova_system_cache"] = test_nova_system_cache_point()
    results["nova_auto_cache"] = test_nova_without_cache_point()
    results["claude_message_cache"] = test_claude_message_cache_point()
    results["nova_cache_hit"] = test_nova_cache_hit()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")
