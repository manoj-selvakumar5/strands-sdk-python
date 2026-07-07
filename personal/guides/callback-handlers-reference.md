# Callback Handlers in Strands Agents SDK - Comprehensive Guide

## What is a Callback Handler?

A **callback handler** is a callable object (function or class with `__call__` method) that receives real-time streaming events during agent execution. It's the mechanism for intercepting and processing events as they happen.

### Key Characteristics:
- **Signature**: `callback_handler(**kwargs)` - receives arbitrary keyword arguments
- **Invocation Point**: Called for each event where `event.is_callback_event == True`
- **Purpose**: Real-time monitoring, custom output formatting, integration with external systems

### Defined in:
- `src/strands/handlers/callback_handler.py:7-77`

---

## How stream_async Works

**File**: `src/strands/agent/agent.py:518-604`

`stream_async` is an **async generator method** that processes prompts and yields events as an async iterator.

### Execution Flow:

```
1. User calls: agent.stream_async("prompt")
          |
          v
2. Convert prompt to messages
          |
          v
3. Start internal event loop (_run_loop)
          |
          v
4. For each event from the loop:
    |-- event.prepare(invocation_state)  # Add state context
    |-- if event.is_callback_event:
    |     |-- callback_handler(**event.as_dict())  # Invoke handler
    |     +-- yield event.as_dict()                # Yield to caller
    +-- else: (skip - not yielded)
          |
          v
5. After loop completes:
    |-- Create AgentResult
    |-- callback_handler(result=result)
    +-- yield AgentResultEvent
```

### Key Code:
```python
async for event in events:
    event.prepare(invocation_state=merged_state)

    if event.is_callback_event:
        as_dict = event.as_dict()
        callback_handler(**as_dict)  # Callback invoked first
        yield as_dict                 # Then yielded to caller
```

### Important Behaviors:
- **Async-only**: No synchronous equivalent (use regular `agent()` call for sync)
- **Callback + Iterator**: Events are sent to callback handler AND yielded
- **Not all events trigger callbacks**: Events with `is_callback_event = False` are skipped

---

## All Streaming Events

**File**: `src/strands/types/_events.py`

### Event Base Class

```python
class TypedEvent(dict):
    @property
    def is_callback_event(self) -> bool:
        return True  # Default: triggers callback

    def as_dict(self) -> dict:
        return {**self}

    def prepare(self, invocation_state: dict) -> None:
        ...  # Optional state merging
```

---

### Lifecycle Events

| Event | Key in kwargs | Description | Callback? |
|-------|---------------|-------------|-----------|
| `InitEventLoopEvent` | `init_event_loop: True` | Agent execution starting | Yes |
| `StartEvent` | `start: True` | Event loop cycle beginning (deprecated) | Yes |
| `StartEventLoopEvent` | `start_event_loop: True` | Event loop processing started | Yes |
| `ForceStopEvent` | `force_stop: True`, `force_stop_reason` | Agent forcibly stopped | Yes |
| `EventLoopStopEvent` | `stop: tuple` | Execution completed | **No** |
| `AgentResultEvent` | `result: AgentResult` | Final agent result | Yes |

---

### Model Stream Events

| Event | Key in kwargs | Description | Callback? |
|-------|---------------|-------------|-----------|
| `ModelStreamChunkEvent` | `event: StreamEvent` | Raw streaming chunk | Yes |
| `TextStreamEvent` | `data: str`, `delta` | Text content being streamed | Yes |
| `ToolUseStreamEvent` | `current_tool_use: dict`, `delta` | Tool input parameters streaming | Yes |
| `CitationStreamEvent` | `callback: {citation, delta}` | Citation data streaming | Yes |
| `ReasoningTextStreamEvent` | `reasoningText: str`, `reasoning: True` | Model reasoning content | Yes |
| `ReasoningSignatureStreamEvent` | `reasoning_signature: str` | Reasoning signature | Yes |
| `ReasoningRedactedContentStreamEvent` | `reasoningRedactedContent: bytes` | Redacted reasoning | Yes |
| `ModelStopReason` | `stop: tuple` | Model finished generating | **No** |
| `ModelMessageEvent` | `message: Message` | Complete message created | Yes |
| `StructuredOutputEvent` | `structured_output: BaseModel` | Structured output parsed | Yes |

---

### Tool Events

| Event | Key in kwargs | Description | Callback? |
|-------|---------------|-------------|-----------|
| `ToolUseStreamEvent` | `current_tool_use: dict` | Tool being executed | Yes |
| `ToolStreamEvent` | `tool_stream_event: {tool_use, data}` | Tool yielded intermediate data | Yes |
| `ToolResultEvent` | `tool_result: ToolResult` | Tool execution completed | **No** |
| `ToolResultMessageEvent` | `message: Message` | Tool results as message | Yes |
| `ToolCancelEvent` | `tool_cancel_event: {tool_use, message}` | Tool call cancelled | Yes |
| `ToolInterruptEvent` | `tool_interrupt_event: {tool_use, interrupts}` | Tool interrupted | Yes |

---

### Multi-Agent Events (Swarm/Graph)

| Event | Key in kwargs | Description | Callback? |
|-------|---------------|-------------|-----------|
| `MultiAgentNodeStartEvent` | `type: "multiagent_node_start"`, `node_id`, `node_type` | Node begins execution | Yes |
| `MultiAgentNodeStopEvent` | `type: "multiagent_node_stop"`, `node_id`, `node_result` | Node stops | Yes |
| `MultiAgentNodeStreamEvent` | `type: "multiagent_node_stream"`, `node_id`, `event` | Forwarded agent events | Yes |
| `MultiAgentHandoffEvent` | `type: "multiagent_handoff"`, `from_node_ids`, `to_node_ids` | Control handoff | Yes |
| `MultiAgentNodeCancelEvent` | `type: "multiagent_node_cancel"`, `node_id`, `message` | Node cancelled | Yes |
| `MultiAgentNodeInterruptEvent` | `type: "multiagent_node_interrupt"`, `node_id`, `interrupts` | Node interrupted | Yes |
| `MultiAgentResultEvent` | `type: "multiagent_result"`, `result` | Final multi-agent result | Yes |

---

### Other Events

| Event | Key in kwargs | Description | Callback? |
|-------|---------------|-------------|-----------|
| `EventLoopThrottleEvent` | `event_loop_throttled_delay: int` | Rate limiting applied | Yes |

---

## Built-in Callback Handlers

### 1. PrintingCallbackHandler (Default)

```python
class PrintingCallbackHandler:
    def __init__(self, verbose_tool_use: bool = True):
        self.tool_count = 0
        self.previous_tool_use = None
        self._verbose_tool_use = verbose_tool_use

    def __call__(self, **kwargs):
        # Prints reasoningText if present
        # Prints data (streamed text)
        # Tracks and prints tool usage
```

**Behavior**:
- Prints `reasoningText` (Claude's thinking)
- Prints `data` (streamed text content)
- Shows tool usage: `Tool #1: tool_name`

### 2. CompositeCallbackHandler

```python
class CompositeCallbackHandler:
    def __init__(self, *handlers: Callable):
        self.handlers = handlers

    def __call__(self, **kwargs):
        for handler in self.handlers:
            handler(**kwargs)
```

**Purpose**: Combine multiple handlers to process the same events differently.

### 3. null_callback_handler

```python
def null_callback_handler(**_kwargs):
    return None
```

**Purpose**: Discard all output (silent mode).

### Default Behavior:
- No `callback_handler` specified -> `PrintingCallbackHandler()` is used
- `callback_handler=None` explicitly -> `null_callback_handler` is used

---

## Use Cases for Callback Handlers

### 1. Custom Console Output

```python
def custom_output(**kwargs):
    if "data" in kwargs:
        print(f"[AI] {kwargs['data']}", end="")
    if "current_tool_use" in kwargs:
        print(f"\n[TOOL] {kwargs['current_tool_use']['name']}")

agent = Agent(callback_handler=custom_output)
```

### 2. Debugging / Logging All Events

```python
def debug_handler(**kwargs):
    print(f"EVENT: {kwargs}")

agent = Agent(callback_handler=debug_handler)
```

### 3. Buffering for Chat UIs (Show Complete Messages Only)

```python
def message_buffer_handler(**kwargs):
    if "message" in kwargs and kwargs["message"].get("role") == "assistant":
        print(json.dumps(kwargs["message"], indent=2))

agent = Agent(callback_handler=message_buffer_handler)
```

### 4. Real-time Metrics Collection

```python
class MetricsHandler:
    def __init__(self):
        self.token_count = 0
        self.tool_calls = 0

    def __call__(self, **kwargs):
        if "data" in kwargs:
            self.token_count += len(kwargs["data"].split())
        if "current_tool_use" in kwargs:
            self.tool_calls += 1
```

### 5. WebSocket Streaming (Real-time Web Apps)

```python
class WebSocketHandler:
    def __init__(self, websocket):
        self.ws = websocket

    async def __call__(self, **kwargs):
        if "data" in kwargs:
            await self.ws.send(json.dumps({"type": "text", "data": kwargs["data"]}))
        if "result" in kwargs:
            await self.ws.send(json.dumps({"type": "complete"}))
```

### 6. Event Lifecycle Tracking

```python
def event_tracker(**kwargs):
    if kwargs.get("init_event_loop"):
        print("Starting agent...")
    elif kwargs.get("start_event_loop"):
        print("Processing cycle...")
    elif "message" in kwargs:
        print(f"New message: {kwargs['message']['role']}")
    elif kwargs.get("force_stop"):
        print(f"Stopped: {kwargs.get('force_stop_reason')}")
    elif "result" in kwargs:
        print("Complete!")
```

### 7. Multi-Handler Composition

```python
from strands.handlers import CompositeCallbackHandler, PrintingCallbackHandler

composite = CompositeCallbackHandler(
    PrintingCallbackHandler(),       # Default console output
    LoggingHandler(),                # Custom logging
    MetricsHandler(),                # Metrics collection
)
agent = Agent(callback_handler=composite)
```

### 8. Sub-Agent Event Tracking (Multi-Agent Systems)

```python
def multiagent_handler(**kwargs):
    if kwargs.get("type") == "multiagent_node_start":
        print(f"Node {kwargs['node_id']} starting...")
    elif kwargs.get("type") == "multiagent_handoff":
        print(f"Handoff: {kwargs['from_node_ids']} -> {kwargs['to_node_ids']}")
    elif kwargs.get("type") == "multiagent_node_stream":
        # Forward nested event
        nested_event = kwargs.get("event", {})
        if "data" in nested_event:
            print(f"[{kwargs['node_id']}] {nested_event['data']}", end="")
```

---

## Key Patterns Summary

| Pattern | When to Use |
|---------|-------------|
| `if "data" in kwargs` | Streaming text content |
| `if "reasoningText" in kwargs` | Claude's reasoning/thinking |
| `if "current_tool_use" in kwargs` | Tool execution tracking |
| `if "message" in kwargs` | Complete message created |
| `if "result" in kwargs` | Agent finished (final result) |
| `if kwargs.get("init_event_loop")` | Agent starting |
| `if kwargs.get("force_stop")` | Agent forcibly stopped |
| `if kwargs.get("type") == "multiagent_..."` | Multi-agent events |

---

## Best Practices

1. **Keep handlers fast** - They run in the critical path
2. **Handle all event types gracefully** - Use `.get()` for optional fields
3. **Catch exceptions** - Errors in handlers can break agent execution
4. **Use CompositeCallbackHandler** for multiple concerns (logging + output + metrics)
5. **Consider async iterators** for async applications instead of callbacks

---

## Callback Handler vs stream_async

| Aspect | Callback Handler | stream_async |
|--------|------------------|--------------|
| **Execution** | Sync (blocks during handler) | Async (non-blocking) |
| **Control** | Push model (events pushed to you) | Pull model (you consume events) |
| **Best for** | Simple scripts, console apps | Web servers, async frameworks |
| **TypeScript** | Not supported | Use `agent.stream()` |

Both receive the same event types - choose based on your application's execution model.

---

## Source Files

- Handler implementations: `src/strands/handlers/callback_handler.py`
- Event types: `src/strands/types/_events.py`
- stream_async method: `src/strands/agent/agent.py:518-604`
- Official docs: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/streaming/callback-handlers/
