# The Event Loop -- The Core Reasoning Engine

This is the most important file in the SDK to understand. Everything flows through here.

**Source:** `src/strands/event_loop/event_loop.py`

---

## What is an Event Loop? (General Concept)

An **event loop** is a program that waits for things to happen and responds to them. It runs in a cycle:

1. Wait for an event
2. Process the event
3. Go back to step 1

### Real-world examples:

- **Restaurant waiter:** Takes order (event) -> goes to kitchen (process) -> brings food back (result) -> takes dessert order -> repeat
- **Web browser:** Waits for click (event) -> runs JavaScript (process) -> updates page (result) -> waits for next click
- **Game engine:** Check input (event) -> update physics (process) -> render frame (result) -> repeat 60 times/second

### The SDK's event loop is different

The SDK's event loop is NOT a persistent loop that runs forever. It's a **recursive async generator** that processes one request and stops. Here's what that means:

- **Recursive:** After executing tools, it calls itself again so the model can see tool results
- **Async:** Uses `async`/`await` for non-blocking I/O (see `00-python-concepts-for-sdk.md`)
- **Generator:** Uses `yield` to stream events back to the caller in real-time

Each "cycle" of the event loop = one model call + optional tool execution.

---

## The State Machine

Think of the event loop as a state machine with a few states:

```
                    +------------------+
                    |   START          |
                    |   Call Model     |
                    +------------------+
                            |
                            v
                    +------------------+
                    |  Model returns   |
                    |  with stop_reason|
                    +------------------+
                       /    |    \
                      /     |     \
              "end_turn" "tool_use" "max_tokens"
                    /       |          \
                   v        v           v
            +---------+ +----------+ +----------+
            |  DONE   | | Execute  | |  ERROR   |
            | Return  | |  Tools   | |  Throw   |
            | result  | +----------+ +----------+
            +---------+      |
                             v
                      +----------+
                      | RECURSE  |
                      | Go back  |
                      | to START |
                      +----------+
```

---

## The `event_loop_cycle()` Function -- Line by Line

**Source:** `src/strands/event_loop/event_loop.py:78-233`

This is the main function. Here's what each section does:

### Lines 78-128: Function Signature

```python
async def event_loop_cycle(
    agent,                      # The Agent instance
    invocation_state,           # State shared across cycles
    cycle_trace,                # Trace for observability
    structured_output_context,  # For structured output parsing
) -> AsyncGenerator:
```

It's an `async` generator (uses `yield`), meaning it produces events as they happen.

### Lines 130-140: Setup

```python
yield StartEventLoopEvent()    # Signal: "cycle starting"
tracer = get_tracer()          # Set up observability tracing
cycle_span = tracer.start_event_loop_cycle_span(...)  # Start timing this cycle
```

### Lines 142-160: Phase 1 -- Model Execution

This is where the SDK decides whether to call the model:

```python
# Case 1: Resuming from interrupt -- skip model, use saved tool request
if agent._interrupt_state.activated:
    stop_reason = "tool_use"
    message = agent._interrupt_state.context["tool_use_message"]

# Case 2: Latest message already has tool request -- skip model
elif _has_tool_use_in_latest_message(agent.messages):
    stop_reason = "tool_use"
    message = agent.messages[-1]

# Case 3: Normal -- call the model
else:
    model_events = _handle_model_execution(agent, ...)
    async for model_event in model_events:
        yield model_event  # Stream model output to caller in real-time

    stop_reason, message = model_event["stop"]
```

Three paths, one outcome: a `stop_reason` and a `message`.

### Lines 162-195: Phase 2 -- Handle Stop Reason

```python
# max_tokens: Model ran out of tokens mid-response. Unrecoverable.
if stop_reason == "max_tokens":
    raise MaxTokensReachedException(...)

# tool_use: Model wants to call tools. Execute them.
if stop_reason == "tool_use":
    tool_events = _handle_tool_execution(agent, message, ...)
    async for tool_event in tool_events:
        yield tool_event  # Stream tool events to caller

    # After tools finish, check if we should continue or stop
    # (see _handle_tool_execution for details)
    return
```

### Lines 197-233: Phase 3 -- End Conditions

If we get here, `stop_reason` is `"end_turn"` -- the model is done.

```python
# Check if structured output was requested but not provided
if structured_output_context.is_enabled and not structured_output_result:
    # Force model to provide structured output
    recurse_event_loop(...)  # Call ourselves again
    return

# Normal end -- yield final stop event
yield EventLoopStopEvent(
    "end_turn",        # Why we stopped
    message,           # The model's response
    metrics,           # Performance data
    state,             # Event loop state
)
```

---

## Stop Reasons -- What Each Means

| Stop Reason | What Happened | What Happens Next |
|-------------|--------------|-------------------|
| `"end_turn"` | Model finished speaking, no tool calls | Agent returns result to you |
| `"tool_use"` | Model wants to call one or more tools | Event loop executes tools, then recurses |
| `"max_tokens"` | Model hit token limit mid-response | `MaxTokensReachedException` thrown (error) |
| `"interrupt"` | Tool or hook triggered human-in-the-loop pause | Agent returns result with `interrupts` list |

Most common flow: model is called -> returns `"tool_use"` -> tools execute -> recurse -> model sees results -> returns `"end_turn"` -> done.

---

## The Recursion Pattern

When the model says "I want to use a tool", the event loop:
1. Executes the tool
2. Appends the tool result to messages
3. **Calls itself again** (`recurse_event_loop()`) so the model can see the tool result
4. The model generates a response based on the tool result
5. If the model wants another tool, repeat from step 1

This can happen multiple times:

```
Cycle 1: Model says "I'll check weather" -> tool_use
  -> Execute weather_tool -> Result: "72F sunny"
  -> recurse_event_loop()

Cycle 2: Model says "Now I'll check calendar" -> tool_use
  -> Execute calendar_tool -> Result: "3 meetings today"
  -> recurse_event_loop()

Cycle 3: Model says "The weather is 72F and you have 3 meetings" -> end_turn
  -> Done! Return result.
```

The SDK has a `max_cycles` limit (default: 20) to prevent infinite loops.

---

## Model Execution Deep Dive: `_handle_model_execution()`

**Source:** `event_loop.py:275-418`

What happens when the model is called:

### Step 1: Before hooks fire
```python
await agent.hooks.invoke_callbacks_async(BeforeModelCallEvent(agent=agent, ...))
```
Hooks can inspect or modify the call before it happens.

### Step 2: Call the model
```python
async for event in stream_messages(agent, ...):
    yield event  # Stream each chunk to caller in real-time
```

The model streams its response. Each chunk is yielded to the caller immediately -- this is how you see text appear word-by-word in real-time.

### Step 3: Collect response
Chunks are assembled into a complete `Message`:
```python
message = {"role": "assistant", "content": [{"text": "The weather is..."}]}
```

### Step 4: After hooks fire
```python
event, _ = await agent.hooks.invoke_callbacks_async(
    AfterModelCallEvent(agent=agent, message=message, ...)
)
if event.retry:
    continue  # Retry the model call!
```

The `AfterModelCallEvent` hook can request a **retry** -- useful for handling model errors gracefully.

### Step 5: Append to conversation
```python
agent.messages.append(message)
```

The model's response is added to conversation history.

---

## Tool Execution Deep Dive: `_handle_tool_execution()`

**Source:** `event_loop.py:421-536`

What happens when tools are executed:

### Step 1: Extract tool requests
The model's message contains `toolUse` blocks:
```python
# Model message:
{"role": "assistant", "content": [
    {"text": "I'll check the weather"},
    {"toolUse": {"toolUseId": "abc", "name": "get_weather", "input": {"city": "Seattle"}}}
]}
```

### Step 2: Handle interrupt state
If resuming from interrupt, restore partial results and only run remaining tools:
```python
if agent._interrupt_state.activated:
    tool_results.extend(agent._interrupt_state.context["tool_results"])
    # Filter out already-completed tools
    tool_uses = [t for t in tool_uses if t["toolUseId"] not in completed_ids]
```

### Step 3: Execute tools
```python
tool_events = agent.tool_executor._execute(agent, tool_uses, ...)
async for tool_event in tool_events:
    if isinstance(tool_event, ToolInterruptEvent):
        interrupts.extend(...)  # Collect interrupts
    yield tool_event
```

Tools run (by default in parallel). Each tool produces a `ToolResult`.

### Step 4: Handle interrupts
If any tool or hook raised an interrupt:
```python
if interrupts:
    agent._interrupt_state.context = {"tool_use_message": message, "tool_results": tool_results}
    agent._interrupt_state.activate()
    yield EventLoopStopEvent("interrupt", message, ..., interrupts)
    return  # Stop the loop
```

### Step 5: Append results and continue
```python
tool_result_message = {
    "role": "user",
    "content": [{"toolResult": result} for result in tool_results]
}
agent.messages.append(tool_result_message)
```

Tool results are added as a **user message** (so the model can read them).

### Step 6: Recurse or stop
```python
if stop_event_loop:
    yield EventLoopStopEvent("end_turn", ...)  # Forced stop
else:
    recurse_event_loop(...)  # Call event_loop_cycle again
```

---

## Complete Traced Example

Request: `agent("What's the weather in Seattle?")`

### Before event loop:
```python
agent.messages = []
```

### Step 1: User message appended (in _run_loop)
```python
agent.messages = [
    {"role": "user", "content": [{"text": "What's the weather in Seattle?"}]}
]
```

### Step 2: event_loop_cycle -- Cycle 1
Model is called. Model responds:
```python
agent.messages = [
    {"role": "user", "content": [{"text": "What's the weather in Seattle?"}]},
    {"role": "assistant", "content": [
        {"text": "I'll check the weather for you."},
        {"toolUse": {"toolUseId": "abc", "name": "get_weather", "input": {"city": "Seattle"}}}
    ]}
]
```
`stop_reason = "tool_use"` -- model wants to call `get_weather`.

### Step 3: _handle_tool_execution
`get_weather(city="Seattle")` is called. Returns `"72F and sunny"`.

### Step 4: Tool result appended
```python
agent.messages = [
    {"role": "user", "content": [{"text": "What's the weather in Seattle?"}]},
    {"role": "assistant", "content": [
        {"text": "I'll check the weather for you."},
        {"toolUse": {"toolUseId": "abc", "name": "get_weather", "input": {"city": "Seattle"}}}
    ]},
    {"role": "user", "content": [
        {"toolResult": {"toolUseId": "abc", "content": [{"text": "72F and sunny"}], "status": "success"}}
    ]}
]
```

### Step 5: recurse_event_loop -- Cycle 2
Model is called again. It sees the tool result and generates:
```python
agent.messages = [
    ...  # Previous 3 messages
    {"role": "assistant", "content": [
        {"text": "The weather in Seattle is 72F and sunny!"}
    ]}
]
```
`stop_reason = "end_turn"` -- model is done.

### Step 6: EventLoopStopEvent
```python
yield EventLoopStopEvent("end_turn", message, metrics, state)
```

### Final result:
```python
result = AgentResult(stop_reason="end_turn", message=..., metrics=...)
print(result)  # "The weather in Seattle is 72F and sunny!"
```

---

## Key Source Locations

| Function | Line | What it does |
|----------|------|-------------|
| `event_loop_cycle` | 78 | Main event loop -- model + tool + recurse |
| `_handle_model_execution` | 275 | Calls model with retry/hook support |
| `_handle_tool_execution` | 421 | Executes tools, handles interrupts |
| `recurse_event_loop` | 236 | Calls event_loop_cycle again after tools |
| `validate_and_prepare_tools` | 430 | Extracts and validates toolUse blocks |
| `stream_messages` | (streaming.py) | Low-level model streaming |
