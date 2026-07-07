# Strands SDK vs Raw Nova Sonic Implementation

A detailed comparison between the Strands SDK's bidirectional agent implementation and a raw Nova Sonic implementation ([patrikszepesi/voice-agents](https://github.com/patrikszepesi/voice-agents)).

## Table of Contents
1. [Overview](#overview)
2. [Architecture Comparison](#architecture-comparison)
3. [Code Complexity](#code-complexity)
4. [How Strands SDK Makes Things Easier](#how-strands-sdk-makes-things-easier)
5. [Side-by-Side Code Examples](#side-by-side-code-examples)
6. [Feature Comparison Matrix](#feature-comparison-matrix)
7. [When to Use Which](#when-to-use-which)

---

## Overview

### What is voice-agents?

A single-file (~1,500 lines) Python application that demonstrates how to build a hotel voice assistant using Amazon Nova Sonic. It directly interfaces with the Bedrock bidirectional streaming API.

**Repository:** https://github.com/patrikszepesi/voice-agents

### What is Strands SDK Bidi?

A modular framework (~20 files, ~2,000+ lines) that abstracts bidirectional streaming into reusable components, supporting multiple model providers and integrating with the broader Strands agent ecosystem.

**Location:** `src/strands/experimental/bidi/`

---

## Architecture Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RAW NOVA SONIC (voice-agents)                            │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      hotel_agent.py                                  │  │
│   │                      (Single File)                                   │  │
│   │                                                                      │  │
│   │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │  │
│   │   │ BedrockStream   │  │ AudioStreamer   │  │ ToolProcessor   │    │  │
│   │   │ Manager         │  │                 │  │                 │    │  │
│   │   │                 │  │ - PyAudio       │  │ - DynamoDB      │    │  │
│   │   │ - JSON templates│  │ - Callbacks     │  │ - 3 hardcoded   │    │  │
│   │   │ - Raw events    │  │ - Queues        │  │   tools         │    │  │
│   │   │ - Manual state  │  │                 │  │                 │    │  │
│   │   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘    │  │
│   │            │                    │                    │              │  │
│   │            └────────────────────┴────────────────────┘              │  │
│   │                                 │                                    │  │
│   │                                 ▼                                    │  │
│   │                    ┌─────────────────────┐                          │  │
│   │                    │   Nova Sonic API    │                          │  │
│   │                    │   (Bedrock)         │                          │  │
│   │                    └─────────────────────┘                          │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Pros: Simple, all visible, easy to understand                             │
│   Cons: Not reusable, no abstractions, hardcoded                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRANDS SDK BIDI                                         │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                        Your Application                              │  │
│   │   ┌─────────────────────────────────────────────────────────────┐   │  │
│   │   │  agent = BidiAgent(model=..., tools=[...])                   │   │  │
│   │   │  await agent.run(inputs=[audio.input()], outputs=[...])      │   │  │
│   │   └─────────────────────────────────────────────────────────────┘   │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                     Strands SDK Layer                                │  │
│   │                                                                      │  │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │  │
│   │   │   BidiAgent   │  │  BidiAudioIO  │  │  ToolRegistry │          │  │
│   │   │               │  │  BidiTextIO   │  │               │          │  │
│   │   │ - Lifecycle   │  │               │  │ - @tool deco  │          │  │
│   │   │ - Hooks       │  │ - Abstracted  │  │ - Auto-schema │          │  │
│   │   │ - Sessions    │  │ - Pluggable   │  │ - Validation  │          │  │
│   │   └───────┬───────┘  └───────────────┘  └───────────────┘          │  │
│   │           │                                                         │  │
│   │           ▼                                                         │  │
│   │   ┌───────────────────────────────────────────────────────────┐    │  │
│   │   │              BidiModel (Protocol)                          │    │  │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │    │  │
│   │   │   │ Nova Sonic  │  │   OpenAI    │  │   Gemini    │       │    │  │
│   │   │   │   Model     │  │  Realtime   │  │    Live     │       │    │  │
│   │   │   └─────────────┘  └─────────────┘  └─────────────┘       │    │  │
│   │   └───────────────────────────────────────────────────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Pros: Reusable, multi-model, production-ready, extensible                │
│   Cons: More code to understand, learning curve                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Code Complexity

### Lines of Code Comparison

| Component | voice-agents | Strands SDK |
|-----------|-------------|-------------|
| Main agent logic | ~600 lines | ~400 lines (agent.py + loop.py) |
| Audio handling | ~200 lines | ~300 lines (audio.py) |
| Event definitions | ~100 lines (JSON strings) | ~600 lines (typed classes) |
| Tool system | ~300 lines | Shared with main SDK |
| Model communication | ~300 lines | ~750 lines (nova_sonic.py) |
| **Total** | **~1,500 lines** | **~2,000+ lines** |

**Why is Strands SDK larger?**
- Typed event classes instead of raw JSON
- Multi-model abstraction layer
- Hook system for lifecycle events
- Session management
- Error handling and connection restart

---

## How Strands SDK Makes Things Easier

### 1. Tool Definition

**The Problem (Raw Implementation):**
You must manually write JSON schemas and wire up tool execution:

```python
# voice-agents: ~50 lines per tool
guest_tool_schema = json.dumps({
    "type": "object",
    "properties": {
        "guestName": {
            "type": "string",
            "description": "The full name of the hotel guest.",
        }
    },
    "required": ["guestName"],
})

prompt_start_event = {
    "event": {
        "promptStart": {
            # ... lots of config ...
            "toolConfiguration": {
                "tools": [{
                    "toolSpec": {
                        "name": "checkGuestProfileTool",
                        "description": "Use this tool to look up a hotel guest...",
                        "inputSchema": {"json": guest_tool_schema},
                    }
                }]
            }
        }
    }
}

# Then manually handle tool calls in _process_responses()
# Then manually route to ToolProcessor
# Then manually send results back
```

**The Solution (Strands SDK):**
Just use the `@tool` decorator:

```python
# Strands SDK: ~10 lines per tool
from strands.tools import tool

@tool
def check_guest_profile(guest_name: str) -> dict:
    """Use this tool to look up a hotel guest's profile.

    Args:
        guest_name: The full name of the hotel guest.

    Returns:
        Guest profile with DOB, loyalty tier, and preferences.
    """
    # Your implementation here
    return {"found": True, "guestName": guest_name, ...}

# That's it! Schema is auto-generated from type hints and docstring
agent = BidiAgent(model=model, tools=[check_guest_profile])
```

**What Strands SDK handles automatically:**
- JSON schema generation from type hints
- Description extraction from docstrings
- Parameter validation
- Tool result formatting
- Error handling

---

### 2. Audio I/O Setup

**The Problem (Raw Implementation):**
Manual PyAudio setup with callbacks and queues:

```python
# voice-agents: ~150 lines
class AudioStreamer:
    def __init__(self, stream_manager):
        self.stream_manager = stream_manager
        self.is_streaming = False
        self.loop = asyncio.get_event_loop()

        # Initialize PyAudio
        self.p = pyaudio.PyAudio()

        # Input stream with callback
        self.input_stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=INPUT_SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self.input_callback,
        )

        # Output stream
        self.output_stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=OUTPUT_SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE,
        )

    def input_callback(self, in_data, frame_count, time_info, status):
        if self.is_streaming and in_data:
            asyncio.run_coroutine_threadsafe(
                self.process_input_audio(in_data), self.loop
            )
        return (None, pyaudio.paContinue)

    async def play_output_audio(self):
        while self.is_streaming:
            # Check for barge-in
            if self.stream_manager.barge_in:
                # Clear the queue manually...
                pass
            # Get audio, write in chunks...
            pass
```

**The Solution (Strands SDK):**
Pre-built audio I/O abstraction:

```python
# Strands SDK: ~5 lines
from strands.experimental.bidi import BidiAgent, BidiAudioIO

audio_io = BidiAudioIO()  # That's it!

agent = BidiAgent(model=model, tools=[...])
await agent.run(
    inputs=[audio_io.input()],
    outputs=[audio_io.output()],
)
```

**What Strands SDK handles automatically:**
- PyAudio initialization and cleanup
- Sample rate configuration from model
- Callback threading
- Buffer management
- Interruption/barge-in handling

---

### 3. Event Handling

**The Problem (Raw Implementation):**
String templates and manual JSON parsing:

```python
# voice-agents: JSON string templates
AUDIO_EVENT_TEMPLATE = """{
    "event": {
        "audioInput": {
            "promptName": "%s",
            "contentName": "%s",
            "content": "%s"
        }
    }
}"""

# Sending events
audio_event = self.AUDIO_EVENT_TEMPLATE % (
    self.prompt_name,
    self.audio_content_name,
    blob.decode("utf-8"),
)
await self.send_raw_event(audio_event)

# Receiving events - manual JSON parsing
response_data = result.value.bytes_.decode("utf-8")
json_data = json.loads(response_data)
if "event" in json_data:
    if "audioOutput" in json_data["event"]:
        audio_content = json_data["event"]["audioOutput"]["content"]
        # handle audio...
    elif "textOutput" in json_data["event"]:
        # handle text...
    elif "toolUse" in json_data["event"]:
        # handle tool...
```

**The Solution (Strands SDK):**
Typed event classes with properties:

```python
# Strands SDK: Typed events
from strands.experimental.bidi import (
    BidiAudioStreamEvent,
    BidiTranscriptStreamEvent,
    ToolUseStreamEvent,
)

async for event in agent.receive():
    if isinstance(event, BidiAudioStreamEvent):
        # Typed properties with IDE autocomplete
        audio_bytes = base64.b64decode(event.audio)
        sample_rate = event.sample_rate  # Type: AudioSampleRate

    elif isinstance(event, BidiTranscriptStreamEvent):
        print(f"[{event.role}]: {event.text}")
        if event.is_final:
            # Handle final transcript
            pass

    elif isinstance(event, ToolUseStreamEvent):
        tool_name = event.current_tool_use["name"]
        # Tool execution handled automatically
```

**What Strands SDK handles automatically:**
- Type safety with IDE support
- Property access instead of dict keys
- Event type discrimination
- JSON serialization/deserialization

---

### 4. Connection Management

**The Problem (Raw Implementation):**
No automatic reconnection on timeout:

```python
# voice-agents: Connection just dies after 8 minutes
# No timeout handling shown in the code
# User must manually restart the application
```

**The Solution (Strands SDK):**
Automatic connection restart:

```python
# Strands SDK: Automatic handling in _BidiAgentLoop
async def _restart_connection(self, timeout_error: BidiModelTimeoutError) -> None:
    """Restart the model connection after timeout."""
    self._send_gate.clear()  # Block new sends

    await self._agent.hooks.invoke_callbacks_async(
        BidiBeforeConnectionRestartEvent(self._agent, timeout_error)
    )

    # Stop and restart with full message history
    await self._agent.model.stop()
    await self._agent.model.start(
        self._agent.system_prompt,
        self._agent.tool_registry.get_all_tool_specs(),
        self._agent.messages,  # Preserves conversation!
        **timeout_error.restart_config,
    )

    self._task_pool.create(self._run_model())
    self._send_gate.set()  # Allow sends again
```

**What Strands SDK handles automatically:**
- 8-minute timeout detection
- Graceful connection restart
- Message history preservation
- Hook notifications for custom handling

---

### 5. System Prompt Setup

**The Problem (Raw Implementation):**
Manual event sequencing:

```python
# voice-agents: ~30 lines for initialization
default_system_prompt = "You are the virtual front desk assistant..."

# Must send events in exact order
init_events = [
    self.START_SESSION_EVENT,
    prompt_event,  # promptStart with tool config
    text_content_start,  # contentStart for system
    text_content,  # textInput with prompt
    text_content_end,  # contentEnd
]

for event in init_events:
    await self.send_raw_event(event)
    await asyncio.sleep(0.1)  # Manual delays!
```

**The Solution (Strands SDK):**
Just pass the prompt:

```python
# Strands SDK: 1 line
agent = BidiAgent(
    model=model,
    system_prompt="You are the virtual front desk assistant...",
    tools=[check_guest, check_reservation, update_reservation],
)
```

**What Strands SDK handles automatically:**
- Event sequencing (sessionStart → promptStart → contentStart → etc.)
- Tool configuration injection
- Proper delays between events
- Content container management

---

### 6. Message History

**The Problem (Raw Implementation):**
No message history tracking:

```python
# voice-agents: No history!
# Each conversation turn is independent
# Cannot reference previous exchanges
# Cannot resume after connection restart
```

**The Solution (Strands SDK):**
Automatic message tracking:

```python
# Strands SDK: Built-in history
agent = BidiAgent(model=model, system_prompt="...")

# Messages automatically tracked
await agent.start()
await agent.send("Hello!")
# ... conversation happens ...

# Access history anytime
print(agent.messages)
# [
#   {"role": "user", "content": [{"text": "Hello!"}]},
#   {"role": "assistant", "content": [{"text": "Hi there!"}]},
#   ...
# ]

# History preserved across connection restarts
# History can be persisted with SessionManager
```

---

### 7. Lifecycle Hooks

**The Problem (Raw Implementation):**
No hook system - must modify core code:

```python
# voice-agents: Want to log events? Modify the code directly.
# Want to add metrics? Modify the code.
# Want custom error handling? Modify the code.
```

**The Solution (Strands SDK):**
Extensible hook system:

```python
# Strands SDK: Add behavior without modifying SDK
from strands.experimental.hooks.events import (
    BidiAgentInitializedEvent,
    BidiMessageAddedEvent,
    BidiInterruptionEvent,
)

class MyMetricsHook:
    def on_bidi_agent_initialized(self, event: BidiAgentInitializedEvent):
        metrics.increment("agent.initialized")

    def on_bidi_message_added(self, event: BidiMessageAddedEvent):
        metrics.increment("messages.count")
        metrics.record("message.length", len(str(event.message)))

    def on_bidi_interruption(self, event: BidiInterruptionEvent):
        metrics.increment("interruptions", tags={"reason": event.reason})

agent = BidiAgent(
    model=model,
    hooks=[MyMetricsHook()],  # Just add your hook
)
```

---

## Side-by-Side Code Examples

### Complete Voice Agent Setup

**Raw Implementation (~100 lines):**
```python
# voice-agents style
import asyncio
import pyaudio
from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient
# ... many more imports ...

class BedrockStreamManager:
    # 600+ lines of event templates, state management, etc.
    pass

class AudioStreamer:
    # 200+ lines of PyAudio handling
    pass

class ToolProcessor:
    # 300+ lines of tool implementations
    pass

async def main():
    stream_manager = BedrockStreamManager(
        model_id="amazon.nova-sonic-v1:0",
        region="us-east-1"
    )
    audio_streamer = AudioStreamer(stream_manager)
    await stream_manager.initialize_stream()

    try:
        await audio_streamer.start_streaming()
    finally:
        await audio_streamer.stop_streaming()

asyncio.run(main())
```

**Strands SDK (~20 lines):**
```python
# Strands SDK style
import asyncio
from strands.experimental.bidi import BidiAgent, BidiNovaSonicModel, BidiAudioIO
from strands.tools import tool

@tool
def check_guest(guest_name: str) -> dict:
    """Look up a hotel guest's profile."""
    # Implementation
    return {"found": True, ...}

@tool
def check_reservation(guest_name: str) -> dict:
    """Check guest's reservation status."""
    # Implementation
    return {"found": True, ...}

async def main():
    audio_io = BidiAudioIO()
    agent = BidiAgent(
        model=BidiNovaSonicModel(),
        system_prompt="You are the virtual front desk assistant...",
        tools=[check_guest, check_reservation],
    )

    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output()],
    )

asyncio.run(main())
```

---

## Feature Comparison Matrix

| Feature | voice-agents | Strands SDK | Benefit |
|---------|-------------|-------------|---------|
| **Setup Complexity** | ~100 lines | ~20 lines | 80% less code |
| **Tool Definition** | Manual JSON schema | `@tool` decorator | Auto-schema generation |
| **Audio I/O** | Manual PyAudio | `BidiAudioIO()` | Zero config |
| **Event Types** | Raw JSON strings | Typed classes | IDE support, type safety |
| **Message History** | None | Automatic | Conversation context |
| **Connection Restart** | None | Automatic | 8-min timeout handled |
| **Multi-Model** | Nova Sonic only | Nova + OpenAI + Gemini | Provider flexibility |
| **Hooks/Lifecycle** | None | Full system | Extensibility |
| **Session Persistence** | None | SessionManager | State management |
| **Error Handling** | Basic try/catch | Typed error events | Better debugging |
| **Interruption** | Manual flag | Automatic events | Cleaner handling |

---

## When to Use Which

### Use Raw Implementation When:
- Learning how Nova Sonic API works
- Building a quick demo/POC
- Need full control over every detail
- Single-use, throwaway code
- Teaching/educational purposes

### Use Strands SDK When:
- Building production applications
- Need multi-model support
- Want reusable components
- Need session persistence
- Want extensibility via hooks
- Team collaboration (cleaner abstractions)
- Long-running voice applications (timeout handling)

---

## Migration Path

If you have an existing raw implementation and want to migrate to Strands SDK:

### Step 1: Convert Tools
```python
# Before (voice-agents)
class ToolProcessor:
    async def _run_tool(self, tool_name, tool_content):
        if tool == "checkguestprofiletool":
            return self._execute_check_guest(content_data)

# After (Strands SDK)
@tool
def check_guest_profile(guest_name: str) -> dict:
    """Look up a hotel guest's profile."""
    return execute_check_guest({"guestName": guest_name})
```

### Step 2: Replace Audio Handling
```python
# Before: 200+ lines of AudioStreamer class
# After:
audio_io = BidiAudioIO()
```

### Step 3: Replace Stream Manager
```python
# Before: 600+ lines of BedrockStreamManager
# After:
agent = BidiAgent(
    model=BidiNovaSonicModel(),
    system_prompt="...",
    tools=[...],
)
```

### Step 4: Run
```python
# Before: Complex async coordination
# After:
await agent.run(
    inputs=[audio_io.input()],
    outputs=[audio_io.output()],
)
```

---

## Summary

The Strands SDK transforms ~1,500 lines of boilerplate into ~20 lines of application code by providing:

1. **Declarative tool definition** - `@tool` decorator vs manual JSON schemas
2. **Pre-built I/O handlers** - `BidiAudioIO()` vs manual PyAudio
3. **Typed event system** - Classes with properties vs raw JSON
4. **Automatic lifecycle** - Connection restart, message history
5. **Extensibility** - Hooks, sessions, multi-model support

The raw implementation is valuable for **understanding** how Nova Sonic works. The Strands SDK is valuable for **building applications** with Nova Sonic.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Raw Implementation     ──────────────>     Strands SDK        │
│                                                                 │
│   "I want to learn"                      "I want to build"      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
