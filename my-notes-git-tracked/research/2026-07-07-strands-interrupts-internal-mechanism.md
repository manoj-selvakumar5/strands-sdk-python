# Human-in-the-Loop Interrupts in Strands — Internal Mechanism

**Date:** 2026-07-07
**Context:** Research

## Summary
How human-in-the-loop interrupts work internally in the Strands Python SDK, traced end-to-end through the actual source (`strands-py/src/strands/…`). Interrupts use a **raise-and-replay** model: the tool runs, raises an exception to unwind the whole loop, and on resume the tool re-runs from the top with the human's answer returned instead of raised.

> Note: the practice file `personal/practice/interrupt/debug_interrupt_tool.py` references the old pre-monorepo `src/strands/…` paths. The code is identical; all paths below use the current monorepo layout `strands-py/src/strands/…`.

---

## 1. The core idea

An interrupt lets a tool (or a hook) say *"I need a human to answer something before I can continue"* — and have the **entire agent event loop unwind cleanly, return control to your code, and later resume as if nothing happened.**

The key insight: Strands does **not** suspend a coroutine or freeze a thread. There is no paused stack sitting in memory. Instead it uses **raise-and-replay**:

- **Phase 1 (trigger):** the tool runs, calls `interrupt()`, which **raises a Python exception** that unwinds the whole loop. The agent returns with `stop_reason="interrupt"`.
- **Phase 2 (resume):** you call the agent again with the human's answer. Strands **re-runs the tool from the top**, but this time `interrupt()` **returns the answer instead of raising**. The tool finishes normally.

So the tool function body executes *twice*. Everything before the `interrupt()` call runs twice; the `interrupt()` call is the pivot point that raises the first time and returns the second time. This is why interrupt-bearing tools must be **idempotent up to the interrupt point**.

```
        Phase 1                              Phase 2
   agent("schedule...")                 agent([responses])
        │                                    │
   tool runs ──► interrupt() RAISES     tool runs ──► interrupt() RETURNS "PST"
        │                                    │
   loop unwinds                         tool finishes
        │                                    │
   stop_reason="interrupt"             stop_reason="end_turn"
```

---

## 2. The data structures

Three small types in `strands-py/src/strands/interrupt.py` carry the whole feature.

**`Interrupt`** — the payload handed back to you (`interrupt.py:11`):

```python
@dataclass
class Interrupt:
    id: str          # deterministic, derived from tool_use id + name
    name: str        # your label, e.g. "timezone_selection"
    reason: Any = None    # human-readable prompt
    response: Any = None  # filled in by YOU on resume; None until then
```

**`InterruptException`** — the control-flow signal (`interrupt.py:32`). It just wraps an `Interrupt`. Raising it is how the tool escapes:

```python
class InterruptException(Exception):
    def __init__(self, interrupt: Interrupt) -> None:
        self.interrupt = interrupt
```

**`_InterruptState`** — per-agent state, lives on `agent._interrupt_state` (`interrupt.py:40`). This is the memory that survives *between* the two agent calls:

```python
@dataclass
class _InterruptState:
    interrupts: dict[str, Interrupt] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)  # tool_use_message, tool_results
    activated: bool = False   # True == "we are parked waiting for a human"
```

Note `context` — when the loop parks, it stashes the model's tool-use message and any already-completed tool results here, so the replay doesn't re-call the model or re-run sibling tools.

---

## 3. The one method that does the magic: `_Interruptible.interrupt()`

Both tool contexts and hook events inherit from `_Interruptible` (`strands-py/src/strands/types/interrupt.py:79`). This method is the heart of the whole feature:

```python
def interrupt(self, name: str, reason: Any = None, response: Any = None) -> Any:
    # 1. find the agent (tools store it as `agent`, hook events as `source`)
    for attr_name in ["agent", "source"]:
        if hasattr(self, attr_name):
            agent = getattr(self, attr_name)
            break
    else:
        raise RuntimeError("agent instance attribute not set")

    id = self._interrupt_id(name)          # 2. deterministic id (see below)
    state = agent._interrupt_state

    # 3. THE PIVOT — setdefault is idempotent across the two phases
    interrupt_ = state.interrupts.setdefault(id, Interrupt(id, name, reason, response))

    # 4. Phase 2: a response was filled in by resume() → RETURN it
    if interrupt_.response is not None:
        return interrupt_.response

    # 4. Phase 1: no response yet → RAISE to unwind the loop
    raise InterruptException(interrupt_)
```

Everything hinges on **step 3 + step 4**:

- **Phase 1:** `state.interrupts` is empty. `setdefault` inserts a fresh `Interrupt` (with `response=None`). `response is None` → **raise `InterruptException`**.
- **Phase 2:** `resume()` (section 6) has already put an `Interrupt` with `response="PST"` into `state.interrupts` under this same `id`. `setdefault` finds the existing one and returns it. `response is not None` → **return `"PST"`**.

The `id` must be **identical across both phases** for `setdefault` to line up. That's why it's derived deterministically, not randomly (`types/tools.py:153`):

```python
def _interrupt_id(self, name: str) -> str:
    return f"v1:tool_call:{self.tool_use['toolUseId']}:{uuid.uuid5(uuid.NAMESPACE_OID, name)}"
```

`uuid5` is a *hash*, not a random uuid — same `toolUseId` + same `name` → same id, every time. (The model reuses the same `toolUseId` on replay because the loop feeds it the stashed tool-use message instead of re-calling the model — see section 5.)

---

## 4. Two ways to trigger an interrupt

There are **two origins**, and they diverge only in *where the `InterruptException` is caught*. `debug_interrupt_tool.py` uses path B; the docstring example in `interrupt.py` uses path A.

### Path A — from a hook (before the tool even runs)

A `BeforeToolCallEvent` hook calls `event.interrupt(...)`. The exception is caught in the **hook registry** (`hooks/registry.py:301`):

```python
async def invoke_callbacks_async(self, event):
    interrupts: dict[str, Interrupt] = {}
    for callback in self.get_callbacks_for_event(event):
        try:
            maybe = callback(event)
            ...
        except InterruptException as exception:
            interrupt = exception.interrupt
            if interrupt.name in interrupts:                 # one interrupt per name
                raise ValueError(f"interrupt_name=<{interrupt.name}> | used more than once")
            interrupts[interrupt.name] = interrupt           # collect, don't propagate
    return event, list(interrupts.values())                  # hand interrupts back
```

The registry **swallows** the exception and returns the interrupts as data. Back in the executor (`tools/executors/_executor.py:153`):

```python
before_event, interrupts = await ToolExecutor._invoke_before_tool_call_hook(...)
if interrupts:
    yield ToolInterruptEvent(tool_use, interrupts)   # emit as an event
    return                                            # tool never runs
```

### Path B — from inside the tool itself

The tool runs and calls `tool_context.interrupt(...)`. Here the exception propagates out of your function and is caught in the **`@tool` decorator's `stream()`** (`tools/decorator.py:641`):

```python
else:
    result = await asyncio.to_thread(self._tool_func, **validated_input)  # your fn runs here
    yield self._wrap_tool_result(tool_use_id, result)

except InterruptException as e:
    yield ToolInterruptEvent(tool_use, [e.interrupt])   # same event type as path A
    return
```

**Both paths converge on the same event: `ToolInterruptEvent`.** That is the unified signal the rest of the loop understands. The comment in `debug_interrupt_tool.py:41` ("THE PATH DIVERGES HERE") is describing exactly this A-vs-B fork — but note it's a *convergence* at the event level.

---

## 5. Phase 1 traversal — the interrupt propagating up and out

Follow the `ToolInterruptEvent` upward. It bubbles through the executor's inner stream loop (`_executor.py:234`), which does one important thing — **registers the interrupt in agent state** so resume can find it later by id:

```python
async for event in selected_tool.stream(tool_use, invocation_state, **kwargs):
    if isinstance(event, ToolInterruptEvent):
        for interrupt in event.interrupts:
            agent._interrupt_state.interrupts.setdefault(interrupt.id, interrupt)
        yield event
        return
```

(For a tool-context interrupt, this `setdefault` is a no-op — `interrupt()` itself already inserted it into `state.interrupts` at section 3, step 3. It matters for sub-agent-as-tool interrupts propagated from elsewhere.)

Then it reaches the event loop's tool handler (`event_loop/event_loop.py:790`):

```python
async for tool_event in tool_events:
    if isinstance(tool_event, ToolInterruptEvent):
        interrupts.extend(tool_event["tool_interrupt_event"]["interrupts"])
    yield tool_event
```

And the crucial parking logic (`event_loop.py:807`):

```python
if interrupts:
    # stash what we need to replay without re-calling the model or sibling tools
    agent._interrupt_state.context = {"tool_use_message": message, "tool_results": tool_results}
    agent._interrupt_state.activate()          # activated = True

    agent.event_loop_metrics.end_cycle(...)
    yield EventLoopStopEvent(
        "interrupt", message, agent.event_loop_metrics,
        invocation_state["request_state"],
        interrupts,                             # ← carried out to the caller
        structured_output=structured_output_result,
    )
    return                                       # loop stops here
```

`activate()` sets `activated = True` (`interrupt.py:57`). This flag is what makes Phase 2 behave differently.

Finally, in `agent.py:1299`, the stop event is unpacked into the object you receive:

```python
if isinstance(event, EventLoopStopEvent):
    agent_result = AgentResult(*event["stop"])   # interrupts is a field on it
```

So `result.stop_reason == "interrupt"` and `result.interrupts == [Interrupt(...)]`.

**At this point nothing is suspended.** The stack has fully unwound. The only thing "remembering" the interrupt is the plain data in `agent._interrupt_state` (`activated=True`, the interrupt dict, and the stashed context). That is also precisely why interrupts are **session-serializable** — `_InterruptState.to_dict()`/`from_dict()` (`interrupt.py:120`) let a session manager persist this across processes.

---

## 6. Phase 2 traversal — resume and replay

You call `agent(responses)` where `responses` is a list of `interruptResponse` blocks. The first thing `invoke_async` does is `agent._interrupt_state.resume(prompt)` (`agent.py:1158`).

`resume()` (`interrupt.py:72`) validates and **injects the human answers into the stored interrupts**:

```python
def resume(self, prompt):
    if not self.activated:
        return                      # not parked → normal prompt, do nothing

    if not isinstance(prompt, list):
        raise TypeError("... must resume from interrupt with list of interruptResponse's")

    contents = cast(list[InterruptResponseContent], prompt)
    for content in contents:
        interrupt_id = content["interruptResponse"]["interruptId"]
        interrupt_response = content["interruptResponse"]["response"]
        if interrupt_id not in self.interrupts:
            raise KeyError(f"interrupt_id=<{interrupt_id}> | no interrupt found")
        self.interrupts[interrupt_id].response = interrupt_response   # ← the answer lands
    self.context["responses"] = contents
```

Now the interrupt sitting in `state.interrupts[id]` has `response="PST"`. That is the value `interrupt()` will return on replay.

There's also a guard on the way in: if you send `interruptResponse` blocks but the agent is *not* parked, `agent.py:1438` raises `"Received interrupt responses but agent is not in interrupt state."` — a common gotcha when session state wasn't persisted.

Then the event loop runs again, but now `activated` short-circuits the expensive parts:

**(a) Skip the model** (`event_loop.py:283`) — don't ask the LLM what to do; it already asked for this tool:

```python
if agent._interrupt_state.activated:
    stop_reason = "tool_use"
    message = agent._interrupt_state.context["tool_use_message"]   # the stashed message
```

**(b) Re-inject completed results, re-run only the interrupted tool** (`event_loop.py:741`):

```python
if agent._interrupt_state.activated:
    tool_results.extend(agent._interrupt_state.context["tool_results"])   # siblings already done
    tool_use_ids = {tr["toolUseId"] for tr in tool_results}
    tool_uses = [tu for tu in tool_uses if tu["toolUseId"] not in tool_use_ids]  # only the parked one
```

So the model is not called and sibling tools are not re-run — only the interrupted tool replays. It replays with the **same `toolUseId`** (from the stashed message), so `_interrupt_id()` recomputes the **same id**, so `setdefault` in `interrupt()` finds the response-bearing `Interrupt` → **`interrupt()` returns `"PST"`** and your tool continues past the `interrupt()` call into the rest of its body.

**(c) Deactivate and finish** — when the replayed tool completes without raising a new interrupt, the loop reaches `event_loop.py:827`:

```python
agent._interrupt_state.deactivate()   # clears interrupts, context, activated=False
```

and proceeds normally: builds the `toolResult` message, recurses into the event loop, the model now sees the tool result, produces its final answer, and you get `stop_reason="end_turn"`.

The nested-interrupt case (docstring flowchart, `interrupt.py:13`) falls out naturally: if the replayed tool calls `interrupt()` a *second* time with a *new* name, that new interrupt has no response yet → raises again → loop parks again → you answer again.

---

## 7. The whole path on one page

| Step | Phase 1 (trigger) | Phase 2 (resume) |
|---|---|---|
| Entry | `agent("schedule…")` | `agent([interruptResponse…])` |
| `resume()` | no-op (`activated=False`) | injects `response` into stored interrupt (`interrupt.py:103`) |
| Model call | runs, emits `tool_use` | **skipped** — replayed from `context["tool_use_message"]` (`event_loop.py:283`) |
| Tool selection | all tool_uses run | **only** the interrupted one; siblings' results re-injected (`event_loop.py:741`) |
| `interrupt()` | `setdefault` inserts fresh (response=None) → **raises** (`interrupt.py:111`) | `setdefault` finds existing (response set) → **returns** (`interrupt.py:109`) |
| Caught at | decorator `:641` (tool) or registry `:335` (hook) | not raised — tool runs to completion |
| Event | `ToolInterruptEvent` → registered in state (`_executor.py:239`) | normal `ToolResultEvent` |
| Loop | `activate()`, stash context, `yield EventLoopStopEvent("interrupt", …)` (`event_loop.py:807`) | `deactivate()` (`event_loop.py:827`), recurse, model produces answer |
| Result | `stop_reason="interrupt"`, `result.interrupts=[…]` | `stop_reason="end_turn"` |

---

## 8. The three invariants worth internalizing

1. **Idempotency up to the interrupt point.** The tool body runs fully on both phases up to the `interrupt()` call. Any side effect *before* it (writing a file, charging a card) happens **twice**. Put side effects *after* the interrupt, or make them idempotent.

2. **Deterministic id = the correlation key.** `uuid5(NAMESPACE_OID, name)` over the `toolUseId` is what lets a fully-unwound stack "reconnect" to the right answer on replay. This is also why the interrupt `name` must be **stable across the two phases** and **unique per hook callback** (`registry.py:337` rejects duplicate names within one event).

3. **State, not stack, is what persists.** Because parking is just `activated=True` + a dict of data (`_InterruptState`), interrupts survive serialization. With a `SessionManager`, `to_dict()`/`from_dict()` (`interrupt.py:120–140`) let the human answer arrive **days later, in a different process** — the replay is reconstructed purely from persisted data, never from a live suspended coroutine.

## References
- `strands-py/src/strands/interrupt.py` — `Interrupt`, `InterruptException`, `_InterruptState`
- `strands-py/src/strands/types/interrupt.py` — `_Interruptible.interrupt()`, `InterruptResponse(Content)`
- `strands-py/src/strands/types/tools.py:153` — `ToolContext._interrupt_id()`
- `strands-py/src/strands/hooks/registry.py:301` — hook-path exception capture
- `strands-py/src/strands/tools/decorator.py:641` — tool-path exception capture
- `strands-py/src/strands/tools/executors/_executor.py` — `ToolInterruptEvent` emission + state registration
- `strands-py/src/strands/event_loop/event_loop.py` — parking (`:807`), model-skip (`:283`), tool-filter (`:741`), deactivate (`:827`)
- `strands-py/src/strands/agent/agent.py` — `resume()` call (`:1158`), `AgentResult` build (`:1299`), not-in-interrupt guard (`:1438`)
- `personal/practice/interrupt/debug_interrupt_tool.py` — companion debugger walkthrough
