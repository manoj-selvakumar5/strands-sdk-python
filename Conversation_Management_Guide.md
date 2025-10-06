# Conversation Management Guide

A comprehensive guide to understanding and using conversation managers in Strands Python SDK.

## Table of Contents
- [What Are Conversation Managers?](#what-are-conversation-managers)
- [How Conversation Managers Work](#how-conversation-managers-work)
- [Types of Conversation Managers](#types-of-conversation-managers)
- [Key Concepts](#key-concepts)
- [Code Examples](#code-examples)
- [Common Issues and Solutions](#common-issues-and-solutions)
- [Best Practices](#best-practices)

---

## What Are Conversation Managers?

Conversation managers control the size and content of your agent's conversation history (the `messages` array). They help you:

- **Manage memory usage** - Keep conversations from growing unbounded
- **Control context length** - Prevent hitting the model's input token limits
- **Maintain relevant state** - Keep important context while removing old messages

**Important:** Conversation managers manage **INPUT** size (what you send to the model), NOT **OUTPUT** size (what the model generates).

---

## How Conversation Managers Work

Conversation managers have two key methods that are called automatically by the agent:

### 1. `apply_management(agent)`

**When called:** After **every event loop cycle** (after the model responds)

**Location in code:** `src/strands/agent/agent.py:633`

```python
finally:
    self.conversation_manager.apply_management(self)
    self.hooks.invoke_callbacks(AfterInvocationEvent(agent=self))
```

**Purpose:** Proactive maintenance - trim messages to stay within configured limits

**Example:** `SlidingWindowConversationManager` removes old messages when count > `window_size`

### 2. `reduce_context(agent, e)`

**When called:** When a `ContextWindowOverflowException` is raised (input too large for model)

**Location in code:** `src/strands/agent/agent.py:658-660`

```python
except ContextWindowOverflowException as e:
    # Try reducing the context size and retrying
    self.conversation_manager.reduce_context(self, e=e)

    # Retry the event loop cycle
    events = self._execute_event_loop_cycle(invocation_state)
```

**Purpose:** Reactive recovery - aggressively reduce context to recover from overflow

**Example:** `SlidingWindowConversationManager` truncates tool results or removes messages

---

## Types of Conversation Managers

### 1. SlidingWindowConversationManager (Default)

Maintains a fixed-size window of recent messages.

**Constructor:**
```python
SlidingWindowConversationManager(
    window_size: int = 40,                    # Max number of messages
    should_truncate_results: bool = True      # Truncate large tool results
)
```

**How it works:**

#### `apply_management()`:
- Checks if message count > `window_size` (default 40)
- If exceeded, calls `reduce_context()` to trim oldest messages
- Preserves tool use/result pairs (won't orphan toolUse or toolResult)

#### `reduce_context()`:
When `should_truncate_results=True`:
1. **First:** Finds the last message with tool results
2. **Truncates:** Replaces tool result content with `"The tool result was too large!"`
3. **If still needed:** Removes oldest messages (respecting tool use/result pairing)

**File:** `src/strands/agent/conversation_manager/sliding_window_conversation_manager.py`

---

### 2. SummarizingConversationManager

Summarizes old conversation history instead of deleting it.

**Constructor:**
```python
SummarizingConversationManager(
    model: Model,                              # Model to use for summarization
    summarization_prompt: Optional[str] = None # Custom prompt for summarization
)
```

**How it works:**

#### `apply_management()`:
- Does nothing (no proactive summarization)
- Only acts when `reduce_context()` is called

#### `reduce_context()`:
1. Takes the conversation history (excluding system prompt)
2. Uses the provided model to generate a summary
3. Replaces old messages with a single summary message
4. Keeps the summary at the start of conversation

**File:** `src/strands/agent/conversation_manager/summarizing_conversation_manager.py`

**Note:** No `should_truncate_results` option - uses summarization instead.

---

### 3. NullConversationManager

Does nothing - keeps all messages forever.

**Constructor:**
```python
NullConversationManager()  # No parameters
```

**How it works:**

#### `apply_management()`:
- Does nothing

#### `reduce_context()`:
- Raises `ContextWindowOverflowException` (cannot recover)

**Use case:** Short conversations or when you want full control over message management.

**File:** `src/strands/agent/conversation_manager/null_conversation_manager.py`

---

## Key Concepts

### Exception Types: The Critical Distinction

Understanding the difference between these two exceptions is crucial:

#### `ContextWindowOverflowException`
- **What:** Your **INPUT** (conversation history + system prompt) is too large
- **When:** Before the model starts generating
- **Triggers:** `conversation_manager.reduce_context()`
- **Conversation managers help:** ✅ Yes! They can truncate/summarize to reduce input
- **Location:** `src/strands/agent/agent.py:658`

#### `MaxTokensReachedException`
- **What:** The model's **OUTPUT** (response) hit the `max_tokens` limit you configured
- **When:** During model generation (response was cut off mid-stream)
- **Triggers:** Hard failure (raises exception)
- **Conversation managers help:** ❌ No! They don't control output size
- **Location:** `src/strands/event_loop/event_loop.py:213-227`

```python
# In event_loop.py
if stop_reason == "max_tokens":
    raise MaxTokensReachedException(
        message=(
            "Agent has reached an unrecoverable state due to max_tokens limit. "
            "For more information see: "
            "https://strandsagents.com/latest/user-guide/concepts/agents/agent-loop/#maxtokensreachedexception"
        )
    )
```

### Visual Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Agent.invoke()                                              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Event Loop Cycle                                     │  │
│  │                                                      │  │
│  │  1. Prepare messages (conversation history)         │  │
│  │     ↓                                                │  │
│  │  2. Send to model                                   │  │
│  │     ↓                                                │  │
│  │     ├─ Input too large? → ContextWindowOverflow     │  │
│  │     │                      ↓                         │  │
│  │     │              conversation_manager             │  │
│  │     │              .reduce_context()                │  │
│  │     │                      ↓                         │  │
│  │     │              Retry event loop                 │  │
│  │     │                                                │  │
│  │  3. Model generates response                        │  │
│  │     ↓                                                │  │
│  │     ├─ Output hit max_tokens? → MaxTokensReached    │  │
│  │     │                             (FAIL - no retry) │  │
│  │     │                                                │  │
│  │  4. Add response to messages                        │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  5. conversation_manager.apply_management()                │
│     (trim if needed)                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Code Examples

### Example 1: Using SlidingWindowConversationManager (Default)

```python
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

# Default configuration
agent = Agent(
    conversation_manager=SlidingWindowConversationManager(
        window_size=40,                  # Keep last 40 messages
        should_truncate_results=True     # Truncate large tool outputs
    )
)

# The conversation manager will automatically:
# - After each turn: trim messages if count > 40
# - On ContextWindowOverflow: truncate tool results then remove old messages
```

### Example 2: Custom Window Size

```python
# Keep only last 10 messages (aggressive trimming)
agent = Agent(
    conversation_manager=SlidingWindowConversationManager(
        window_size=10,
        should_truncate_results=True
    )
)

# Useful for:
# - Cost optimization (smaller context = lower costs)
# - Short-term memory agents
# - High-frequency interactions
```

### Example 3: Disable Tool Result Truncation

```python
# Don't truncate tool results, just remove old messages
agent = Agent(
    conversation_manager=SlidingWindowConversationManager(
        window_size=40,
        should_truncate_results=False  # Never truncate tool results
    )
)

# Use when:
# - Tool results are critical to the task
# - You prefer removing old messages instead of truncating recent tool outputs
```

### Example 4: Using SummarizingConversationManager

```python
from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import SummarizingConversationManager

# Create a model for summarization (can be different from main agent model)
summarizer_model = BedrockModel(
    model_id="anthropic.claude-3-haiku-20240307-v1:0"  # Fast, cheap model
)

agent = Agent(
    model=BedrockModel(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
    conversation_manager=SummarizingConversationManager(
        model=summarizer_model,
        summarization_prompt="Provide a concise summary of the conversation so far."
    )
)

# The conversation manager will:
# - Do nothing until ContextWindowOverflow occurs
# - Then: summarize old messages using the summarizer_model
# - Replace old messages with a single summary message
```

### Example 5: Using NullConversationManager

```python
from strands import Agent
from strands.agent.conversation_manager import NullConversationManager

# Keep all messages forever
agent = Agent(
    conversation_manager=NullConversationManager()
)

# Use when:
# - You know the conversation will be short
# - You want full control over message management
# - You handle context manually via hooks

# Warning: Will raise ContextWindowOverflowException if input gets too large
```

### Example 6: Handling MaxTokensReachedException

```python
from strands import Agent
from strands.types.exceptions import MaxTokensReachedException

agent = Agent()

try:
    response = agent.invoke("Generate a very long research report...")
except MaxTokensReachedException as e:
    print("Model hit max_tokens limit!")

    # Solutions:
    # 1. Increase max_tokens in model config
    # 2. Break task into smaller chunks
    # 3. Prompt model to continue from where it left off

    # Option 1: Increase max_tokens
    from strands.models import BedrockModel
    agent_with_higher_limit = Agent(
        model=BedrockModel(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            config={"max_tokens": 8000}  # Increase from default
        )
    )

    # Option 2: Break into chunks
    response_part1 = agent.invoke("Generate the introduction and background...")
    response_part2 = agent.invoke("Now generate the methodology section...")

    # Option 3: Continue generation
    agent.invoke("Continue the report from where you left off...")
```

---

## Common Issues and Solutions

### Issue 1: "MaxTokensReachedException during single-turn research report"

**Scenario:**
```python
agent = Agent(
    conversation_manager=SlidingWindowConversationManager(
        should_truncate_results=True  # You expected this to help
    )
)

# This fails with MaxTokensReachedException
response = agent.invoke("Generate a comprehensive 10-page research report on AI safety")
```

**Why it fails:**
- `should_truncate_results` only helps with **INPUT** size (tool results in history)
- Your issue is **OUTPUT** size (the report itself is too long)
- Conversation managers cannot prevent max_tokens in model responses

**Solution:**
```python
# Option A: Increase max_tokens
from strands.models import BedrockModel

agent = Agent(
    model=BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        config={"max_tokens": 8000}  # Claude default is 4096
    )
)

# Option B: Break into multiple turns
agent.invoke("Generate the research report outline with section headings")
agent.invoke("Write the introduction and background sections")
agent.invoke("Write the methodology section")
# ... continue for each section
```

### Issue 2: "ContextWindowOverflowException even with small window_size"

**Scenario:**
```python
agent = Agent(
    conversation_manager=SlidingWindowConversationManager(window_size=5)
)

# Still hits ContextWindowOverflow!
response = agent.invoke("Analyze this document: " + huge_document)
```

**Why it fails:**
- The **single message** (user input + huge document) is too large
- Window size limits message **count**, not individual message **size**
- Even with window_size=1, a single huge message will overflow

**Solution:**
```python
# Option A: Use a tool to provide the document
from strands.tools import tool

@tool
def get_document():
    """Returns the document content"""
    return huge_document

agent = Agent(tools=[get_document])
agent.invoke("Use get_document tool to retrieve the document, then analyze it")

# Option B: Chunk the document
chunks = split_document_into_chunks(huge_document)
for chunk in chunks:
    agent.invoke(f"Analyze this section: {chunk}")
```

### Issue 3: "Tool results keep getting truncated"

**Scenario:**
```python
agent = Agent(
    conversation_manager=SlidingWindowConversationManager(
        should_truncate_results=True  # Default
    )
)

# Tool results are being replaced with "The tool result was too large!"
```

**Solution:**
```python
# Option A: Disable truncation
agent = Agent(
    conversation_manager=SlidingWindowConversationManager(
        should_truncate_results=False  # Never truncate
    )
)

# Option B: Use SummarizingConversationManager
# It summarizes old context instead of truncating tool results
agent = Agent(
    conversation_manager=SummarizingConversationManager(
        model=BedrockModel(model_id="anthropic.claude-3-haiku-20240307-v1:0")
    )
)
```

---

## Best Practices

### 1. Choose the Right Conversation Manager

| Use Case | Recommended Manager | Configuration |
|----------|---------------------|---------------|
| General purpose agents | `SlidingWindowConversationManager` | Default (window_size=40) |
| Cost-sensitive applications | `SlidingWindowConversationManager` | Small window (10-20) |
| Long-running conversations needing full context | `SummarizingConversationManager` | With efficient model |
| Short, single-turn interactions | `NullConversationManager` | N/A |
| Debugging/development | `NullConversationManager` | See full history |

### 2. Configure max_tokens Appropriately

```python
# Match max_tokens to your use case
configs = {
    "short_responses": {"max_tokens": 1024},      # Quick answers
    "standard": {"max_tokens": 4096},             # Default
    "long_form": {"max_tokens": 8000},            # Reports, articles
    "maximum": {"max_tokens": 200000},            # Claude 3.5 Sonnet v2 max
}

agent = Agent(
    model=BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        config=configs["long_form"]
    )
)
```

### 3. Monitor Conversation Manager Behavior

```python
from strands.hooks import AfterInvocationEvent

def monitor_message_count(event: AfterInvocationEvent):
    agent = event.agent
    manager = agent.conversation_manager

    print(f"Messages in history: {len(agent.messages)}")
    print(f"Messages removed: {manager.removed_message_count}")

agent = Agent(hooks=[monitor_message_count])
```

### 4. Handle Tool Results Strategically

```python
# If tool results are very large, summarize them in the tool itself
from strands.tools import tool

@tool
def analyze_large_dataset():
    """Analyzes a large dataset and returns summary"""
    raw_results = perform_analysis()  # Returns huge data

    # Summarize before returning to agent
    summary = {
        "total_records": len(raw_results),
        "key_insights": extract_insights(raw_results),
        "statistics": calculate_stats(raw_results)
    }

    return summary  # Small, concise result
```

### 5. Test with Edge Cases

```python
# Test that your conversation manager handles edge cases
test_cases = [
    "Single huge message",
    "Many small messages",
    "Tool use followed immediately by overflow",
    "Long-running conversation (100+ turns)",
]

for test_case in test_cases:
    agent = Agent()  # Fresh agent
    try:
        # Run your test scenario
        pass
    except Exception as e:
        print(f"Failed on: {test_case}, Error: {e}")
```

---

## Summary

### Key Takeaways

1. **Conversation managers manage INPUT, not OUTPUT**
   - They help with `ContextWindowOverflowException` ✅
   - They don't help with `MaxTokensReachedException` ❌

2. **Two modes of operation:**
   - `apply_management()`: Proactive trimming after each turn
   - `reduce_context()`: Reactive recovery from overflow

3. **`should_truncate_results` is SlidingWindow-only:**
   - Only available in `SlidingWindowConversationManager`
   - Truncates tool results before removing old messages
   - Default is `True`

4. **Choose the right tool for the job:**
   - Need recent context? → `SlidingWindowConversationManager`
   - Need full context? → `SummarizingConversationManager`
   - Short conversations? → `NullConversationManager`

### Quick Reference

```python
# Default (recommended for most cases)
agent = Agent()

# Custom sliding window
agent = Agent(
    conversation_manager=SlidingWindowConversationManager(
        window_size=20,
        should_truncate_results=True
    )
)

# With summarization
agent = Agent(
    conversation_manager=SummarizingConversationManager(
        model=BedrockModel(model_id="anthropic.claude-3-haiku-20240307-v1:0")
    )
)

# No management
agent = Agent(conversation_manager=NullConversationManager())
```

---

## Related Documentation

- [Agent Loop Documentation](https://strandsagents.com/latest/user-guide/concepts/agents/agent-loop/)
- [MaxTokensReachedException Guide](https://strandsagents.com/latest/user-guide/concepts/agents/agent-loop/#maxtokensreachedexception)
- Source Code:
  - `src/strands/agent/conversation_manager/`
  - `src/strands/event_loop/event_loop.py`
  - `src/strands/agent/agent.py`
