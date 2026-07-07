# Customer Response: Nova Caching and PR #1305

## Bug Status

We've confirmed the issue you reported. PR #1305 addresses this bug and is ready for review/merge.

**The bug:** When system prompt content blocks contain extra fields (beyond what Bedrock expects), the SDK passes them directly to Bedrock's API without sanitizing, causing a `ParamValidationError`.

**The fix:** PR #1305 adds proper formatting for system blocks, stripping extra fields before sending to Bedrock.

---

## Nova Prompt Caching Clarification

**Your question:** "Does Nova (Lite/Micro) by default cache system prompts?"

**Answer:** Nova has **two types** of prompt caching:

### 1. Automatic Caching (Default - No Configuration Needed)

Nova automatically optimizes repetitive prompt prefixes for **latency benefits**:
- Works transparently without any code changes
- You won't see cache metrics in the response
- Does NOT provide cost savings
- This is what the documentation refers to when saying Nova "automatically caches"

### 2. Explicit Prompt Caching (Opt-in for Cost Savings)

To get **cost savings** in addition to latency benefits, you need to explicitly add `cachePoint` blocks:

```python
from strands import Agent
from strands.models import BedrockModel

system_prompt_content = [
    {"text": "Your long system prompt here... (must be 1000+ tokens)"},
    {"cachePoint": {"type": "default"}},
]

agent = Agent(
    model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
    system_prompt=system_prompt_content,
)
```

**Requirements for explicit caching:**
- Minimum **1,000 tokens** before the `cachePoint`
- Maximum 20,000 tokens
- 5-minute TTL (resets on cache hit)
- Nova supports caching `system` and `messages` only (NOT `tools`)

---

## Verifying Cache is Working

When explicit caching is enabled, check your response metrics:

| Request | Expected Metric |
|---------|-----------------|
| First request | `cacheWriteInputTokens` > 0 (cache created) |
| Subsequent requests | `cacheReadInputTokens` > 0 (cache hit) |

**Example output we observed in testing:**
```
First request:  cacheWriteInputTokens: 2136
Second request: cacheReadInputTokens: 2136  (cache HIT!)
```

If you don't see these metrics:
1. Your system prompt may not meet the 1,000 token minimum
2. You may be hitting the 5-minute TTL between requests
3. There may be a bug (like the one PR #1305 fixes)

---

## Action Items

1. **Wait for PR #1305 to be merged** - This fixes the system prompt caching bug
2. **Update your SDK** once the PR is merged
3. **Verify your system prompt has 1,000+ tokens** before the `cachePoint`
4. **Check for cache metrics** in your response to confirm caching is working

---

## Documentation Note

The AWS documentation is vague because it doesn't clearly distinguish between:
- **Automatic caching** (latency only, no config needed)
- **Explicit caching** (cost + latency, requires `cachePoint`)

We recommend checking the [Amazon Bedrock Prompt Caching documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html) for the latest details.

---

## Testing Code

If you'd like to verify caching is working after the PR is merged:

```python
from strands import Agent
from strands.models import BedrockModel

# Generate 1000+ token system prompt
system_prompt_content = [
    {"text": "Your assistant instructions... " * 300},  # ~1500 tokens
    {"cachePoint": {"type": "default"}},
]

agent = Agent(
    model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
    system_prompt=system_prompt_content,
)

# First request - should show cacheWriteInputTokens
result1 = agent("Hello!")
print(f"Write: {result1.metrics.accumulated_usage.get('cacheWriteInputTokens', 0)}")

# Second request - should show cacheReadInputTokens
result2 = agent("Hello again!")
print(f"Read: {result2.metrics.accumulated_usage.get('cacheReadInputTokens', 0)}")
```

---

If you have any further questions, please let us know!
