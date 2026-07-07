# Messages and Conversation Management

**Date:** 2026-01-31
**Context:** SDK Fundamentals - Learning Guide
**Source Files:** `src/strands/types/content.py`, `src/strands/agent/conversation_manager/`

---

## 1. What Is a Message?

A message is the fundamental unit of communication in the Strands SDK. Every interaction between the user, the model, and tools is represented as a message.

**Plain English:** A message is a dictionary with two fields: who said it (`role`) and what they said (`content`). The content is a list of content blocks, each of which can be text, an image, a tool request, a tool result, or other content types.

**Analogy:** Think of a group chat. Each bubble has a sender (user or assistant) and content (text, images, etc.). The conversation is just a list of these bubbles in order. When you scroll up, you see the entire history. That is exactly what `agent.messages` is -- a list of message bubbles.

**Source:** `src/strands/types/content.py`, lines 170-191

```python
Role = Literal["user", "assistant"]

class Message(TypedDict):
    content: list[ContentBlock]
    role: Role

Messages = list[Message]
```

There are only two roles:
- `"user"` -- messages from the user (and tool results, which are wrapped as user messages)
- `"assistant"` -- messages from the model

---

## 2. ContentBlock Types

Each message contains a list of `ContentBlock` objects. A `ContentBlock` is a TypedDict where different keys represent different content types. Only one key is typically set per block.

**Source:** `src/strands/types/content.py`, lines 74-99

### Text Block (most common)

```json
{"text": "Hello, how can I help you today?"}
```

Plain text content. This is what you see in most user messages and model responses.

### Image Block

```json
{
    "image": {
        "source": {
            "bytes": "<base64-encoded-data>",
            "type": "base64"
        },
        "format": "png"
    }
}
```

Used for sending images to the model (vision capabilities).

### Tool Use Block

```json
{
    "toolUse": {
        "toolUseId": "tooluse_abc123",
        "name": "weather_tool",
        "input": {"city": "Seattle"}
    }
}
```

This appears in **assistant** messages. The model is requesting that a tool be executed. One assistant message can contain multiple `toolUse` blocks.

### Tool Result Block

```json
{
    "toolResult": {
        "toolUseId": "tooluse_abc123",
        "status": "success",
        "content": [{"text": "72F and sunny in Seattle"}]
    }
}
```

This appears in **user** messages. It is the result of executing a tool, sent back to the model. The `toolUseId` matches the corresponding `toolUse` block.

### Document Block

```json
{
    "document": {
        "name": "report",
        "format": "pdf",
        "source": {
            "bytes": "<base64-encoded-data>"
        }
    }
}
```

Used for sending documents (PDFs, etc.) to the model.

### Video Block

```json
{
    "video": {
        "format": "mp4",
        "source": {
            "bytes": "<base64-encoded-data>"
        }
    }
}
```

Used for sending video content to the model (where supported).

### Other Block Types

- `reasoningContent` -- Extended thinking / chain-of-thought from the model
- `guardContent` -- Content for guardrail evaluation
- `cachePoint` -- Prompt caching optimization marker
- `citationsContent` -- Citation references from the model

---

## 3. How Messages Build Up During a Request

Let's walk through a tool-using conversation step by step. We will track what `agent.messages` looks like at each stage.

### Setup

```python
from strands import Agent, tool

@tool
def weather_tool(city: str) -> str:
    """Get weather for a city."""
    return "72F and sunny"

agent = Agent(tools=[weather_tool])
```

### User asks: "What's the weather in Seattle?"

**Step 1:** User message is added.

```python
agent.messages = [
    {
        "role": "user",
        "content": [{"text": "What's the weather in Seattle?"}]
    }
]
```

**Step 2:** Model responds with a tool use request. Assistant message is added.

```python
agent.messages = [
    # Message 1: User's question
    {
        "role": "user",
        "content": [{"text": "What's the weather in Seattle?"}]
    },
    # Message 2: Model decides to call weather_tool
    {
        "role": "assistant",
        "content": [
            {"text": "Let me check the weather for you."},
            {
                "toolUse": {
                    "toolUseId": "tooluse_abc123",
                    "name": "weather_tool",
                    "input": {"city": "Seattle"}
                }
            }
        ]
    }
]
```

**Step 3:** SDK executes the tool. Tool result is added as a user message.

```python
agent.messages = [
    # Message 1: User's question
    {
        "role": "user",
        "content": [{"text": "What's the weather in Seattle?"}]
    },
    # Message 2: Model's tool request
    {
        "role": "assistant",
        "content": [
            {"text": "Let me check the weather for you."},
            {
                "toolUse": {
                    "toolUseId": "tooluse_abc123",
                    "name": "weather_tool",
                    "input": {"city": "Seattle"}
                }
            }
        ]
    },
    # Message 3: Tool result (wrapped as user message)
    {
        "role": "user",
        "content": [
            {
                "toolResult": {
                    "toolUseId": "tooluse_abc123",
                    "status": "success",
                    "content": [{"text": "72F and sunny"}]
                }
            }
        ]
    }
]
```

**Step 4:** Model reads the tool result and generates its final answer. Final assistant message is added.

```python
agent.messages = [
    # Message 1: User's question
    {"role": "user", "content": [{"text": "What's the weather in Seattle?"}]},
    # Message 2: Model's tool request
    {"role": "assistant", "content": [
        {"text": "Let me check the weather for you."},
        {"toolUse": {"toolUseId": "tooluse_abc123", "name": "weather_tool", "input": {"city": "Seattle"}}}
    ]},
    # Message 3: Tool result
    {"role": "user", "content": [
        {"toolResult": {"toolUseId": "tooluse_abc123", "status": "success", "content": [{"text": "72F and sunny"}]}}
    ]},
    # Message 4: Model's final answer
    {"role": "assistant", "content": [
        {"text": "The weather in Seattle is currently 72F and sunny!"}
    ]}
]
```

**Key pattern:** Messages always alternate between `user` and `assistant` roles. A `toolUse` in an assistant message is always followed by a `toolResult` in the next user message with matching `toolUseId`. This pairing is critical -- breaking it causes errors.

---

## 4. System Prompt

The system prompt is a special instruction sent to the model with every call. It tells the model who it is and how to behave.

```python
agent = Agent(
    system_prompt="You are a helpful weather assistant. Always provide temperatures in both F and C."
)
```

**Important:** The system prompt is NOT part of `agent.messages`. It is sent separately to the model as a `system` parameter. You can read and modify it:

```python
# Read the system prompt
print(agent.system_prompt)

# Change it at runtime
agent.system_prompt = "You are now a coding assistant."
```

The system prompt is sent on every model call, so changing it affects all subsequent interactions.

---

## 5. Conversation Management -- Why It Matters

Models have a limited context window (e.g., 200K tokens for Claude). Every message in `agent.messages` consumes tokens. As conversations grow longer, you will eventually hit the limit.

Conversation management automatically handles this by trimming, summarizing, or otherwise reducing the conversation history. Without it, long-running agents would crash with a context window overflow error.

The `ConversationManager.apply_management()` method runs after each invocation. If the context window is exceeded during a model call, `reduce_context()` is called as an emergency measure.

**Source:** `src/strands/agent/conversation_manager/__init__.py`

---

## 6. Three Conversation Management Strategies

### Strategy 1: SlidingWindowConversationManager (Default)

**Source:** `src/strands/agent/conversation_manager/sliding_window_conversation_manager.py`

This is the default. It keeps the most recent messages and removes the oldest ones when the window size is exceeded.

```python
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

# Default behavior (window_size=40)
agent = Agent()

# Custom window size
agent = Agent(
    conversation_manager=SlidingWindowConversationManager(window_size=100)
)
```

**How it works:**
- After each invocation, checks if `len(messages) > window_size`
- If yes, removes the oldest messages until within the window
- Carefully avoids breaking `toolUse`/`toolResult` pairs (a toolResult without its matching toolUse would cause errors)
- Can truncate oversized tool results as a first resort before removing messages

**Per-turn management:** For agents that make many tool calls in a single invocation (e.g., web browsing with screenshots), you can enable proactive management:

```python
# Apply management before every model call
manager = SlidingWindowConversationManager(window_size=40, per_turn=True)

# Apply management every 5 model calls
manager = SlidingWindowConversationManager(window_size=40, per_turn=5)
```

**When to use:** Most use cases. Simple, predictable, low overhead.

### Strategy 2: SummarizingConversationManager

**Source:** `src/strands/agent/conversation_manager/summarizing_conversation_manager.py`

Instead of simply dropping old messages, this strategy uses the model to generate a summary of the oldest messages and keeps that summary as context.

```python
from strands.agent.conversation_manager import SummarizingConversationManager

agent = Agent(
    conversation_manager=SummarizingConversationManager(
        summary_ratio=0.3,              # Summarize the oldest 30% of messages
        preserve_recent_messages=10,     # Always keep the 10 most recent messages
    )
)
```

**How it works:**
- Triggered when the context window overflows (not proactively)
- Takes the oldest `summary_ratio` proportion of messages
- Sends them to the model with a summarization prompt
- Replaces those messages with a single summary message
- Subsequent overflows re-summarize, building on the previous summary

**Custom summarization:** You can provide your own summarization prompt or a dedicated summarization agent:

```python
# Custom prompt
manager = SummarizingConversationManager(
    summarization_system_prompt="Summarize the key technical decisions and code snippets."
)

# Dedicated agent (uses its own model/config)
summary_agent = Agent(model=cheaper_model, system_prompt="You are a summarizer.")
manager = SummarizingConversationManager(summarization_agent=summary_agent)
```

**When to use:** Long conversations where context from early messages matters (multi-step research, ongoing projects). The trade-off is that summarization adds latency and cost (an extra model call).

### Strategy 3: NullConversationManager

**Source:** `src/strands/agent/conversation_manager/null_conversation_manager.py`

Does absolutely nothing. All messages are kept forever.

```python
from strands.agent.conversation_manager import NullConversationManager

agent = Agent(
    conversation_manager=NullConversationManager()
)
```

**How it works:**
- `apply_management()` is a no-op
- `reduce_context()` raises `ContextWindowOverflowException`

**When to use:** Short conversations that will never approach the context limit, testing, or when you manage the conversation history yourself externally.

---

## 7. Emergency Context Reduction

When the model returns a "context too large" error during a model call, the SDK calls `reduce_context()` as an emergency measure. This happens regardless of the conversation manager's normal management cycle.

For `SlidingWindowConversationManager`:
1. First tries to truncate the largest tool result in the history
2. If that does not help, trims the oldest messages (respecting toolUse/toolResult pairs)
3. If nothing can be trimmed, raises `ContextWindowOverflowException`

For `SummarizingConversationManager`:
1. Calculates how many messages to summarize
2. Generates a summary and replaces those messages
3. If summarization fails, raises the original error

For `NullConversationManager`:
1. Immediately raises `ContextWindowOverflowException`

---

## Quick Reference

```
Message = {"role": "user"|"assistant", "content": [ContentBlock, ...]}

ContentBlock types:
  {"text": "..."}                          -- plain text
  {"toolUse": {"toolUseId", "name", "input"}}  -- model wants to use a tool
  {"toolResult": {"toolUseId", "status", "content"}}  -- tool execution result
  {"image": {...}}                         -- image content
  {"document": {...}}                      -- document content
  {"video": {...}}                         -- video content

Conversation flow:
  user text -> assistant toolUse -> user toolResult -> assistant text
  (roles always alternate, toolUse/toolResult always paired)

System prompt:
  Separate from messages. Sent on every model call. Not in agent.messages.

Conversation managers:
  SlidingWindowConversationManager  -- drops oldest (default, window_size=40)
  SummarizingConversationManager   -- summarizes oldest on overflow
  NullConversationManager          -- keeps everything, fails on overflow
```

**Key source files:**
- `src/strands/types/content.py` -- `Message`, `ContentBlock`, `Role`, `Messages`
- `src/strands/agent/conversation_manager/conversation_manager.py` -- `ConversationManager` base class
- `src/strands/agent/conversation_manager/sliding_window_conversation_manager.py` -- `SlidingWindowConversationManager`
- `src/strands/agent/conversation_manager/summarizing_conversation_manager.py` -- `SummarizingConversationManager`
- `src/strands/agent/conversation_manager/null_conversation_manager.py` -- `NullConversationManager`
