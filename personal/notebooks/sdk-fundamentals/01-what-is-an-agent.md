# What is an Agent?

The single most important concept in the Strands SDK.

---

## AI Agent vs Plain Model Call

A **plain model call** is simple: you send text, you get text back. Like texting a friend who can only reply with words.

```python
# Plain model call (NOT using Strands SDK)
response = bedrock_client.invoke_model(prompt="What is 2+2?")
# Returns: "2+2 is 4"
```

An **agent** is much more. It's a model with superpowers:

| Component | Analogy | What it does |
|-----------|---------|-------------|
| **Model** | Brain | Thinks, understands, generates text |
| **Tools** | Hands | Can perform actions (check weather, send email, query database) |
| **Messages** | Memory | Remembers the conversation so far |
| **Hooks** | Reflexes | Automatic reactions at key moments (log events, approve tool calls) |
| **System prompt** | Personality | Permanent instructions ("you are a helpful assistant") |
| **Conversation manager** | Forgetting old memories | Keeps memory from overflowing |

```python
# Agent (using Strands SDK)
from strands import Agent, tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"72F and sunny in {city}"

agent = Agent(tools=[get_weather])
result = agent("What's the weather in Seattle?")
# The model DECIDES to call get_weather, READS the result, then RESPONDS:
# "The weather in Seattle is 72F and sunny!"
```

The key difference: the model **decides** what to do. It reads the tool descriptions, picks the right tool, generates the right arguments, reads the results, and formulates a response. The SDK orchestrates this dance.

---

## The Agent Class -- What It Holds

The `Agent` class lives in `src/strands/agent/agent.py` (lines 86-891). When you create an agent, it sets up all these attributes:

### Core attributes

**`self.model`** (line ~187)
- **What:** The AI model to use (e.g., BedrockModel, OpenAIModel)
- **Analogy:** The agent's brain
- **Default:** `BedrockModel()` (Amazon Bedrock with Claude)
- **You set it:** `Agent(model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514"))`

**`self.system_prompt`** (line ~192)
- **What:** Permanent instructions sent to the model every call
- **Analogy:** The agent's personality and job description
- **Default:** A generic helpful assistant prompt
- **You set it:** `Agent(system_prompt="You are a weather expert.")`

**`self.messages`** (line ~202)
- **What:** List of all messages in the conversation (user messages, assistant responses, tool results)
- **Analogy:** The agent's memory of the conversation
- **Default:** Empty list `[]`
- **You read it:** `agent.messages` after calling the agent

**`self.callback_handler`** (line ~195)
- **What:** Function that handles streaming output (prints text as it's generated)
- **Analogy:** A live transcriber writing down what the agent says in real-time
- **Default:** Built-in handler that prints to console
- **Disable streaming:** `Agent(callback_handler=None)`

### Tool system

**`self.tool_registry`** (line ~211)
- **What:** A registry (dictionary) of all available tools
- **Analogy:** A catalog of buttons the agent can press
- **You set it:** `Agent(tools=[get_weather, calculator])`
- **You inspect it:** `agent.tool_registry.registry.keys()`

**`self.tool_executor`**
- **What:** Executes tools when the model requests them
- **Default:** Parallel execution using thread pool

### Lifecycle and state

**`self.hooks`** (line ~222)
- **What:** Registry of lifecycle callbacks
- **Analogy:** Sensors that fire at key moments
- **You set it:** `Agent(hooks=[MyHookProvider()])`

**`self.conversation_manager`** (line ~230)
- **What:** Manages message history size to prevent context window overflow
- **Analogy:** A librarian who removes old books when shelves are full
- **Default:** `SlidingWindowConversationManager` (keeps recent messages)

**`self.state`** (line ~240)
- **What:** A dictionary for storing arbitrary user data across calls
- **Analogy:** A scratch pad the agent carries around
- **You read/write it:** `agent.state["user_name"] = "Alice"`

**`self.event_loop_metrics`** (line ~243)
- **What:** Performance statistics (latency, token count, cycle count)
- **You read it:** `agent.event_loop_metrics`

### Internal state

**`self._invocation_lock`** (line ~245)
- **What:** Threading lock preventing concurrent agent calls
- **Why:** Calling the agent from two threads at once would corrupt messages

**`self._interrupt_state`** (line ~245)
- **What:** Tracks interrupt (pause/resume) state for human-in-the-loop workflows
- **See:** `../interrupt/` tutorial for details

---

## What Happens When You Call `agent("hello")`

When you write `result = agent("hello")`, **8 functions** are called in sequence. Here's the complete chain:

### 1. `__call__` (agent.py:335)
- **What it does:** Entry point. Converts your call to async.
- **Why it exists:** So you can write `agent("hello")` instead of `await agent.invoke_async("hello")`
- **Analogy:** The front desk receptionist who takes your request

### 2. `invoke_async` (agent.py:376)
- **What it does:** Calls `stream_async()` and collects all events into an `AgentResult`
- **Why it exists:** Separates "stream events in real time" from "give me the final result"
- **Analogy:** Waits for the entire response before handing it to you

### 3. `stream_async` (agent.py:539)
- **What it does:** Acquires the invocation lock, converts your prompt to messages, starts the event loop
- **Why it exists:** This is the main orchestrator -- handles lock, prompt conversion, tracing
- **Analogy:** The project manager who prepares everything before work begins

### 4. `_run_loop` (agent.py:643)
- **What it does:** Invokes before/after hooks, appends your message to conversation, calls the event loop, applies conversation management
- **Why it exists:** Manages the lifecycle around the event loop (hooks fire here)
- **Analogy:** The ceremony around the actual work -- announcements before and after

### 5. `_execute_event_loop_cycle` (agent.py:702)
- **What it does:** Calls `event_loop_cycle()` and processes its events
- **Why it exists:** Bridge between agent and event loop module
- **Analogy:** The dispatcher who sends your request to the engine room

### 6. `event_loop_cycle` (event_loop.py:78)
- **What it does:** THE CORE. Calls the model, handles the response, executes tools if needed
- **Why it exists:** This is the reasoning engine -- the heart of the SDK
- **Analogy:** The engine room where all the real work happens
- **See:** `02-the-event-loop.md` for deep dive

### 7. `_handle_model_execution` (event_loop.py:275) / `_handle_tool_execution` (event_loop.py:421)
- **What they do:** Model execution streams the AI response. Tool execution runs requested tools.
- **Why they exist:** Separate the two main phases of each cycle
- **Analogy:** Kitchen (model) and delivery (tools)

### 8. `recurse_event_loop` (event_loop.py:236)
- **What it does:** After tools finish, calls `event_loop_cycle()` again so the model can see tool results
- **Why it exists:** The model needs to see tool output before giving a final answer
- **Analogy:** Going back to the kitchen with the delivery receipt

### The call chain visualized:

```
agent("hello")
  |
  v
__call__                    # Entry point
  |
  v
invoke_async                # Collect all events into result
  |
  v
stream_async                # Lock, convert prompt, start loop
  |
  v
_run_loop                   # Before/after hooks, message management
  |
  v
_execute_event_loop_cycle   # Bridge to event loop
  |
  v
event_loop_cycle            # THE CORE ENGINE
  |
  +--> _handle_model_execution    # Call the AI model
  |         |
  |         v
  |    Model responds with tool_use
  |         |
  +--> _handle_tool_execution     # Execute requested tools
  |         |
  |         v
  |    recurse_event_loop         # Go back to event_loop_cycle
  |         |
  |         v
  |    event_loop_cycle (again)   # Model sees tool results
  |         |
  |         v
  |    Model responds with end_turn
  |         |
  v         v
  EventLoopStopEvent              # Done!
  |
  v
AgentResult                       # Returned to you
```

---

## What You Get Back: `AgentResult`

**Source:** `src/strands/agent/agent_result.py`

When the agent finishes, you get an `AgentResult` object with these fields:

| Field | Type | What it means |
|-------|------|--------------|
| `stop_reason` | `str` | Why the agent stopped: `"end_turn"` (normal), `"interrupt"` (paused for human input) |
| `message` | `dict` | The model's last message (contains the response text) |
| `metrics` | `EventLoopMetrics` | Performance stats: latency, token count, cycle count |
| `state` | `dict` | Event loop state (internal) |
| `interrupts` | `list` or `None` | List of `Interrupt` objects if `stop_reason == "interrupt"` |
| `structured_output` | `BaseModel` or `None` | Parsed structured output if you requested it |

```python
result = agent("What is 2+2?")

print(result.stop_reason)   # "end_turn"
print(result.message)       # {"role": "assistant", "content": [{"text": "2+2 is 4"}]}
print(str(result))          # "2+2 is 4"  (the __str__ method extracts the text)
```

---

## Source File Map

Every major file in the SDK and what it does:

| File | What it does | Key classes/functions |
|------|-------------|---------------------|
| `agent/agent.py` | Main Agent class | `Agent`, `__call__`, `stream_async`, `_run_loop` |
| `agent/agent_result.py` | Result object | `AgentResult` |
| `agent/conversation_manager/` | History management | `SlidingWindowConversationManager`, `SummarizingConversationManager` |
| `event_loop/event_loop.py` | Core reasoning loop | `event_loop_cycle`, `_handle_model_execution`, `_handle_tool_execution` |
| `models/model.py` | Model interface | `Model` (ABC) |
| `models/bedrock.py` | Amazon Bedrock adapter | `BedrockModel` |
| `models/anthropic.py` | Anthropic adapter | `AnthropicModel` |
| `models/openai.py` | OpenAI adapter | `OpenAIModel` |
| `tools/decorator.py` | @tool decorator | `tool`, `DecoratorTool` |
| `tools/registry.py` | Tool storage | `ToolRegistry` |
| `tools/executors/` | Tool execution | `ThreadPoolExecutor` |
| `hooks/events.py` | Hook event definitions | `BeforeToolCallEvent`, `AfterModelCallEvent`, etc. |
| `hooks/registry.py` | Hook dispatch | `HookRegistry`, `HookProvider` |
| `types/content.py` | Message types | `Message`, `ContentBlock` |
| `types/tools.py` | Tool types | `ToolSpec`, `ToolUse`, `ToolResult`, `ToolContext` |
| `types/streaming.py` | Streaming types | `StreamEvent`, `StopReason` |
| `interrupt.py` | Human-in-the-loop | `Interrupt`, `InterruptException`, `_InterruptState` |
| `telemetry/` | Observability | `EventLoopMetrics`, OpenTelemetry tracing |
| `session/` | Session persistence | Save/restore conversations |
| `multiagent/` | Multi-agent patterns | `GraphAgent`, `SwarmAgent` |
| `experimental/bidi/` | Real-time streaming | `BidiAgent` (audio/real-time) |
