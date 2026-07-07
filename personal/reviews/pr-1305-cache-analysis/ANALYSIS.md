# PR #1305 Analysis: Bedrock Cache Point Formatting Issue

## Summary

**PR:** https://github.com/strands-agents/sdk-python/pull/1305
**Related Issues:** #1219, #1015
**Status:** Bug confirmed, PR fix is correct and needed

---

## Bug Description

When using `cachePoint` blocks in system prompts, Bedrock's API can throw a `ParamValidationError` if the system content blocks contain extra/non-standard fields.

**Error:**
```
ParamValidationError: Parameter validation failed:
Invalid number of parameters set for tagged union structure system[0].
Can only set one of the following keys: text, guardContent, cachePoint.
Unknown parameter in system[0]: "extraField"
```

---

## Root Cause Analysis

### Current SDK Behavior (v1.19.0)

| Content Type | Formatting | Extra Fields Handling |
|--------------|------------|----------------------|
| **Messages** | `_format_bedrock_messages()` → `_format_request_message_content()` | Stripped |
| **System blocks** | Passed directly (no formatting) | **Not stripped** |

### Code Path

**Messages (correct):**
```
_format_request() line 227:
    "messages": self._format_bedrock_messages(messages)

_format_bedrock_messages() loops through content and calls:
    self._format_request_message_content(content_block)

_format_request_message_content() line 385-386:
    if "cachePoint" in content:
        return {"cachePoint": {"type": content["cachePoint"]["type"]}}
```

**System blocks (bug):**
```
_format_request() line 228:
    "system": system_blocks,  # Passed directly!
```

---

## Test Results

### Direct Bedrock API (boto3)

All tests PASS - Bedrock API works correctly with proper formatting:

| Test | Result | Cache Metrics |
|------|--------|---------------|
| Nova system cache | PASS | `cacheWriteInputTokens: 1035` |
| Nova without cachePoint | PASS | No cache metrics (expected) |
| Claude message cache | PASS | `cacheWriteInputTokens: 1081` |
| Nova cache hit | PASS | `cacheReadInputTokens: 1035` |

### Strands SDK (v1.19.0)

| Test | Result | Notes |
|------|--------|-------|
| System prompt with clean cachePoint | PASS | Works when no extra fields |
| System prompt with extra fields | **FAIL** | `ParamValidationError` |
| Messages with extra fields | PASS | Extra fields stripped correctly |

---

## PR #1305 Fix Analysis

### What the PR does:

1. Adds `_format_bedrock_system_blocks()` method
2. Formats each system block through `_format_request_message_content()`
3. Ensures extra fields are stripped from system blocks

**Code change:**
```python
# Before (line 228):
"system": system_blocks,

# After:
formatted_system_blocks = self._format_bedrock_system_blocks(system_blocks)
...
"system": formatted_system_blocks,
```

### Assessment

| Criteria | Status |
|----------|--------|
| Fix is minimal and focused | YES |
| Reuses existing code | YES (`_format_request_message_content`) |
| Backwards compatible | YES |
| Test coverage | YES (5 new tests) |
| All existing tests pass | YES (92 unit, 19 integration) |

**Recommendation: APPROVE**

---

## Nova Caching Clarification

### Two Types of Caching

1. **Automatic (Implicit) Caching** - Default, no config needed
   - Provides **latency benefits** for repetitive prefixes
   - Does NOT show in usage metrics
   - Does NOT provide cost savings

2. **Explicit Prompt Caching** - Opt-in with `cachePoint`
   - Provides **latency AND cost savings**
   - Shows `cacheWriteInputTokens` / `cacheReadInputTokens` in metrics
   - Requires minimum 1,000 tokens per checkpoint (Nova)
   - 5-minute TTL that resets on cache hit

### Nova Model Requirements

| Model | Min Tokens | Max Checkpoints | Cacheable Fields |
|-------|-----------|-----------------|------------------|
| Nova Micro | 1,000 | 4 | `system`, `messages` |
| Nova Lite | 1,000 | 4 | `system`, `messages` |
| Nova Pro | 1,000 | 4 | `system`, `messages` |
| Nova Premier | 1,000 | 4 | `system`, `messages` |

**Note:** Nova does NOT support caching `tools` (unlike Claude models).

---

## Reproducing the Bug

```python
from strands import Agent
from strands.models import BedrockModel

# This will FAIL with current SDK if there are extra fields
system_prompt_content = [
    {
        "text": "Long system prompt..." * 300,
        "extraField": "some value",  # Extra field causes failure
    },
    {"cachePoint": {"type": "default"}},
]

agent = Agent(
    model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
    system_prompt=system_prompt_content,
)
agent("Hello")  # Throws ParamValidationError
```

---

## Files Referenced

- `src/strands/models/bedrock.py:190-296` - `_format_request()`
- `src/strands/models/bedrock.py:298-356` - `_format_bedrock_messages()`
- `src/strands/models/bedrock.py:369-386` - `_format_request_message_content()`
- `tests_integ/test_bedrock_cache_point.py` - Existing cache tests

---

## Test Scripts

- `reviews/pr-1305-cache-analysis/test_bedrock_direct.py` - Direct Bedrock API tests
- `reviews/pr-1305-cache-analysis/test_strands_sdk.py` - Strands SDK tests
