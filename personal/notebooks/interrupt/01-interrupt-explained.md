# How the Interrupt System Works in Strands SDK

A complete walkthrough of the human-in-the-loop interrupt system, from triggering to resuming.

**Prerequisite:** Read `00-python-basics-for-interrupts.md` first if you're not familiar with exceptions, dataclasses, or protocols.

---

## What Problem Does Interrupt Solve?

Imagine you build an AI agent that can delete files, send emails, or make purchases. You don't want it doing these things without your permission. The interrupt system lets you say: **"Stop and ask me before you do that."**

It's a **pause button with a question attached**.

---

## The 3 Core Classes

### 1. `Interrupt` — the question card

**File:** `src/strands/interrupt.py:11-29`

```python
@dataclass
class Interrupt:
    id: str        # Unique ID (auto-generated)
    name: str      # A name you pick, like "for_delete_tool"
    reason: Any    # Why the interrupt was raised ("need approval")
    response: Any  # The user's answer (None until answered)
```

Think of this as a sticky note. It has a question (`reason`) and a blank space for the answer (`response`). When first created, `response` is `None` — nobody has answered yet.

### 2. `InterruptException` — the stop signal

**File:** `src/strands/interrupt.py:32-37`

```python
class InterruptException(Exception):
    def __init__(self, interrupt: Interrupt):
        self.interrupt = interrupt
```

This is a custom exception that carries an `Interrupt` object inside it. When raised, it stops execution. When caught, the interrupt data can be extracted.

### 3. `_InterruptState` — the saved game

**File:** `src/strands/interrupt.py:40-120`

```python
@dataclass
class _InterruptState:
    interrupts: dict[str, Interrupt]  # All pending interrupts
    context: dict[str, Any]           # Saved execution state
    activated: bool                    # Is the agent paused?
```

This tracks the overall interrupt state of the agent. Key methods:
- `activate()` — flip the "paused" flag on
- `deactivate()` — clear everything, resume normal operation
- `resume(prompt)` — process user responses and fill in interrupt answers

---

## The Key Method: `interrupt()` — the dual-call trick

**File:** `src/strands/types/interrupt.py:82-111`

This is the most important function in the entire system. It gets called from hooks and tools:

```python
def interrupt(self, name, reason=None, response=None):
    id = self._interrupt_id(name)
    state = agent._interrupt_state

    # Get existing interrupt OR create a new one
    interrupt_ = state.interrupts.setdefault(id, Interrupt(id, name, reason, response))

    if interrupt_.response is not None:
        return interrupt_.response      # RESUME path: return the answer

    raise InterruptException(interrupt_) # FIRST CALL path: stop everything
```

The magic: **this function runs TWICE**.

| Call | `response` value | What happens |
|------|-----------------|-------------|
| 1st (initial) | `None` | Raises `InterruptException` — agent stops |
| 2nd (after user responds) | `"APPROVE"` | Returns `"APPROVE"` — execution continues |

The `setdefault()` call is what makes this work. On the 1st call, it creates a new `Interrupt` with `response=None`. On the 2nd call, it finds the existing `Interrupt` (which now has `response="APPROVE"` because `resume()` filled it in) and returns it.

---

## Two Places You Can Trigger Interrupts

### A. From a Hook (before the tool runs)

**File:** `src/strands/hooks/events.py:119-155`

Hooks run **before** a tool executes. `BeforeToolCallEvent` implements `_Interruptible`, so you can call `event.interrupt()`:

```python
class ToolInterruptHook(HookProvider):
    def register_hooks(self, registry, **kwargs):
        registry.add_callback(BeforeToolCallEvent, self.approve)

    def approve(self, event: BeforeToolCallEvent):
        if event.tool_use["name"] != "delete_tool":
            return

        approval = event.interrupt("for_delete", reason="needs approval")
        if approval != "APPROVE":
            event.cancel_tool = "rejected"
```

When the `InterruptException` is raised, the hook registry catches it at `src/strands/hooks/registry.py:238`:

```python
try:
    callback(event)
except InterruptException as exception:
    interrupts[interrupt.name] = exception.interrupt
```

### B. From a Tool (during execution)

**File:** `src/strands/types/tools.py:129-160`

Tools can interrupt mid-execution using `ToolContext`:

```python
@tool(name="sensitive_op", context=True)
def func(action: str, tool_context: ToolContext) -> str:
    response = tool_context.interrupt("confirm", reason=f"About to {action}")
    return f"User said: {response}"
```

When the `InterruptException` is raised, the tool decorator catches it at `src/strands/tools/decorator.py:609-611`:

```python
except InterruptException as e:
    yield ToolInterruptEvent(tool_use, [e.interrupt])
    return
```

---

## The Complete Flow: 11 Steps

### Phase 1: Interrupt Raised (Steps 1-6)

**Step 1:** You call the agent.
```python
result = agent("delete object X")
```

**Step 2:** The agent sends the prompt to the model.

**Step 3:** The model responds with a tool use request (e.g., call `delete_tool`).

**Step 4:** The event loop enters tool execution (`src/strands/event_loop/event_loop.py:460`).

**Step 5:** The hook/tool calls `event.interrupt("name", reason="...")`:
- Creates an `Interrupt` with `response=None`
- `InterruptException` is raised
- Caught by hook registry or tool decorator
- Converted to `ToolInterruptEvent`

**Step 6:** The event loop collects interrupts (`event_loop.py:485-503`):
```python
if interrupts:
    agent._interrupt_state.context = {
        "tool_use_message": message,
        "tool_results": tool_results
    }
    agent._interrupt_state.activate()
    yield EventLoopStopEvent("interrupt", ...)
    return
```

The agent saves its state (which tool was requested, which tools already completed), activates the interrupt flag, and returns an `AgentResult` with `stop_reason="interrupt"`.

### Phase 2: User Responds (Steps 7-8)

**Step 7:** You inspect the result and build responses:
```python
assert result.stop_reason == "interrupt"
responses = [
    {"interruptResponse": {"interruptId": interrupt.id, "response": "APPROVE"}}
    for interrupt in result.interrupts
]
```

**Step 8:** You call the agent again with responses:
```python
result = agent(responses)
```

### Phase 3: Agent Resumes (Steps 9-11)

**Step 9:** `_interrupt_state.resume(responses)` processes your answers (`interrupt.py:69-102`):
- Finds each interrupt by ID
- Sets `interrupt.response = "APPROVE"`

**Step 10:** The event loop checks `_interrupt_state.activated` (`event_loop.py:143-146`):
```python
if agent._interrupt_state.activated:
    stop_reason = "tool_use"
    message = agent._interrupt_state.context["tool_use_message"]
```
It skips calling the model again and goes straight to tool execution using the saved state.

The event loop restores partial results and only re-runs interrupted tools (`event_loop.py:460-465`):
```python
if agent._interrupt_state.activated:
    tool_results.extend(agent._interrupt_state.context["tool_results"])
    tool_use_ids = {r["toolUseId"] for r in tool_results}
    tool_uses = [t for t in tool_uses if t["toolUseId"] not in tool_use_ids]
```

**Step 11:** The hook/tool calls `event.interrupt()` again. This time `interrupt.response` is `"APPROVE"`, so it **returns** the response instead of raising an exception. The tool completes normally. `_interrupt_state.deactivate()` clears all state (`event_loop.py:505`), and the agent loop continues.

---

## Visual Flow

```
YOU                          AGENT                        HOOK/TOOL
 |                             |                              |
 |-- "delete X" ------------->|                              |
 |                             |-- model says: use tool ----->|
 |                             |                              |
 |                             |                   interrupt() called
 |                             |                   response=None -> RAISE
 |                             |<---- InterruptException -----|
 |                             |                              |
 |                             | saves state, activates       |
 |<-- result.interrupts -------|                              |
 |                             |                              |
 | (user decides)              |                              |
 |                             |                              |
 |-- [interruptResponse] ---->|                              |
 |                             | resume() fills response      |
 |                             |-- re-runs tool execution --->|
 |                             |                              |
 |                             |                   interrupt() called
 |                             |                   response="APPROVE" -> RETURN
 |                             |                   tool continues normally
 |                             |<---- tool result ------------|
 |                             |                              |
 |                             | deactivates, continues loop  |
 |<-- final answer ------------|                              |
```

---

## Important Rules and Constraints

1. **One interrupt per callback** — the hook registry enforces uniqueness by name (`registry.py:240-243`)
2. **Tool calls only** — interrupts are currently only supported during tool execution (`event_loop.py:143` comment)
3. **Partial results preserved** — if the model requested 3 tools and tool #2 interrupts, tool #1's result is saved and not re-executed on resume
4. **Session-managed** — interrupt state serializes via `to_dict()`/`from_dict()` so it can survive across sessions
5. **Unique IDs** — each interrupt gets a deterministic ID: `v1:{context_type}:{tool_or_node_id}:{uuid5(name)}`
6. **Multi-agent support** — `BeforeNodeCallEvent` in graph/swarm patterns also implements `_Interruptible` (`hooks/events.py:306`)

---

## File Reference

| File | What it does |
|------|-------------|
| `src/strands/interrupt.py` | `Interrupt`, `InterruptException`, `_InterruptState` classes |
| `src/strands/types/interrupt.py` | `_Interruptible` protocol, `InterruptResponse` TypedDict |
| `src/strands/hooks/events.py:119` | `BeforeToolCallEvent` with interrupt support |
| `src/strands/hooks/registry.py:238` | Where `InterruptException` is caught in hooks |
| `src/strands/tools/decorator.py:609` | Where `InterruptException` is caught in tools |
| `src/strands/event_loop/event_loop.py:143` | Event loop checks interrupt state |
| `src/strands/event_loop/event_loop.py:460` | Tool execution with interrupt handling |
| `src/strands/event_loop/event_loop.py:485` | Interrupt activation and state saving |
| `src/strands/types/tools.py:129` | `ToolContext` with interrupt support |
| `src/strands/agent/agent_result.py:35` | `AgentResult.interrupts` field |
