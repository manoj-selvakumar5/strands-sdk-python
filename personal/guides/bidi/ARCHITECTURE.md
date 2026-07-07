# Bidirectional (Bidi) Agent Architecture

## Table of Contents
1. [Overview](#overview)
2. [What is a Bidi Agent?](#what-is-a-bidi-agent)
3. [Regular Agent vs Bidi Agent](#regular-agent-vs-bidi-agent)
4. [Architecture Overview](#architecture-overview)
5. [Component Deep Dive](#component-deep-dive)
6. [Event System](#event-system)
7. [Data Flow](#data-flow)
8. [Model Implementations](#model-implementations)
9. [Tool Execution](#tool-execution)
10. [Connection Lifecycle](#connection-lifecycle)
11. [Usage Examples](#usage-examples)

---

## Overview

The Bidirectional (Bidi) Agent is an **experimental** feature in the Strands SDK that enables real-time, streaming conversations with AI models. Unlike traditional request-response patterns, bidi agents maintain persistent streaming connections (HTTP/2 or WebSocket depending on the provider) for simultaneous input/output streams.

**Key Use Cases:**
- Voice assistants with real-time audio I/O
- Interactive conversations with interruption support
- Multi-modal (text + audio + image) streaming applications

**Requirements:** Python 3.12+

---

## What is a Bidi Agent?

A Bidi Agent enables **bidirectional streaming** - the ability to send and receive data simultaneously over a persistent connection:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BIDIRECTIONAL STREAMING                          │
│                                                                     │
│    ┌──────────┐          Persistent Connection          ┌────────┐ │
│    │          │  ════════════════════════════════════>  │        │ │
│    │   User   │          (Audio/Text Input)             │  Model │ │
│    │          │  <════════════════════════════════════  │        │ │
│    └──────────┘          (Audio/Text Output)            └────────┘ │
│                                                                     │
│    Both streams are active simultaneously                           │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Properties:**
- **Persistent Connection**: Stream stays open for the conversation duration
- **Full Duplex**: Send and receive happen concurrently
- **Real-time**: Sub-second latency for audio streaming
- **Interruptible**: User can interrupt the model mid-response

> **Note on Protocols:** Different providers use different streaming protocols:
> - **Nova Sonic (Bedrock)**: HTTP/2 Event Streams via AWS SDK
> - **OpenAI Realtime**: WebSocket
> - **Gemini Live**: WebSocket

---

## Regular Agent vs Bidi Agent

```
┌─────────────────────────────────────────────────────────────────────┐
│                      REGULAR AGENT (Request-Response)               │
│                                                                     │
│    ┌──────────┐    Request     ┌────────┐    Request    ┌────────┐ │
│    │   User   │ ─────────────> │ Agent  │ ────────────> │  API   │ │
│    └──────────┘                └────────┘               └────────┘ │
│         │                           │                        │      │
│         │                           │                        │      │
│         │        Response           │       Response         │      │
│         │ <─────────────────────────│ <──────────────────────│      │
│                                                                     │
│    Connection closes after each exchange                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      BIDI AGENT (Streaming)                         │
│                                                                     │
│    ┌──────────┐                 ┌────────┐               ┌────────┐ │
│    │   User   │ ═══════════════ │ Agent  │ ═════════════ │  API   │ │
│    │          │ ═══════════════ │  Loop  │ ═════════════ │        │ │
│    └──────────┘  Audio/Text     └────────┘   HTTP/2 or   └────────┘ │
│                   Streams                    WebSocket              │
│                                                                     │
│    Connection remains open throughout conversation                  │
└─────────────────────────────────────────────────────────────────────┘
```

| Aspect | Regular Agent | Bidi Agent |
|--------|---------------|------------|
| **Connection** | Per-request HTTP | Persistent (HTTP/2 or WebSocket) |
| **Input** | Text only | Audio + Text + Images |
| **Output** | Text (streamed) | Audio + Text (real-time) |
| **Latency** | Higher (connection overhead) | Lower (persistent) |
| **Interruption** | Not supported | Supported |
| **Use Case** | Chat, coding assistants | Voice assistants, real-time apps |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BIDI AGENT ARCHITECTURE                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           USER SPACE                                 │   │
│  │                                                                      │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │   │
│  │   │  Microphone  │    │   Keyboard   │    │    Camera    │         │   │
│  │   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘         │   │
│  │          │                   │                   │                  │   │
│  │          v                   v                   v                  │   │
│  │   ┌──────────────────────────────────────────────────────┐         │   │
│  │   │                    BidiAudioIO / BidiTextIO          │         │   │
│  │   │              (Input/Output Abstraction)              │         │   │
│  │   └──────────────────────────┬───────────────────────────┘         │   │
│  └──────────────────────────────┼───────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────┼───────────────────────────────────────┐   │
│  │                              v          SDK LAYER                     │   │
│  │   ┌──────────────────────────────────────────────────────────────┐  │   │
│  │   │                        BidiAgent                              │  │   │
│  │   │  ┌─────────────────────────────────────────────────────────┐ │  │   │
│  │   │  │                    _BidiAgentLoop                        │ │  │   │
│  │   │  │                                                          │ │  │   │
│  │   │  │   ┌──────────────┐      ┌──────────────┐                │ │  │   │
│  │   │  │   │  Input Queue │      │ Output Queue │                │ │  │   │
│  │   │  │   └──────┬───────┘      └──────┬───────┘                │ │  │   │
│  │   │  │          │                     │                         │ │  │   │
│  │   │  │          v                     ^                         │ │  │   │
│  │   │  │   ┌──────────────────────────────────────┐              │ │  │   │
│  │   │  │   │          _run_model() Task           │              │ │  │   │
│  │   │  │   │    (Event Processing & Dispatch)     │              │ │  │   │
│  │   │  │   └──────────────────────────────────────┘              │ │  │   │
│  │   │  │          │                     ^                         │ │  │   │
│  │   │  │          v                     │                         │ │  │   │
│  │   │  │   ┌──────────────────────────────────────┐              │ │  │   │
│  │   │  │   │         _TaskPool (Tool Exec)        │              │ │  │   │
│  │   │  │   │    Concurrent tool execution tasks   │              │ │  │   │
│  │   │  │   └──────────────────────────────────────┘              │ │  │   │
│  │   │  └─────────────────────────────────────────────────────────┘ │  │   │
│  │   └──────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                       │   │
│  │                              v                                       │   │
│  │   ┌──────────────────────────────────────────────────────────────┐  │   │
│  │   │                      BidiModel (Protocol)                     │  │   │
│  │   │                                                               │  │   │
│  │   │   ┌────────────────┐  ┌────────────────┐  ┌───────────────┐  │  │   │
│  │   │   │ BidiNovaSonic  │  │ OpenAIRealtime │  │  GeminiLive   │  │  │   │
│  │   │   │    Model       │  │     Model      │  │    Model      │  │  │   │
│  │   │   └────────┬───────┘  └────────────────┘  └───────────────┘  │  │   │
│  │   │            │                                                  │  │   │
│  │   └────────────┼──────────────────────────────────────────────────┘  │   │
│  └────────────────┼─────────────────────────────────────────────────────┘   │
│                   │                                                         │
│  ┌────────────────┼─────────────────────────────────────────────────────┐   │
│  │                v                   CLOUD LAYER                        │   │
│  │   ┌──────────────────────────────────────────────────────────────┐   │   │
│  │   │              Amazon Bedrock Runtime                           │   │   │
│  │   │         InvokeModelWithBidirectionalStream                    │   │   │
│  │   │                                                               │   │   │
│  │   │   ┌─────────────────────────────────────────────────────────┐│   │   │
│  │   │   │                 Nova Sonic Model                         ││   │   │
│  │   │   │           (amazon.nova-sonic-v1:0)                       ││   │   │
│  │   │   └─────────────────────────────────────────────────────────┘│   │   │
│  │   └──────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Deep Dive

### File Structure

```
src/strands/experimental/bidi/
├── __init__.py                 # Public exports
├── _async/                     # Async utilities
│   ├── __init__.py
│   ├── _task_group.py          # TaskGroup shim (like asyncio.TaskGroup)
│   └── _task_pool.py           # Pool for managing concurrent tasks
├── agent/
│   ├── __init__.py
│   ├── agent.py                # BidiAgent main class
│   └── loop.py                 # _BidiAgentLoop - event processing
├── io/
│   ├── __init__.py
│   ├── audio.py                # BidiAudioIO - microphone/speaker
│   └── text.py                 # BidiTextIO - stdin/stdout
├── models/
│   ├── __init__.py
│   ├── model.py                # BidiModel Protocol
│   ├── nova_sonic.py           # Amazon Nova Sonic implementation
│   ├── openai_realtime.py      # OpenAI Realtime (planned)
│   └── gemini_live.py          # Gemini Live (planned)
├── tools/
│   ├── __init__.py
│   └── stop_conversation.py    # Built-in tool to end conversation
└── types/
    ├── __init__.py
    ├── agent.py                # Agent type definitions
    ├── events.py               # All event types
    ├── io.py                   # I/O type definitions
    └── model.py                # Model type definitions
```

### BidiAgent (`agent/agent.py`)

The main entry point for users. Manages:
- Model initialization
- Tool registration
- Message history
- Hook system
- Session management

```python
class BidiAgent:
    """Core attributes and responsibilities"""

    # Model connection
    model: BidiModel              # The streaming model (Nova Sonic, etc.)

    # Conversation state
    messages: Messages            # Conversation history
    system_prompt: str | None     # System instructions

    # Tool management
    tool_registry: ToolRegistry   # Registered tools
    tool_executor: ToolExecutor   # How tools are executed

    # Event loop
    _loop: _BidiAgentLoop         # Handles event processing

    # Key methods
    async def start()             # Open connection
    async def send(input)         # Send text/audio/image
    async def receive()           # Yield output events
    async def stop()              # Close connection
    async def run(inputs, outputs)  # Run with I/O channels
```

### _BidiAgentLoop (`agent/loop.py`)

The heart of event processing:

```
┌────────────────────────────────────────────────────────────────────┐
│                      _BidiAgentLoop                                │
│                                                                    │
│   ┌────────────────────────────────────────────────────────────┐  │
│   │                    _run_model() Task                        │  │
│   │                                                             │  │
│   │   async for event in model.receive():                       │  │
│   │       ├─> BidiTranscriptStreamEvent -> append to messages   │  │
│   │       ├─> ToolUseStreamEvent -> spawn _run_tool() task      │  │
│   │       ├─> BidiInterruptionEvent -> invoke hooks             │  │
│   │       └─> * -> put in event_queue for user                  │  │
│   │                                                             │  │
│   └────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              v                                     │
│   ┌────────────────────────────────────────────────────────────┐  │
│   │                     event_queue                             │  │
│   │         (asyncio.Queue - bridges model and user)            │  │
│   └────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              v                                     │
│   ┌────────────────────────────────────────────────────────────┐  │
│   │                    receive() generator                      │  │
│   │                                                             │  │
│   │   while True:                                               │  │
│   │       event = await event_queue.get()                       │  │
│   │       if BidiModelTimeoutError -> restart connection        │  │
│   │       if Exception -> raise to user                         │  │
│   │       if BidiConnectionCloseEvent -> break                  │  │
│   │       yield event                                           │  │
│   │                                                             │  │
│   └────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### BidiModel Protocol (`models/model.py`)

Abstract interface that all model implementations must follow:

```python
class BidiModel(Protocol):
    """Protocol for bidirectional streaming models"""

    config: dict[str, Any]

    async def start(
        system_prompt: str | None,
        tools: list[ToolSpec] | None,
        messages: Messages | None,
    ) -> None

    async def stop() -> None

    def receive() -> AsyncIterable[BidiOutputEvent]

    async def send(content: BidiInputEvent | ToolResultEvent) -> None
```

---

## Event System

The bidi system uses a typed event architecture for all communication:

### Input Events (User -> Model)

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT EVENTS                             │
│                                                                 │
│   ┌─────────────────────┐                                       │
│   │ BidiTextInputEvent  │  User text message                    │
│   │   - text: str       │  "Hello, how are you?"                │
│   │   - role: "user"    │                                       │
│   └─────────────────────┘                                       │
│                                                                 │
│   ┌─────────────────────┐                                       │
│   │ BidiAudioInputEvent │  Audio chunk from microphone          │
│   │   - audio: base64   │  PCM audio data                       │
│   │   - format: "pcm"   │                                       │
│   │   - sample_rate     │  16000, 24000, or 48000 Hz            │
│   │   - channels        │  1 (mono) or 2 (stereo)               │
│   └─────────────────────┘                                       │
│                                                                 │
│   ┌─────────────────────┐                                       │
│   │ BidiImageInputEvent │  Image/video frame                    │
│   │   - image: base64   │                                       │
│   │   - mime_type       │  "image/jpeg", "image/png"            │
│   └─────────────────────┘                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Output Events (Model -> User)

```
┌─────────────────────────────────────────────────────────────────┐
│                       OUTPUT EVENTS                             │
│                                                                 │
│   CONNECTION LIFECYCLE                                          │
│   ┌───────────────────────────┐                                 │
│   │ BidiConnectionStartEvent  │  Connection established         │
│   │ BidiConnectionRestartEvent│  Reconnecting after timeout     │
│   │ BidiConnectionCloseEvent  │  Connection ended               │
│   └───────────────────────────┘                                 │
│                                                                 │
│   RESPONSE LIFECYCLE                                            │
│   ┌───────────────────────────┐                                 │
│   │ BidiResponseStartEvent    │  Model starts responding        │
│   │ BidiResponseCompleteEvent │  Model finished responding      │
│   └───────────────────────────┘                                 │
│                                                                 │
│   CONTENT STREAMING                                             │
│   ┌───────────────────────────┐                                 │
│   │ BidiAudioStreamEvent      │  Audio chunk from model         │
│   │ BidiTranscriptStreamEvent │  Text transcript (partial/final)│
│   └───────────────────────────┘                                 │
│                                                                 │
│   TOOL EXECUTION                                                │
│   ┌───────────────────────────┐                                 │
│   │ ToolUseStreamEvent        │  Model wants to call a tool     │
│   │ ToolResultEvent           │  Tool execution result          │
│   └───────────────────────────┘                                 │
│                                                                 │
│   CONTROL                                                       │
│   ┌───────────────────────────┐                                 │
│   │ BidiInterruptionEvent     │  User interrupted model         │
│   │ BidiUsageEvent            │  Token usage metrics            │
│   │ BidiErrorEvent            │  Error occurred                 │
│   └───────────────────────────┘                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Complete Request-Response Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BIDI DATA FLOW (Voice Conversation)                  │
│                                                                         │
│  1. USER SPEAKS                                                         │
│  ┌──────────┐                                                           │
│  │   User   │ ──> [Microphone] ──> [PyAudio Callback]                   │
│  └──────────┘                              │                            │
│                                            v                            │
│  2. AUDIO CAPTURED                  ┌──────────────┐                    │
│                                     │ _BidiAudio   │                    │
│                                     │   Buffer     │                    │
│                                     └──────┬───────┘                    │
│                                            │                            │
│  3. AUDIO SENT TO AGENT                    v                            │
│                            ┌───────────────────────────────┐            │
│                            │    BidiAudioInputEvent        │            │
│                            │    {audio: base64, rate: 16k} │            │
│                            └───────────────┬───────────────┘            │
│                                            │                            │
│  4. AGENT SENDS TO MODEL                   v                            │
│                            ┌───────────────────────────────┐            │
│                            │        agent.send()           │            │
│                            │            │                  │            │
│                            │            v                  │            │
│                            │       model.send()            │            │
│                            └───────────────┬───────────────┘            │
│                                            │                            │
│  5. MODEL PROCESSES                        v                            │
│                            ┌───────────────────────────────┐            │
│                            │      Nova Sonic (Bedrock)     │            │
│                            │                               │            │
│                            │  - Speech-to-Text (STT)       │            │
│                            │  - LLM Processing             │            │
│                            │  - Text-to-Speech (TTS)       │            │
│                            └───────────────┬───────────────┘            │
│                                            │                            │
│  6. MODEL STREAMS RESPONSE                 v                            │
│                            ┌───────────────────────────────┐            │
│                            │   Multiple events streamed:   │            │
│                            │                               │            │
│                            │   - BidiResponseStartEvent    │            │
│                            │   - BidiTranscriptStreamEvent │ (text)     │
│                            │   - BidiAudioStreamEvent      │ (audio)    │
│                            │   - BidiResponseCompleteEvent │            │
│                            └───────────────┬───────────────┘            │
│                                            │                            │
│  7. AGENT LOOP PROCESSES                   v                            │
│                            ┌───────────────────────────────┐            │
│                            │      _BidiAgentLoop           │            │
│                            │                               │            │
│                            │  - Updates message history    │            │
│                            │  - Queues events for user     │            │
│                            │  - Spawns tool tasks if needed│            │
│                            └───────────────┬───────────────┘            │
│                                            │                            │
│  8. USER RECEIVES EVENTS                   v                            │
│                            ┌───────────────────────────────┐            │
│                            │     agent.receive()           │            │
│                            │            │                  │            │
│                            │            v                  │            │
│                            │    BidiAudioStreamEvent       │            │
│                            └───────────────┬───────────────┘            │
│                                            │                            │
│  9. AUDIO PLAYED                           v                            │
│                            ┌───────────────────────────────┐            │
│                            │   _BidiAudioOutput Buffer     │            │
│                            │            │                  │            │
│                            │            v                  │            │
│                            │   [PyAudio Callback] ──> [Speaker]         │
│                            └───────────────────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TOOL EXECUTION FLOW                                │
│                                                                         │
│   ┌─────────────────┐         ┌─────────────────┐                      │
│   │   Nova Sonic    │ ──────> │ ToolUseStream   │                      │
│   │   "Call weather │         │ Event           │                      │
│   │    tool"        │         │ {name: "weather"│                      │
│   └─────────────────┘         │  input: {...}}  │                      │
│                               └────────┬────────┘                      │
│                                        │                               │
│                                        v                               │
│   ┌───────────────────────────────────────────────────────────────┐   │
│   │                     _BidiAgentLoop._run_tool()                 │   │
│   │                                                                │   │
│   │   1. Spawn task in _TaskPool                                   │   │
│   │   2. Build invocation_state with agent context                 │   │
│   │   3. Execute via tool_executor._stream()                       │   │
│   │   4. Collect tool events (progress, result)                    │   │
│   │   5. Append tool_use + tool_result to messages                 │   │
│   │   6. Send ToolResultEvent back to model                        │   │
│   │                                                                │   │
│   └───────────────────────────────────────────────────────────────┘   │
│                                        │                               │
│                                        v                               │
│   ┌─────────────────┐         ┌─────────────────┐                      │
│   │   Nova Sonic    │ <────── │ ToolResultEvent │                      │
│   │   "Weather is   │         │ {content: "72F"}│                      │
│   │    72F sunny"   │         └─────────────────┘                      │
│   └─────────────────┘                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Interruption Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      INTERRUPTION HANDLING                              │
│                                                                         │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │ Timeline:                                                      │    │
│   │                                                                │    │
│   │ t=0s    Model speaking: "The weather today is going to be..." │    │
│   │         ════════════════════════════════════════════>          │    │
│   │                                                                │    │
│   │ t=2s    User interrupts: "Wait, what about tomorrow?"          │    │
│   │         <═══════════════════                                   │    │
│   │                                                                │    │
│   │ t=2.1s  Model detects interruption via VAD                     │    │
│   │         ┌─────────────────────────────────────┐                │    │
│   │         │ BidiInterruptionEvent               │                │    │
│   │         │ {reason: "user_speech"}             │                │    │
│   │         └─────────────────────────────────────┘                │    │
│   │                                                                │    │
│   │ t=2.2s  Audio buffer cleared (stops playback)                  │    │
│   │         ┌─────────────────────────────────────┐                │    │
│   │         │ _BidiAudioOutput._buffer.clear()    │                │    │
│   │         └─────────────────────────────────────┘                │    │
│   │                                                                │    │
│   │ t=2.3s  Model processes new input and responds                 │    │
│   │         "Tomorrow will be partly cloudy with..."               │    │
│   │         ════════════════════════════════════════════>          │    │
│   │                                                                │    │
│   └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Model Implementations

### HTTP/2 Event Streams vs WebSocket

Different model providers use different underlying protocols for bidirectional streaming:

```
┌─────────────────────────────────────────────────────────────────────────┐
│              STREAMING PROTOCOL COMPARISON                              │
│                                                                         │
│   HTTP/2 EVENT STREAMS (Amazon Bedrock)                                 │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                  │  │
│   │   Client                              Server                     │  │
│   │     │                                   │                        │  │
│   │     │ ══ HTTP/2 Stream (HEADERS) ═════> │                        │  │
│   │     │ ══ DATA frame (event 1) ════════> │                        │  │
│   │     │ ══ DATA frame (event 2) ════════> │                        │  │
│   │     │ <════════════ DATA frame (event) ═│                        │  │
│   │     │ <════════════ DATA frame (event) ═│                        │  │
│   │     │                                   │                        │  │
│   │   Uses AWS SDK's DuplexEventStream                               │  │
│   │   SigV4 authentication built-in                                  │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   WEBSOCKET (OpenAI, Google)                                            │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                  │  │
│   │   Client                              Server                     │  │
│   │     │                                   │                        │  │
│   │     │ ── HTTP Upgrade Request ────────> │                        │  │
│   │     │ <─ 101 Switching Protocols ────── │                        │  │
│   │     │ ══ WS Frame (message) ══════════> │                        │  │
│   │     │ <══════════════ WS Frame (message)│                        │  │
│   │     │ ══ WS Frame (message) ══════════> │                        │  │
│   │     │                                   │                        │  │
│   │   Uses websockets library                                        │  │
│   │   Token-based auth in headers                                    │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

| Aspect | HTTP/2 Event Streams | WebSocket |
|--------|---------------------|-----------|
| **Used By** | Amazon Bedrock (Nova Sonic) | OpenAI Realtime, Gemini Live |
| **Protocol** | HTTP/2 multiplexed streams | ws:// or wss:// |
| **Authentication** | AWS SigV4 signing | Bearer token in headers |
| **SDK** | AWS Smithy SDK (`DuplexEventStream`) | `websockets` library |
| **Message Format** | AWS Event Stream encoding | JSON or binary frames |
| **Connection** | Single HTTP/2 connection, multiplexed | Dedicated TCP connection |
| **Firewall Friendly** | Yes (standard HTTPS port 443) | Usually (port 443) |

**Why the difference?**
- **Bedrock** uses HTTP/2 because it integrates with AWS's existing infrastructure, authentication (IAM/SigV4), and SDK ecosystem
- **OpenAI/Google** use WebSocket because it's simpler to implement and widely supported

### Nova Sonic (`models/nova_sonic.py`)

The primary implementation for Amazon Bedrock's Nova Sonic model, using **HTTP/2 Event Streams**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     NOVA SONIC EVENT PROTOCOL                           │
│                                                                         │
│   INITIALIZATION SEQUENCE (sent on start())                             │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                  │  │
│   │   1. sessionStart        ──> Inference config (temp, max_tokens) │  │
│   │   2. promptStart         ──> Audio/text/tool output configs      │  │
│   │   3. contentStart(SYSTEM)──> System prompt container             │  │
│   │   4. textInput           ──> Actual system prompt text           │  │
│   │   5. contentEnd          ──> Close system container              │  │
│   │   6. [message history]   ──> Prior conversation if any           │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   AUDIO INPUT SEQUENCE (for each audio chunk)                           │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                  │  │
│   │   1. contentStart(AUDIO) ──> Opens audio container (once)        │  │
│   │   2. audioInput          ──> Base64 PCM audio chunk              │  │
│   │   3. audioInput          ──> More chunks...                      │  │
│   │   4. contentEnd          ──> Closes audio container              │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   MODEL RESPONSE EVENTS (received via receive())                        │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                  │  │
│   │   completionStart   ──> Response starting (completionId)         │  │
│   │   contentStart      ──> Content block starting                   │  │
│   │   textOutput        ──> Transcript text (partial/final)          │  │
│   │   audioOutput       ──> Base64 PCM audio chunk                   │  │
│   │   toolUse           ──> Tool call request                        │  │
│   │   contentEnd        ──> Content block finished                   │  │
│   │   completionEnd     ──> Response finished (stopReason)           │  │
│   │   usageEvent        ──> Token usage metrics                      │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   CLEANUP SEQUENCE (sent on stop())                                     │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                  │  │
│   │   1. contentEnd (audio)  ──> Close any open audio container      │  │
│   │   2. promptEnd           ──> End the prompt                      │  │
│   │   3. connectionEnd       ──> Close the connection                │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Configuration Options:**

```python
BidiNovaSonicModel(
    model_id="amazon.nova-sonic-v1:0",
    provider_config={
        "audio": {
            "input_rate": 16000,    # Sample rate for input
            "output_rate": 16000,   # Sample rate for output
            "channels": 1,          # Mono audio
            "format": "pcm",        # Audio format
            "voice": "matthew",     # TTS voice
        },
        "inference": {
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    },
    client_config={
        "region": "us-east-1",      # AWS region
        # OR
        "boto_session": session,    # Custom boto3 session
    }
)
```

### Connection Timeout Handling

Nova Sonic has an 8-minute connection limit. The SDK handles this transparently:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION TIMEOUT HANDLING                          │
│                                                                         │
│   t=0min   Connection established                                       │
│            │                                                            │
│            │  Normal conversation...                                    │
│            │                                                            │
│   t=8min   ModelTimeoutException received                               │
│            │                                                            │
│            v                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │ _BidiAgentLoop._restart_connection()                             │  │
│   │                                                                  │  │
│   │   1. _send_gate.clear()  ──> Block new sends                     │  │
│   │   2. Invoke BidiBeforeConnectionRestartEvent hook                │  │
│   │   3. model.stop()        ──> Close old connection                │  │
│   │   4. model.start(        ──> Open new connection                 │  │
│   │        system_prompt,                                            │  │
│   │        tools,                                                    │  │
│   │        messages          ──> Includes full history!              │  │
│   │      )                                                           │  │
│   │   5. Start new _run_model() task                                 │  │
│   │   6. Invoke BidiAfterConnectionRestartEvent hook                 │  │
│   │   7. _send_gate.set()    ──> Allow sends again                   │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│            │                                                            │
│            │  Conversation continues seamlessly...                      │
│            │                                                            │
│   t=16min  Next timeout, repeat...                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Connection Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION STATE MACHINE                             │
│                                                                         │
│                      ┌───────────────┐                                  │
│                      │   CREATED     │                                  │
│                      │   (init)      │                                  │
│                      └───────┬───────┘                                  │
│                              │ start()                                  │
│                              v                                          │
│                      ┌───────────────┐                                  │
│                      │   STARTING    │                                  │
│                      │               │                                  │
│                      └───────┬───────┘                                  │
│                              │ WebSocket connected                      │
│                              │ Init events sent                         │
│                              v                                          │
│                      ┌───────────────┐                                  │
│              ┌──────>│    ACTIVE     │<──────┐                          │
│              │       │               │       │                          │
│              │       └───────┬───────┘       │                          │
│              │               │               │                          │
│              │    ┌──────────┼──────────┐    │                          │
│              │    │          │          │    │                          │
│              │    v          v          v    │                          │
│      ┌───────────────┐  ┌────────┐  ┌───────────────┐                   │
│      │  RESTARTING   │  │ ERROR  │  │   CLOSING     │                   │
│      │  (timeout)    │  │        │  │   (user)      │                   │
│      └───────┬───────┘  └────┬───┘  └───────┬───────┘                   │
│              │               │              │                           │
│              │ reconnect     │              │ stop()                    │
│              │ success       │              │                           │
│              └───────────────┤              v                           │
│                              │      ┌───────────────┐                   │
│                              └─────>│    CLOSED     │                   │
│                                     │               │                   │
│                                     └───────────────┘                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### Basic Voice Assistant

```python
import asyncio
from strands.experimental.bidi import (
    BidiAgent,
    BidiNovaSonicModel,
    BidiAudioIO,
)

async def main():
    # Initialize model and agent
    model = BidiNovaSonicModel()
    agent = BidiAgent(
        model=model,
        system_prompt="You are a helpful voice assistant.",
    )

    # Setup audio I/O
    audio_io = BidiAudioIO()

    # Run the agent with audio channels
    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output()],
    )

asyncio.run(main())
```

### Manual Event Loop Control

```python
import asyncio
from strands.experimental.bidi import (
    BidiAgent,
    BidiNovaSonicModel,
    BidiAudioStreamEvent,
    BidiTranscriptStreamEvent,
)

async def main():
    agent = BidiAgent(
        model=BidiNovaSonicModel(),
        system_prompt="You are a helpful assistant.",
    )

    # Start the connection
    await agent.start()

    try:
        # Send a text message
        await agent.send("Hello, how are you?")

        # Process events
        async for event in agent.receive():
            if isinstance(event, BidiTranscriptStreamEvent):
                print(f"[{event.role}]: {event.text}")
            elif isinstance(event, BidiAudioStreamEvent):
                # Handle audio output
                audio_bytes = base64.b64decode(event.audio)
                # ... play audio ...
    finally:
        await agent.stop()

asyncio.run(main())
```

### With Tools

```python
from strands.experimental.bidi import BidiAgent, BidiNovaSonicModel, stop_conversation
from strands.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"The weather in {city} is 72F and sunny."

async def main():
    agent = BidiAgent(
        model=BidiNovaSonicModel(),
        tools=[get_weather, stop_conversation],
        system_prompt="You are a weather assistant.",
    )

    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output()],
    )
```

### With Context Manager

```python
async def main():
    agent = BidiAgent(model=BidiNovaSonicModel())

    async with agent:  # Calls start() and stop() automatically
        await agent.send("Tell me a joke")

        async for event in agent.receive():
            handle_event(event)
```

---

## Supported Models

| Model | Provider | Protocol | Status | Features |
|-------|----------|----------|--------|----------|
| Nova Sonic | Amazon Bedrock | HTTP/2 Event Streams | Implemented | Audio I/O, Tools, Interruption |
| OpenAI Realtime | OpenAI | WebSocket | Planned | Audio I/O, Tools |
| Gemini Live | Google | WebSocket | Planned | Audio I/O, Video |

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `agent/agent.py` | Main BidiAgent class |
| `agent/loop.py` | Event processing loop |
| `models/model.py` | BidiModel protocol |
| `models/nova_sonic.py` | Nova Sonic implementation |
| `io/audio.py` | Audio input/output handling |
| `io/text.py` | Text input/output handling |
| `types/events.py` | All event type definitions |
| `tools/stop_conversation.py` | Built-in stop tool |

---

## Summary

The Bidi Agent architecture provides:

1. **Abstraction**: Clean separation between I/O, agent logic, and model communication
2. **Flexibility**: Protocol-based model interface allows multiple providers
3. **Real-time**: Concurrent async tasks enable true bidirectional streaming
4. **Resilience**: Automatic connection restart on timeout
5. **Extensibility**: Hook system and tool support for customization

The design follows an event-driven architecture where all communication happens through typed events, making it easy to handle different input/output modalities and integrate with various model providers.
