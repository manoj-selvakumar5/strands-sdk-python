# Comprehensive Guide to Streaming and Async in Strands SDK

## Overview

The Strands SDK provides robust async and streaming support through a layered architecture. Here's everything you need to know:

---

## 1. Core Async Patterns

### Three Ways to Call an Agent

**Synchronous (Default)**
```python
agent = Agent()
result = agent("hello")  # Blocks until complete
```
- Uses `ThreadPoolExecutor` internally
- Calls `asyncio.run()` under the hood (agent.py:404)

**Async**
```python
result = await agent.invoke_async("hello")  # Non-blocking
```
- Returns `AgentResult` when complete
- Full async/await support

**Streaming Async**
```python
async for event in agent.stream_async("hello"):
    if "data" in event:
        print(event["data"], end="")
```
- Yields events as they occur
- Real-time access to model output

---

## 2. Streaming Architecture

### The Streaming Pipeline

```
Model.stream() → process_stream() → event_loop_cycle() → agent.stream_async() → User
```

### Key Components

**Model Interface** (src/strands/models/model.py:68)
```python
class Model(abc.ABC):
    @abc.abstractmethod
    def stream(
        self,
        messages: Messages,
        tool_specs: Optional[list[ToolSpec]] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        """Stream conversation with the model."""
```

**Stream Processing** (src/strands/event_loop/streaming.py:276)
```python
async def process_stream(chunks: AsyncIterable[StreamEvent]) -> AsyncGenerator[TypedEvent, None]:
    """Processes response stream, constructing messages and extracting metrics."""
```

---

## 3. Stream Event Types

### Raw Stream Events (from Model Provider)

Defined in `src/strands/types/streaming.py`:

- **`MessageStartEvent`** - Message begins
- **`ContentBlockStartEvent`** - Content block starts (text or tool use)
- **`ContentBlockDeltaEvent`** - Incremental content updates
  - `text` - Text fragments
  - `toolUse` - Tool input fragments
  - `reasoningContent` - Reasoning text/signature
  - `citation` - Citation information
- **`ContentBlockStopEvent`** - Content block ends
- **`MessageStopEvent`** - Message ends with stop reason
- **`MetadataEvent`** - Usage metrics and trace info

### Typed Events (Emitted to User)

Defined in `src/strands/types/_events.py`:

**Processing Events**
- `InitEventLoopEvent` - Agent execution starts
- `StartEventLoopEvent` - Event loop cycle begins
- `ModelStreamChunkEvent` - Raw chunk from model (has `.chunk` property)

**Content Events**
- `TextStreamEvent` - Text streaming (has `"data"` key)
- `ToolUseStreamEvent` - Tool input streaming (has `"current_tool_use"`)
- `ReasoningTextStreamEvent` - Reasoning content (has `"reasoningText"`)
- `CitationStreamEvent` - Citation data (has `"citation"`)

**Completion Events**
- `ModelMessageEvent` - Model message added to history
- `ToolResultMessageEvent` - Tool results added
- `AgentResultEvent` - Final result available
- `EventLoopStopEvent` - Event loop completed

---

## 4. Stream Processing Flow

### State Management (src/strands/event_loop/streaming.py:287)

```python
state = {
    "message": {"role": "assistant", "content": []},
    "text": "",                    # Accumulated text
    "current_tool_use": {},        # Current tool being invoked
    "reasoningText": "",           # Accumulated reasoning
    "citationsContent": [],        # Citation data
}
```

### Processing Stages

1. **`handle_message_start()`** - Sets message role
2. **`handle_content_block_start()`** - Initializes tool use if present
3. **`handle_content_block_delta()`** - Accumulates content:
   - Text chunks → `state["text"]`
   - Tool input → `state["current_tool_use"]["input"]`
   - Reasoning → `state["reasoningText"]`
4. **`handle_content_block_stop()`** - Finalizes content:
   - Parses JSON tool input
   - Adds completed content to message
5. **`handle_message_stop()`** - Returns stop reason
6. **`extract_usage_metrics()`** - Extracts tokens/latency

---

## 5. Callback Handlers

### Built-in Handlers (src/strands/handlers/callback_handler.py)

**PrintingCallbackHandler** (default)
```python
handler = PrintingCallbackHandler()
agent = Agent(callback_handler=handler)
```
- Streams text to stdout
- Shows tool invocations
- Displays reasoning content

**null_callback_handler**
```python
agent = Agent(callback_handler=None)  # Disables output
```

**CompositeCallbackHandler**
```python
handler = CompositeCallbackHandler(handler1, handler2, handler3)
agent = Agent(callback_handler=handler)  # Multiple handlers
```

### Custom Handler

```python
def custom_handler(**kwargs):
    data = kwargs.get("data", "")           # Text content
    complete = kwargs.get("complete", False) # Final chunk?
    current_tool_use = kwargs.get("current_tool_use", {})
    reasoningText = kwargs.get("reasoningText", "")

    if data:
        print(f"Text: {data}")
    if current_tool_use:
        print(f"Tool: {current_tool_use['name']}")
    if reasoningText:
        print(f"Reasoning: {reasoningText}")

agent = Agent(callback_handler=custom_handler)
```

---

## 6. Advanced Streaming Patterns

### Pattern 1: Accumulate Full Response

```python
async def get_full_response(agent, prompt):
    full_text = ""
    async for event in agent.stream_async(prompt):
        if "data" in event:
            full_text += event["data"]
    return full_text
```

### Pattern 2: Track Tool Usage

```python
async def track_tools(agent, prompt):
    tools_used = []
    async for event in agent.stream_async(prompt):
        if "current_tool_use" in event:
            tools_used.append(event["current_tool_use"])
    return tools_used
```

### Pattern 3: Raw Stream Events

```python
async def process_raw_events(agent, prompt):
    async for event in agent.stream_async(prompt):
        if "event" in event:
            chunk = event["event"]
            if "contentBlockDelta" in chunk:
                delta = chunk["contentBlockDelta"]["delta"]
                # Process raw delta
```

### Pattern 4: Access Reasoning Content

```python
async def get_reasoning(agent, prompt):
    reasoning = []
    async for event in agent.stream_async(prompt):
        if "reasoningText" in event:
            reasoning.append(event["reasoningText"])
    return "".join(reasoning)
```

---

## 7. Event Loop Integration

### How Streaming Fits (src/strands/event_loop/event_loop.py:144)

```python
async for event in stream_messages(agent.model, agent.system_prompt, agent.messages, tool_specs):
    if not isinstance(event, ModelStopReason):
        yield event  # Stream to user

stop_reason, message, usage, metrics = event["stop"]
```

### Retry Logic for Throttling (event_loop.py:126)

- Exponential backoff: 4s → 8s → 16s → 32s → 64s → 240s
- Max 6 attempts
- Emits `EventLoopThrottleEvent` on retry

---

## 8. Practical Examples

### Example 1: Simple Async Agent (tests_integ/test_agent_async.py:12)

```python
@pytest.mark.asyncio
async def test_stream_async(agent):
    stream = agent.stream_async("hello")

    exp_message = ""
    async for event in stream:
        if "event" in event and "contentBlockDelta" in event["event"]:
            exp_message += event["event"]["contentBlockDelta"]["delta"]["text"]

    # Final message matches streamed content
    assert agent.messages[-1]["content"][0]["text"] == exp_message
```

### Example 2: Custom Callback (tests_integ/test_stream_agent.py:14)

```python
class ToolCountingCallbackHandler:
    def __init__(self):
        self.tool_count = 0
        self.message_count = 0

    def callback_handler(self, **kwargs):
        current_tool_use = kwargs.get("current_tool_use", {})
        if current_tool_use:
            self.tool_count += 1
            print(f"Tool #{self.tool_count}: {current_tool_use['name']}")

agent = Agent(callback_handler=handler.callback_handler)
```

---

## 9. Key Configuration

### Enable/Disable Streaming per Model

```python
from strands.models import BedrockModel

model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0",
    streaming=True,  # Enable streaming (default)
)
```

### Agent Configuration

```python
agent = Agent(
    model=model,
    callback_handler=custom_handler,  # Or None, or PrintingCallbackHandler()
    tools=[...],
)
```

---

## 10. Important Implementation Details

### Thread Pool Usage (agent.py:406)
- Sync calls use `ThreadPoolExecutor`
- Prevents blocking the main thread
- Each invocation gets its own executor

### Blank Text Handling (streaming.py:39)
- Empty text in tool use messages is removed
- Empty text without tool use becomes `"[blank text]"`
- Prevents model API errors

### State Persistence (agent.py:287)
- `invocation_state` passed through event loop
- Includes `request_state` for custom data
- Available in tool implementations

### Error Handling
- `ModelThrottledException` → Retry with backoff
- `ContextWindowOverflowException` → Reduce conversation
- `MaxTokensReachedException` → Hard failure
- Other exceptions → Wrapped in `EventLoopException`

---

## Summary

**Streaming**: Real-time access to model output via async generators
**Events**: Typed event system with multiple event types
**Handlers**: Callback system for processing events
**Async**: Full async/await support throughout
**Flexibility**: Works with all model providers that implement `stream()`

The SDK provides a clean abstraction over model-specific streaming formats, normalizing them into a consistent event system that's easy to work with.
