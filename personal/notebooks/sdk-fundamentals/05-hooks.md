# How Hooks Work in the Strands SDK

**Date:** 2026-01-31
**Context:** SDK Fundamentals - Learning Guide
**Source Files:** `src/strands/hooks/events.py`, `src/strands/hooks/registry.py`, `src/strands/hooks/__init__.py`

---

## 1. What Are Hooks?

Hooks are callbacks that run at specific moments during the agent's lifecycle. They let you observe, log, modify, or control agent behavior without changing the agent's core code.

**Plain English:** Every time the agent does something significant -- starts a request, calls the model, runs a tool, finishes a request -- it fires an "event". You can register functions (callbacks) that listen for these events and react to them.

**Analogy:** Think of security cameras in a building. At every entrance, hallway, and room, there is a camera (event). Most cameras just observe and record (logging hooks). But some cameras are connected to door locks -- they can *prevent* someone from entering a room (guard hooks that cancel tool calls) or *make someone try again* (retry hooks). The building operates normally whether the cameras are there or not, but the cameras give you visibility and control.

---

## 2. All Hook Events -- Chronological Order

Here is every hook event that fires during a single agent request, in the order they occur:

### One-Time Event (Agent Creation)

**1. `AgentInitializedEvent`**

Fires once when the agent is created (in `Agent.__init__`), after all components are initialized.

| Field | Type | Description |
|---|---|---|
| `agent` | `Agent` | The fully initialized agent instance |

Use: Setup tasks, registering external resources, validation. Note: only synchronous callbacks are allowed for this event.

---

### Per-Request Events

**2. `BeforeInvocationEvent`**

Fires at the start of every agent call (`agent("hello")`, `agent.stream_async()`, `agent.structured_output()`).

| Field | Type | Writable | Description |
|---|---|---|---|
| `agent` | `Agent` | No | The agent handling the request |
| `invocation_state` | `dict` | No | State passed through the invocation |
| `messages` | `Messages` | Yes | Input messages -- can be modified to redact or transform |

Use: Request-level setup, input validation, PII redaction, metrics start.

**3. `MessageAddedEvent`**

Fires every time a message is added to the conversation history. This fires multiple times per request.

| Field | Type | Description |
|---|---|---|
| `agent` | `Agent` | The agent instance |
| `message` | `Message` | The message that was added |

Use: Logging all messages, auditing, real-time monitoring.

When it fires:
- After user input is added to history
- After assistant (model) response is added
- After tool results are added

**4. `BeforeModelCallEvent`**

Fires just before the SDK calls the model for inference.

| Field | Type | Description |
|---|---|---|
| `agent` | `Agent` | The agent instance |
| `invocation_state` | `dict` | State passed through the invocation |

Use: Logging, latency measurement start, message inspection.

**5. Model streams its response...**

(No hook event during streaming -- the model is generating tokens.)

**6. `AfterModelCallEvent`**

Fires after the model finishes responding.

| Field | Type | Writable | Description |
|---|---|---|---|
| `agent` | `Agent` | No | The agent instance |
| `invocation_state` | `dict` | No | State passed through the invocation |
| `stop_response` | `ModelStopResponse` | No | Model response data (message + stop_reason) |
| `exception` | `Exception` | No | Exception if model call failed |
| `retry` | `bool` | Yes | Set to `True` to discard response and retry |

Use: Latency measurement, response validation, conditional retries, guardrails checking. Note: callbacks fire in **reverse** order (last registered fires first).

**7. `MessageAddedEvent`** (again -- assistant message added)

**8. If the model requested tool use:**

**8a. `BeforeToolCallEvent`**

Fires before each tool execution.

| Field | Type | Writable | Description |
|---|---|---|---|
| `agent` | `Agent` | No | The agent instance |
| `selected_tool` | `AgentTool` | Yes | The tool about to run (can swap it) |
| `tool_use` | `ToolUse` | Yes | Tool parameters (can modify inputs) |
| `invocation_state` | `dict` | No | State passed through the invocation |
| `cancel_tool` | `bool/str` | Yes | Set to cancel the tool call |

Use: Authorization checks, input sanitization, human-in-the-loop approval, tool swapping. Also supports `interrupt()` for human-in-the-loop workflows.

**8b. Tool executes...**

**8c. `AfterToolCallEvent`**

Fires after each tool execution completes.

| Field | Type | Writable | Description |
|---|---|---|---|
| `agent` | `Agent` | No | The agent instance |
| `selected_tool` | `AgentTool` | No | The tool that ran |
| `tool_use` | `ToolUse` | No | The tool parameters that were used |
| `invocation_state` | `dict` | No | State passed through the invocation |
| `result` | `ToolResult` | Yes | The tool result (can modify) |
| `exception` | `Exception` | No | Exception if tool failed |
| `cancel_message` | `str` | No | Set if tool was cancelled |
| `retry` | `bool` | Yes | Set to `True` to retry the tool |

Use: Result validation, cleanup, logging, retry logic. Note: callbacks fire in **reverse** order.

**8d. `MessageAddedEvent`** (tool result message added)

**8e. Loop back to step 4** (model is called again with the tool result)

**9. `AfterInvocationEvent`**

Fires when the entire request is complete (after all model calls and tool executions).

| Field | Type | Description |
|---|---|---|
| `agent` | `Agent` | The agent instance |
| `invocation_state` | `dict` | State passed through the invocation |
| `result` | `AgentResult` | The final result (None for structured_output) |

Use: Cleanup, final logging, metrics collection, state persistence. Note: callbacks fire in **reverse** order.

---

## 3. The HookProvider Pattern

The recommended way to create hooks is by implementing the `HookProvider` protocol.

**Source:** `src/strands/hooks/registry.py`, lines 88-114

```python
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import (
    BeforeInvocationEvent,
    AfterInvocationEvent,
    BeforeToolCallEvent,
    MessageAddedEvent,
)


class MyHookProvider(HookProvider):
    """A hook provider that logs agent activity."""

    def register_hooks(self, registry: HookRegistry) -> None:
        """Register callbacks for the events we care about."""
        registry.add_callback(BeforeInvocationEvent, self.on_request_start)
        registry.add_callback(AfterInvocationEvent, self.on_request_end)
        registry.add_callback(MessageAddedEvent, self.on_message)

    def on_request_start(self, event: BeforeInvocationEvent) -> None:
        print(f"Request started for agent: {event.agent.name}")

    def on_request_end(self, event: AfterInvocationEvent) -> None:
        print(f"Request completed. Result: {event.result}")

    def on_message(self, event: MessageAddedEvent) -> None:
        role = event.message["role"]
        print(f"  [{role}] message added")
```

Then pass it to the agent:

```python
from strands import Agent

agent = Agent(
    hooks=[MyHookProvider()],
    tools=[...]
)
```

You can pass multiple hook providers. Their callbacks are invoked in registration order (except for "after" events, which use reverse order for proper cleanup semantics).

---

## 4. HookRegistry Internals

The `HookRegistry` is the engine that stores and dispatches callbacks.

**Source:** `src/strands/hooks/registry.py`, lines 145-338

### How It Works

```python
class HookRegistry:
    _registered_callbacks: dict[type, list[HookCallback]]
    #                      ^event class -> [callback1, callback2, ...]
```

When you call `registry.add_callback(BeforeInvocationEvent, my_func)`, it stores `my_func` in a list keyed by the event class.

### Dispatching Events

When the SDK fires an event, it calls:

```python
event, interrupts = await registry.invoke_callbacks_async(event)
```

This:
1. Looks up all callbacks registered for that event type
2. Determines ordering (normal or reversed based on `event.should_reverse_callbacks`)
3. Calls each callback with the event object
4. Catches any `InterruptException` and collects them (for human-in-the-loop)
5. Returns the (possibly modified) event and any interrupts

### Event Property Protection

Hook events use write protection -- you can only modify fields that are explicitly marked as writable. Trying to set a non-writable field raises `AttributeError`:

```python
def bad_hook(event: BeforeInvocationEvent):
    event.agent = other_agent  # AttributeError! 'agent' is not writable
    event.messages = [...]     # This works -- 'messages' IS writable
```

This is enforced by `BaseHookEvent.__setattr__()` and `_can_write()` on each event class.

### Async Support

Callbacks can be synchronous or asynchronous:

```python
def sync_callback(event: BeforeInvocationEvent) -> None:
    print("sync")

async def async_callback(event: BeforeInvocationEvent) -> None:
    await some_async_operation()
```

Exception: `AgentInitializedEvent` only accepts synchronous callbacks (because it fires during `__init__` which is not async).

---

## 5. Practical Hook Examples

### Example 1: Logging Hook

Traces every event through the agent lifecycle.

```python
import time
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import (
    BeforeInvocationEvent,
    AfterInvocationEvent,
    BeforeModelCallEvent,
    AfterModelCallEvent,
    BeforeToolCallEvent,
    AfterToolCallEvent,
    MessageAddedEvent,
)


class LoggingHook(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.on_start)
        registry.add_callback(AfterInvocationEvent, self.on_end)
        registry.add_callback(BeforeModelCallEvent, self.on_before_model)
        registry.add_callback(AfterModelCallEvent, self.on_after_model)
        registry.add_callback(BeforeToolCallEvent, self.on_before_tool)
        registry.add_callback(AfterToolCallEvent, self.on_after_tool)
        registry.add_callback(MessageAddedEvent, self.on_message)

    def on_start(self, event: BeforeInvocationEvent):
        print("[LOG] === Request started ===")

    def on_end(self, event: AfterInvocationEvent):
        print("[LOG] === Request completed ===")

    def on_before_model(self, event: BeforeModelCallEvent):
        print("[LOG] Calling model...")

    def on_after_model(self, event: AfterModelCallEvent):
        reason = event.stop_response.stop_reason if event.stop_response else "error"
        print(f"[LOG] Model responded (stop_reason: {reason})")

    def on_before_tool(self, event: BeforeToolCallEvent):
        print(f"[LOG] Running tool: {event.tool_use['name']}")

    def on_after_tool(self, event: AfterToolCallEvent):
        print(f"[LOG] Tool result: {event.result['status']}")

    def on_message(self, event: MessageAddedEvent):
        print(f"[LOG] Message added: role={event.message['role']}")
```

### Example 2: Retry Hook

Retries the model call if it fails with a specific error.

```python
class RetryOnThrottleHook(HookProvider):
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._retry_count = 0

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeModelCallEvent, self.on_before)
        registry.add_callback(AfterModelCallEvent, self.on_after)

    def on_before(self, event: BeforeModelCallEvent):
        # Reset retry counter on new model call
        pass

    def on_after(self, event: AfterModelCallEvent):
        if event.exception and "ThrottlingException" in str(event.exception):
            if self._retry_count < self.max_retries:
                self._retry_count += 1
                print(f"[RETRY] Throttled, retry {self._retry_count}/{self.max_retries}")
                event.retry = True  # This tells the SDK to retry the model call
            else:
                print("[RETRY] Max retries exceeded")
                self._retry_count = 0
        else:
            self._retry_count = 0
```

### Example 3: Guard Hook

Prevents specific tools from running based on authorization logic.

```python
class ToolGuardHook(HookProvider):
    def __init__(self, blocked_tools: list[str]):
        self.blocked_tools = blocked_tools

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self.check_tool)

    def check_tool(self, event: BeforeToolCallEvent):
        tool_name = event.tool_use["name"]
        if tool_name in self.blocked_tools:
            event.cancel_tool = f"Tool '{tool_name}' is not authorized"
            # The tool will NOT execute. An error ToolResult with this
            # message is sent back to the model instead.


# Usage
agent = Agent(
    tools=[delete_file, read_file, write_file],
    hooks=[ToolGuardHook(blocked_tools=["delete_file"])]
)
```

### Example 4: Metrics Hook

Measures latency for model calls and tool executions.

```python
import time


class MetricsHook(HookProvider):
    def __init__(self):
        self.model_latencies = []
        self.tool_latencies = {}
        self._model_start = None
        self._tool_starts = {}

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeModelCallEvent, self.start_model_timer)
        registry.add_callback(AfterModelCallEvent, self.stop_model_timer)
        registry.add_callback(BeforeToolCallEvent, self.start_tool_timer)
        registry.add_callback(AfterToolCallEvent, self.stop_tool_timer)

    def start_model_timer(self, event: BeforeModelCallEvent):
        self._model_start = time.time()

    def stop_model_timer(self, event: AfterModelCallEvent):
        if self._model_start:
            latency = time.time() - self._model_start
            self.model_latencies.append(latency)
            self._model_start = None

    def start_tool_timer(self, event: BeforeToolCallEvent):
        tool_id = event.tool_use["toolUseId"]
        self._tool_starts[tool_id] = time.time()

    def stop_tool_timer(self, event: AfterToolCallEvent):
        tool_id = event.tool_use["toolUseId"]
        if tool_id in self._tool_starts:
            latency = time.time() - self._tool_starts.pop(tool_id)
            tool_name = event.tool_use["name"]
            self.tool_latencies.setdefault(tool_name, []).append(latency)

    def summary(self) -> dict:
        """Get a summary of collected metrics."""
        return {
            "model_calls": len(self.model_latencies),
            "avg_model_latency": sum(self.model_latencies) / max(len(self.model_latencies), 1),
            "tool_calls": {name: len(lats) for name, lats in self.tool_latencies.items()},
            "avg_tool_latency": {
                name: sum(lats) / len(lats)
                for name, lats in self.tool_latencies.items()
            },
        }
```

---

## Quick Reference

```
Agent.__init__  -->  AgentInitializedEvent (once)

agent("hello")  -->  BeforeInvocationEvent
                     |
                     v
               MessageAddedEvent (user)
                     |
                     v
               BeforeModelCallEvent
                     |  (model generates response)
                     v
               AfterModelCallEvent  (can retry)
                     |
                     v
               MessageAddedEvent (assistant)
                     |
                     v  (if tool_use in response)
               BeforeToolCallEvent  (can cancel / interrupt)
                     |  (tool executes)
                     v
               AfterToolCallEvent  (can retry)
                     |
                     v
               MessageAddedEvent (tool result)
                     |
                     v  (loop back to BeforeModelCallEvent)
                     ...
                     |
                     v
               AfterInvocationEvent (done)
```

**Key source files:**
- `src/strands/hooks/events.py` -- All event classes and their fields
- `src/strands/hooks/registry.py` -- `HookRegistry`, `HookProvider` protocol, `HookCallback`, `BaseHookEvent`
- `src/strands/hooks/__init__.py` -- Public exports
