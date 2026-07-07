# Understanding Prompt Caching: A First-Principles Guide

This document explains the prompt caching issue from the ground up. No prior knowledge required.

---

## Table of Contents

1. [What is an LLM?](#1-what-is-an-llm)
2. [How Does LLM Inference Work?](#2-how-does-llm-inference-work)
3. [The Problem: Repetitive Context = Wasted Compute](#3-the-problem-repetitive-context--wasted-compute)
4. [The Solution: Prompt Caching](#4-the-solution-prompt-caching)
5. [What is Amazon Bedrock?](#5-what-is-amazon-bedrock)
6. [How the Bedrock Converse API Works](#6-how-the-bedrock-converse-api-works)
7. [What are cachePoint Blocks?](#7-what-are-cachepoint-blocks)
8. [What is the Strands Agents SDK?](#8-what-is-the-strands-agents-sdk)
9. [Automatic vs Explicit Caching](#9-automatic-vs-explicit-caching)
10. [The Bug: What's Broken](#10-the-bug-whats-broken)
11. [The Fix: PR #1305](#11-the-fix-pr-1305)

---

## 1. What is an LLM?

A **Large Language Model (LLM)** is an AI system trained on massive amounts of text to understand and generate human-like language.

Examples:
- **Claude** (Anthropic)
- **Amazon Nova** (Amazon)
- **GPT-4** (OpenAI)
- **Llama** (Meta)

LLMs work by predicting "what comes next" given some input text. When you ask Claude a question, it processes your text and generates a response word-by-word (actually token-by-token).

---

## 2. How Does LLM Inference Work?

### What is a Token?

LLMs don't process text character-by-character. They break text into **tokens** - chunks of characters that represent common patterns.

```
"Hello, how are you?" → ["Hello", ",", " how", " are", " you", "?"]
                         (6 tokens)
```

Roughly: **1 token ≈ 4 characters** or **100 tokens ≈ 75 words**

### The Inference Process

When you send a prompt to an LLM:

```
┌─────────────────────────────────────────────────────────────┐
│                         YOUR PROMPT                          │
│  "You are a helpful assistant. Answer questions clearly."   │
│  "User: What is the capital of France?"                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      TOKENIZATION                            │
│  Break text into tokens: ~25 tokens                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   TRANSFORMER PROCESSING                     │
│  Each token "attends" to every other token                  │
│  This is the EXPENSIVE part (GPU compute)                   │
│  Cost: O(n²) where n = number of tokens                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      GENERATE OUTPUT                         │
│  "The capital of France is Paris."                          │
└─────────────────────────────────────────────────────────────┘
```

### Key Insight: Processing is Expensive

Every token in your prompt needs to be processed. The more tokens, the more:
- **Time** (latency)
- **Cost** (you pay per token)
- **GPU memory** used

---

## 3. The Problem: Repetitive Context = Wasted Compute

### The Scenario

Imagine you're building a customer support chatbot. Every message includes:

```python
system_prompt = """
You are a customer support agent for Acme Corp.
Here are our policies:
- Returns accepted within 30 days
- Shipping is free over $50
- ... (1000+ more words of policies)
"""
```

Every time a user sends a message, you send the ENTIRE system prompt + conversation:

```
Request 1: system_prompt + "What's your return policy?"
Request 2: system_prompt + prev_messages + "Can I return after 30 days?"
Request 3: system_prompt + prev_messages + "What about shipping?"
```

### The Waste

```
┌─────────────────────────────────────────────────────────────┐
│ Request 1: [System Prompt: 2000 tokens] + [User: 10 tokens] │
│            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                   │
│            Processed from scratch                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Request 2: [System Prompt: 2000 tokens] + [Prev: 100] + [User: 20] │
│            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                         │
│            SAME 2000 tokens processed AGAIN!                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Request 3: [System Prompt: 2000 tokens] + [Prev: 200] + [User: 15] │
│            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                         │
│            SAME 2000 tokens processed AGAIN!                      │
└─────────────────────────────────────────────────────────────┘
```

You're paying to process the same 2000 tokens over and over!

---

## 4. The Solution: Prompt Caching

### The Idea

What if we could tell the model: "Hey, I'm going to send you the same system prompt every time. Process it once and remember the result."

```
┌─────────────────────────────────────────────────────────────┐
│ Request 1: [System Prompt: 2000 tokens] + [User: 10 tokens] │
│            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                   │
│            Process and CACHE this                           │
│            Cost: 2000 input tokens (write to cache)         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Request 2: [CACHED: 2000 tokens] + [Prev: 100] + [User: 20] │
│            ^^^^^^^^^^^^^^^^^^^                               │
│            Read from cache (MUCH cheaper!)                  │
│            Cost: 2000 cached tokens + 120 input tokens      │
└─────────────────────────────────────────────────────────────┘
```

### The Benefits

| Without Caching | With Caching |
|-----------------|--------------|
| Pay full price for 2000 tokens every request | Pay once to cache, then ~90% discount on reads |
| Higher latency (reprocessing) | Lower latency (cache hit) |
| More GPU usage | Less GPU usage |

---

## 5. What is Amazon Bedrock?

**Amazon Bedrock** is AWS's managed service for accessing foundation models (LLMs).

### Why Use Bedrock?

Instead of hosting your own LLM infrastructure, you call an API:

```
┌──────────────┐         ┌─────────────────┐         ┌──────────────┐
│  Your App    │ ──────► │  Amazon Bedrock │ ──────► │   Claude /   │
│              │ (API)   │   (AWS Service) │         │   Nova       │
└──────────────┘         └─────────────────┘         └──────────────┘
```

### Available Models on Bedrock

- **Anthropic Claude** (Claude Sonnet, Opus, Haiku)
- **Amazon Nova** (Nova Lite, Micro, Pro, Premier)
- **Meta Llama**
- **Mistral**
- And more...

---

## 6. How the Bedrock Converse API Works

The **Converse API** is Bedrock's standardized way to have chat conversations with any model.

### Request Structure

```python
response = bedrock_client.converse(
    modelId="amazon.nova-lite-v1:0",

    # System prompt - instructions for the AI
    system=[
        {"text": "You are a helpful assistant."}
    ],

    # Conversation history
    messages=[
        {"role": "user", "content": [{"text": "Hello!"}]},
        {"role": "assistant", "content": [{"text": "Hi there!"}]},
        {"role": "user", "content": [{"text": "What's 2+2?"}]},
    ],

    # Tools the AI can use (optional)
    toolConfig={
        "tools": [...]
    }
)
```

### Content Blocks

Each piece of content is a **content block** - a dictionary with a specific type:

```python
# Text content
{"text": "Hello world"}

# Image content
{"image": {"format": "png", "source": {"bytes": ...}}}

# Cache point (tells Bedrock to cache everything before this)
{"cachePoint": {"type": "default"}}
```

### Tagged Unions

Bedrock uses **tagged unions** for content blocks. This means each block can only have ONE type:

```python
# VALID - one type per block
{"text": "Hello"}
{"cachePoint": {"type": "default"}}

# INVALID - multiple types in one block
{"text": "Hello", "cachePoint": {"type": "default"}}  # ERROR!
```

This is important for understanding the bug later.

---

## 7. What are cachePoint Blocks?

A **cachePoint** is a marker that tells Bedrock: "Cache everything up to this point."

### How to Use It

```python
system = [
    {"text": "Your very long system prompt... (1000+ tokens)"},
    {"cachePoint": {"type": "default"}},  # <-- Cache marker
]
```

### Requirements

| Model | Minimum Tokens Before Cache Point |
|-------|----------------------------------|
| Claude Sonnet 4 | 1,024 tokens |
| Claude 3.5 Haiku | 2,048 tokens |
| Claude Opus 4.5 | 4,096 tokens |
| Nova (all models) | 1,000 tokens |

### Cache Behavior

1. **First Request**: Content is processed and cached
   - You see: `cacheWriteInputTokens: 1500`
   - You pay: Cache write rate (slightly higher than normal)

2. **Subsequent Requests** (within 5 minutes): Content read from cache
   - You see: `cacheReadInputTokens: 1500`
   - You pay: Cache read rate (~90% discount!)

3. **After 5 minutes**: Cache expires, start over

---

## 8. What is the Strands Agents SDK?

**Strands Agents SDK** is a Python library that makes it easy to build AI agents using Bedrock.

### Without Strands (Raw Bedrock API)

```python
import boto3

client = boto3.client("bedrock-runtime")
response = client.converse(
    modelId="amazon.nova-lite-v1:0",
    system=[{"text": "You are helpful."}],
    messages=[{"role": "user", "content": [{"text": "Hello"}]}]
)
print(response["output"]["message"]["content"][0]["text"])
```

### With Strands SDK

```python
from strands import Agent
from strands.models import BedrockModel

agent = Agent(
    model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
    system_prompt="You are helpful."
)
result = agent("Hello")
print(result)
```

### How Strands Works Internally

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Code                                │
│   agent = Agent(system_prompt="...", model=BedrockModel(...))   │
│   result = agent("Hello")                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Strands SDK                                 │
│   BedrockModel._format_request()                                │
│   - Formats system prompt                                        │
│   - Formats messages                                             │
│   - Formats tools                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Bedrock Converse API                          │
│   client.converse(modelId=..., system=..., messages=...)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Automatic vs Explicit Caching

This is where the documentation gets confusing. There are TWO types of caching:

### Type 1: Automatic Caching (Nova Only)

Nova models automatically optimize repetitive prefixes:

```python
# No special code needed
agent = Agent(
    model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
    system_prompt="Your prompt here..."
)
```

**Characteristics:**
- Happens automatically
- Provides **latency benefits** (faster responses)
- Does **NOT** provide cost savings
- You **won't see** cache metrics in the response
- The documentation calls this "automatic prompt caching"

### Type 2: Explicit Caching (Opt-in)

You explicitly mark content for caching with `cachePoint`:

```python
system_prompt_content = [
    {"text": "Your long prompt... (1000+ tokens)"},
    {"cachePoint": {"type": "default"}},  # Explicit marker
]

agent = Agent(
    model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
    system_prompt=system_prompt_content,
)
```

**Characteristics:**
- Requires explicit `cachePoint` blocks
- Provides **latency benefits** AND **cost savings**
- You **will see** cache metrics in the response
- Requires minimum token count (1000 for Nova)

### Summary Table

| Feature | Automatic | Explicit |
|---------|-----------|----------|
| Configuration | None | `cachePoint` blocks |
| Latency benefit | Yes | Yes |
| Cost savings | **No** | **Yes** |
| Cache metrics visible | No | Yes |
| Minimum tokens | N/A | 1000 (Nova) |

---

## 10. The Bug: What's Broken

### The Problem

When you use `cachePoint` in system prompts with the Strands SDK, you might get this error:

```
ParamValidationError: Parameter validation failed:
Invalid number of parameters set for tagged union structure system[0].
Can only set one of the following keys: text, guardContent, cachePoint.
Unknown parameter in system[0]: "extraField"
```

### Root Cause

The bug is in how Strands SDK handles system prompt content blocks.

**Messages are handled correctly:**
```python
# In BedrockModel._format_request():
"messages": self._format_bedrock_messages(messages)  # ✓ Formatted!
```

The `_format_bedrock_messages()` function:
1. Loops through each content block
2. Calls `_format_request_message_content()` on each
3. This strips any extra fields and ensures correct format

**System blocks are NOT handled:**
```python
# In BedrockModel._format_request():
"system": system_blocks,  # ✗ Passed directly, no formatting!
```

### The Consequence

If your system content blocks have any extra fields (beyond what Bedrock expects), they get passed directly to Bedrock, which throws a validation error.

### Visual Representation

```
                    MESSAGES PATH (Works)
                    ─────────────────────
User Input ──► _format_bedrock_messages() ──► _format_request_message_content()
                                                        │
                                                        ▼
                                              Strips extra fields
                                              Ensures correct format
                                                        │
                                                        ▼
                                              Clean content block ──► Bedrock API ✓


                    SYSTEM PATH (Broken)
                    ────────────────────
User Input ──────────────────────────────────────────────► Bedrock API ✗
                    (No formatting, extra fields remain)
                              │
                              ▼
                    ParamValidationError!
```

---

## 11. The Fix: PR #1305

### What the PR Does

PR #1305 adds a new method `_format_bedrock_system_blocks()` that formats system content blocks the same way messages are formatted.

### Before (Broken)

```python
def _format_request(...):
    ...
    return {
        "modelId": self.config["model_id"],
        "messages": self._format_bedrock_messages(messages),
        "system": system_blocks,  # ← Direct pass, no formatting
        ...
    }
```

### After (Fixed)

```python
def _format_request(...):
    ...
    # NEW: Format system blocks
    formatted_system_blocks = self._format_bedrock_system_blocks(system_blocks)

    return {
        "modelId": self.config["model_id"],
        "messages": self._format_bedrock_messages(messages),
        "system": formatted_system_blocks,  # ← Now formatted!
        ...
    }

def _format_bedrock_system_blocks(self, system_blocks):
    """Format system content blocks for Bedrock API compatibility."""
    if not system_blocks:
        return []

    cleaned_blocks = []
    for block in system_blocks:
        # Reuse the same formatting logic as messages
        formatted_block = self._format_request_message_content(block)
        cleaned_blocks.append(formatted_block)

    return cleaned_blocks
```

### The Result

```
                    SYSTEM PATH (After Fix)
                    ───────────────────────
User Input ──► _format_bedrock_system_blocks() ──► _format_request_message_content()
                                                           │
                                                           ▼
                                                 Strips extra fields
                                                 Ensures correct format
                                                           │
                                                           ▼
                                                 Clean content block ──► Bedrock API ✓
```

---

## Quick Reference

### How to Use Caching Correctly (After PR #1305)

```python
from strands import Agent
from strands.models import BedrockModel

# System prompt must be 1000+ tokens for Nova
long_system_prompt = "Your detailed instructions here... " * 300

system_prompt_content = [
    {"text": long_system_prompt},
    {"cachePoint": {"type": "default"}},  # Cache marker
]

agent = Agent(
    model=BedrockModel(model_id="amazon.nova-lite-v1:0"),
    system_prompt=system_prompt_content,
)

# First request - writes to cache
result1 = agent("Hello!")
print(f"Cache write: {result1.metrics.accumulated_usage.get('cacheWriteInputTokens', 0)}")

# Second request - reads from cache
result2 = agent("Hello again!")
print(f"Cache read: {result2.metrics.accumulated_usage.get('cacheReadInputTokens', 0)}")
```

### Expected Output

```
Cache write: 1500  (First request - content cached)
Cache read: 1500   (Second request - cache hit!)
```

---

## Glossary

| Term | Definition |
|------|------------|
| **LLM** | Large Language Model - AI that generates text |
| **Token** | Chunk of text (~4 characters) that LLMs process |
| **Inference** | The process of generating output from an LLM |
| **Amazon Bedrock** | AWS service for accessing LLMs via API |
| **Converse API** | Bedrock's chat API for multi-turn conversations |
| **Content Block** | A piece of content (text, image, cache point) |
| **Tagged Union** | A data structure that can be one of several types |
| **cachePoint** | Marker that tells Bedrock to cache content |
| **Cache Write** | First time content is cached (slightly higher cost) |
| **Cache Read** | Reading from cache (much cheaper, ~90% discount) |
| **TTL** | Time To Live - cache expires after 5 minutes |
| **Strands SDK** | Python library for building AI agents on Bedrock |
