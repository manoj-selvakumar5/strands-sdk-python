# Bidi Agent Event Flow Guide

This document explains the complete event lifecycle in the Strands SDK's Bidirectional (Bidi) Agent system - where events originate, how they flow through the system, and where they are consumed.

---

## Table of Contents

1. [Event System Overview](#event-system-overview)
2. [Event Origin and Destination](#event-origin-and-destination)
3. [Complete Flow Diagrams](#complete-flow-diagrams)
4. [Detailed Examples](#detailed-examples)
5. [Event Reference Table](#event-reference-table)

---

## Event System Overview

The Bidi Agent uses a **typed event architecture** where all communication happens through well-defined event objects. Events flow bidirectionally between user applications, the agent loop, and the model.

### Event Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVENT HIERARCHY                                    │
│                                                                             │
│   INPUT EVENTS (User → Model)          OUTPUT EVENTS (Model → User)         │
│   ┌─────────────────────────┐          ┌─────────────────────────────────┐ │
│   │ BidiTextInputEvent      │          │ CONNECTION LIFECYCLE            │ │
│   │ BidiAudioInputEvent     │          │   BidiConnectionStartEvent      │ │
│   │ BidiImageInputEvent     │          │   BidiConnectionRestartEvent    │ │
│   └─────────────────────────┘          │   BidiConnectionCloseEvent      │ │
│                                        │                                  │ │
│   TOOL EVENTS (Bidirectional)          │ RESPONSE LIFECYCLE              │ │
│   ┌─────────────────────────┐          │   BidiResponseStartEvent        │ │
│   │ ToolUseStreamEvent      │ ←────    │   BidiResponseCompleteEvent     │ │
│   │ ToolResultEvent         │ ────→    │                                  │ │
│   └─────────────────────────┘          │ CONTENT STREAMING               │ │
│                                        │   BidiAudioStreamEvent          │ │
│                                        │   BidiTranscriptStreamEvent     │ │
│                                        │                                  │ │
│                                        │ CONTROL                         │ │
│                                        │   BidiInterruptionEvent         │ │
│                                        │   BidiUsageEvent                │ │
│                                        │   BidiErrorEvent                │ │
│                                        └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | File | Role |
|-----------|------|------|
| **BidiAgent** | `agent/agent.py` | Main entry point, manages model and tools |
| **_BidiAgentLoop** | `agent/loop.py` | Event processing, queuing, and dispatch |
| **BidiModel** | `models/model.py` | Protocol for model implementations |
| **BidiNovaSonicModel** | `models/nova_sonic.py` | Amazon Bedrock Nova Sonic implementation |
| **Event Types** | `types/events.py` | All event class definitions |

---

## Event Origin and Destination

### Input Events

| Event | Origin | Processing | Destination |
|-------|--------|------------|-------------|
| `BidiTextInputEvent` | User application | `agent.send()` → `model.send()` | Model (Nova Sonic) |
| `BidiAudioInputEvent` | Microphone/Audio source | `agent.send()` → `model.send()` | Model (Nova Sonic) |
| `BidiImageInputEvent` | Camera/Image source | `agent.send()` → `model.send()` | Model (Nova Sonic) |

### Output Events

| Event | Origin | Processing | Destination |
|-------|--------|------------|-------------|
| `BidiConnectionStartEvent` | Model implementation | `model.receive()` → event queue | User via `agent.receive()` |
| `BidiConnectionRestartEvent` | Agent loop (on timeout) | Created in `_restart_connection()` | User via `agent.receive()` |
| `BidiConnectionCloseEvent` | Model or Agent | `model.receive()` → event queue | User via `agent.receive()` |
| `BidiResponseStartEvent` | Model (on `completionStart`) | Translated from Nova event | User via `agent.receive()` |
| `BidiResponseCompleteEvent` | Model (on `completionEnd`) | Translated from Nova event | User via `agent.receive()` |
| `BidiAudioStreamEvent` | Model (on `audioOutput`) | Translated from Nova event | User via `agent.receive()` |
| `BidiTranscriptStreamEvent` | Model (on `textOutput`) | Queued + appended to messages | User via `agent.receive()` |
| `BidiInterruptionEvent` | Model (VAD detection) | Queued + triggers hook | User via `agent.receive()` |
| `BidiUsageEvent` | Model (on `usageEvent`) | Translated from Nova event | User via `agent.receive()` |
| `BidiErrorEvent` | Any component | Created on exception | User via `agent.receive()` |
| `ToolUseStreamEvent` | Model (on `toolUse`) | Spawns `_run_tool()` task | User + Tool executor |
| `ToolResultEvent` | Tool executor | Sent back to model | Model (Nova Sonic) |

---

## Complete Flow Diagrams

### 1. Basic Event Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BIDI EVENT FLOW ARCHITECTURE                          │
│                                                                             │
│  USER APPLICATION                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │   send()                                          receive()          │   │
│  │     │                                                 ▲              │   │
│  │     │  BidiTextInputEvent                             │              │   │
│  │     │  BidiAudioInputEvent          BidiOutputEvent   │              │   │
│  │     │  BidiImageInputEvent                            │              │   │
│  │     ▼                                                 │              │   │
│  └─────┼─────────────────────────────────────────────────┼──────────────┘   │
│        │                                                 │                   │
│  ┌─────┼─────────────────────────────────────────────────┼──────────────┐   │
│  │     │              _BidiAgentLoop                     │              │   │
│  │     ▼                                                 │              │   │
│  │  ┌──────────────┐                              ┌──────────────┐     │   │
│  │  │ send()       │                              │ receive()    │     │   │
│  │  │  - wait gate │                              │  - dequeue   │     │   │
│  │  │  - forward   │                              │  - yield     │     │   │
│  │  └──────┬───────┘                              └──────▲───────┘     │   │
│  │         │                                             │              │   │
│  │         │                    ┌────────────┐           │              │   │
│  │         │                    │ Event Queue│───────────┘              │   │
│  │         │                    │ (maxsize=1)│                          │   │
│  │         │                    └──────▲─────┘                          │   │
│  │         │                           │                                │   │
│  │         │    ┌──────────────────────┴───────────────────────┐       │   │
│  │         │    │              _run_model() Task               │       │   │
│  │         │    │                                              │       │   │
│  │         │    │   async for event in model.receive():       │       │   │
│  │         │    │       put(event) in queue                   │       │   │
│  │         │    │       if TranscriptStream: append messages  │       │   │
│  │         │    │       if ToolUseStream: spawn _run_tool()   │       │   │
│  │         │    │       if Interruption: invoke hook          │       │   │
│  │         │    │                                              │       │   │
│  │         │    └──────────────────────▲───────────────────────┘       │   │
│  │         │                           │                                │   │
│  │         │    ┌──────────────────────┴───────────────────────┐       │   │
│  │         │    │              _run_tool() Tasks               │       │   │
│  │         │    │                                              │       │   │
│  │         │    │   Execute tool via tool_executor._stream()  │       │   │
│  │         │    │   Put intermediate events in queue          │       │   │
│  │         │    │   Append tool_use + tool_result to messages │       │   │
│  │         │    │   Send ToolResultEvent back to model        │       │   │
│  │         │    │                                              │       │   │
│  │         │    └──────────────────────────────────────────────┘       │   │
│  │         │                                                           │   │
│  └─────────┼───────────────────────────────────────────────────────────┘   │
│            │                                                               │
│  ┌─────────┼───────────────────────────────────────────────────────────┐   │
│  │         ▼              BidiModel (Nova Sonic)                       │   │
│  │  ┌──────────────┐                              ┌──────────────┐     │   │
│  │  │ send()       │                              │ receive()    │     │   │
│  │  │              │                              │              │     │   │
│  │  │  Translate   │                              │  Translate   │     │   │
│  │  │  SDK events  │                              │  Nova events │     │   │
│  │  │  to Nova     │                              │  to SDK      │     │   │
│  │  │  protocol    │                              │  events      │     │   │
│  │  └──────┬───────┘                              └──────▲───────┘     │   │
│  │         │                                             │              │   │
│  │         │         HTTP/2 Bidirectional Stream         │              │   │
│  │         └─────────────────────────────────────────────┘              │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Amazon Bedrock (Cloud)                          │  │
│  │                                                                      │  │
│  │                        Nova Sonic Model                              │  │
│  │                   (amazon.nova-sonic-v1:0)                           │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Text Conversation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TEXT CONVERSATION EVENT FLOW                           │
│                                                                             │
│  STEP 1: User sends text                                                    │
│  ────────────────────────────────────────────────────────────────────────   │
│                                                                             │
│  User Code                        Agent Loop                   Model        │
│     │                                │                           │          │
│     │  BidiTextInputEvent            │                           │          │
│     │  {type: "bidi_text_input",     │                           │          │
│     │   text: "Hello!",              │                           │          │
│     │   role: "user"}                │                           │          │
│     │ ───────────────────────────────>                           │          │
│     │                                │                           │          │
│     │                                │  Nova Protocol Events:    │          │
│     │                                │  1. contentStart          │          │
│     │                                │  2. textInput             │          │
│     │                                │  3. contentEnd            │          │
│     │                                │ ─────────────────────────>│          │
│     │                                │                           │          │
│                                                                             │
│  STEP 2: Model generates response                                           │
│  ────────────────────────────────────────────────────────────────────────   │
│                                                                             │
│     │                                │                           │          │
│     │                                │  Nova Protocol Events:    │          │
│     │                                │ <─────────────────────────│          │
│     │                                │  1. completionStart       │          │
│     │                                │  2. contentStart          │          │
│     │                                │  3. textOutput (partial)  │          │
│     │                                │  4. textOutput (final)    │          │
│     │                                │  5. contentEnd            │          │
│     │                                │  6. completionEnd         │          │
│     │                                │  7. usageEvent            │          │
│     │                                │                           │          │
│                                                                             │
│  STEP 3: Events translated and delivered to user                            │
│  ────────────────────────────────────────────────────────────────────────   │
│                                                                             │
│     │                                │                           │          │
│     │  BidiResponseStartEvent        │                           │          │
│     │ <───────────────────────────────                           │          │
│     │                                │                           │          │
│     │  BidiTranscriptStreamEvent     │                           │          │
│     │  {role: "assistant",           │                           │          │
│     │   text: "Hi there!",           │                           │          │
│     │   is_final: false}             │                           │          │
│     │ <───────────────────────────────                           │          │
│     │                                │                           │          │
│     │  BidiTranscriptStreamEvent     │ (appends to messages)     │          │
│     │  {role: "assistant",           │                           │          │
│     │   text: "Hi there! How...",    │                           │          │
│     │   is_final: true}              │                           │          │
│     │ <───────────────────────────────                           │          │
│     │                                │                           │          │
│     │  BidiResponseCompleteEvent     │                           │          │
│     │  {stop_reason: "complete"}     │                           │          │
│     │ <───────────────────────────────                           │          │
│     │                                │                           │          │
│     │  BidiUsageEvent                │                           │          │
│     │  {input_tokens: 10,            │                           │          │
│     │   output_tokens: 15}           │                           │          │
│     │ <───────────────────────────────                           │          │
│     │                                │                           │          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. Audio Conversation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUDIO CONVERSATION EVENT FLOW                          │
│                                                                             │
│  Microphone          BidiAudioIO          Agent         Model (Nova Sonic)  │
│     │                    │                  │                    │          │
│  ┌──┴──┐                 │                  │                    │          │
│  │Speak│                 │                  │                    │          │
│  └──┬──┘                 │                  │                    │          │
│     │                    │                  │                    │          │
│     │ PCM audio chunk    │                  │                    │          │
│     │ ──────────────────>│                  │                    │          │
│     │                    │                  │                    │          │
│     │                    │ BidiAudioInputEvent                   │          │
│     │                    │ {audio: base64,  │                    │          │
│     │                    │  sample_rate: 16000,                  │          │
│     │                    │  channels: 1}    │                    │          │
│     │                    │ ────────────────>│                    │          │
│     │                    │                  │                    │          │
│     │                    │                  │ Nova audioInput    │          │
│     │                    │                  │ ──────────────────>│          │
│     │                    │                  │                    │          │
│     │                    │                  │         (STT + LLM + TTS)     │
│     │                    │                  │                    │          │
│     │                    │                  │ Nova completionStart          │
│     │                    │                  │ <──────────────────│          │
│     │                    │                  │                    │          │
│     │                    │                  │ Nova textOutput    │          │
│     │                    │                  │ (user transcript)  │          │
│     │                    │                  │ <──────────────────│          │
│     │                    │                  │                    │          │
│     │                    │ BidiTranscriptStreamEvent             │          │
│     │                    │ {role: "user",   │                    │          │
│     │                    │  text: "What's the weather?"}         │          │
│     │                    │ <────────────────│                    │          │
│     │                    │                  │                    │          │
│     │                    │                  │ Nova textOutput    │          │
│     │                    │                  │ (assistant text)   │          │
│     │                    │                  │ <──────────────────│          │
│     │                    │                  │                    │          │
│     │                    │ BidiTranscriptStreamEvent             │          │
│     │                    │ {role: "assistant",                   │          │
│     │                    │  text: "It's sunny today!"}           │          │
│     │                    │ <────────────────│                    │          │
│     │                    │                  │                    │          │
│     │                    │                  │ Nova audioOutput   │          │
│     │                    │                  │ (TTS audio)        │          │
│     │                    │                  │ <──────────────────│          │
│     │                    │                  │                    │          │
│     │                    │ BidiAudioStreamEvent                  │          │
│     │                    │ {audio: base64,  │                    │          │
│     │                    │  sample_rate: 24000}                  │          │
│     │                    │ <────────────────│                    │          │
│     │                    │                  │                    │          │
│     │ PCM audio chunk    │                  │                    │          │
│     │ <──────────────────│                  │                    │          │
│     │                    │                  │                    │          │
│  ┌──┴──┐                 │                  │                    │          │
│  │Speak│ (Speaker plays) │                  │                    │          │
│  └─────┘                 │                  │                    │          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOOL EXECUTION EVENT FLOW                            │
│                                                                             │
│  User               Agent Loop           Tool Executor          Model       │
│   │                     │                     │                    │        │
│   │                     │                     │  Nova toolUse      │        │
│   │                     │                     │ <───────────────────│        │
│   │                     │                     │                    │        │
│   │                     │ _run_model() receives ToolUseStreamEvent │        │
│   │                     │                     │                    │        │
│   │                     │ Spawns _run_tool()  │                    │        │
│   │                     │ task in _TaskPool   │                    │        │
│   │                     │ ───────────────────>│                    │        │
│   │                     │                     │                    │        │
│   │  ToolUseStreamEvent │                     │                    │        │
│   │  {name: "weather",  │                     │                    │        │
│   │   input: {city: "NYC"}}                   │                    │        │
│   │ <────────────────────                     │                    │        │
│   │                     │                     │                    │        │
│   │                     │                     │                    │        │
│   │                     │    _run_tool() executes:                 │        │
│   │                     │    1. Call tool_executor._stream()       │        │
│   │                     │    2. Get weather("NYC")                 │        │
│   │                     │    3. Tool returns "72F, Sunny"          │        │
│   │                     │                     │                    │        │
│   │                     │                     │                    │        │
│   │                     │ Append to messages: │                    │        │
│   │                     │  - tool_use message │                    │        │
│   │                     │  - tool_result message                   │        │
│   │                     │                     │                    │        │
│   │  ToolResultMessageEvent                   │                    │        │
│   │  {tool_result: "72F, Sunny"}              │                    │        │
│   │ <────────────────────                     │                    │        │
│   │                     │                     │                    │        │
│   │                     │                     │  ToolResultEvent   │        │
│   │                     │                     │  {content: "72F..."│        │
│   │                     │                     │ ───────────────────>│        │
│   │                     │                     │                    │        │
│   │                     │                     │  Nova continues... │        │
│   │                     │                     │ <───────────────────│        │
│   │                     │                     │                    │        │
│   │  BidiTranscriptStreamEvent                │                    │        │
│   │  "The weather in NYC is 72F and sunny!"   │                    │        │
│   │ <────────────────────                     │                    │        │
│   │                     │                     │                    │        │
│                                                                             │
│  NOTE: The special "stop_conversation" tool ends the session:               │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│   │                     │                     │                    │        │
│   │                     │ _run_tool("stop_conversation")           │        │
│   │                     │                     │                    │        │
│   │  BidiConnectionCloseEvent                 │                    │        │
│   │  {reason: "user_request"}                 │                    │        │
│   │ <────────────────────                     │                    │        │
│   │                     │                     │                    │        │
│   │  (receive() loop breaks - session ends)   │                    │        │
│   │                     │                     │                    │        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5. Interruption Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTERRUPTION EVENT FLOW                              │
│                                                                             │
│  Timeline showing user interrupting model mid-response:                     │
│                                                                             │
│  t=0.0s ─────────────────────────────────────────────────────────────────   │
│   │                                                                         │
│   │  Model speaking: "The weather forecast for today shows..."              │
│   │  ════════════════════════════════════════════════════>                  │
│   │                                                                         │
│   │  User               Agent Loop          Audio Output         Model      │
│   │   │                     │                    │                  │       │
│   │   │                     │  BidiAudioStreamEvent                 │       │
│   │   │                     │ <──────────────────────────────────────│       │
│   │   │                     │                    │                  │       │
│   │   │                     │                    │ Play audio       │       │
│   │   │                     │ ──────────────────>│                  │       │
│   │   │                     │                    │                  │       │
│   │                                                                         │
│  t=2.0s ─────────────────────────────────────────────────────────────────   │
│   │                                                                         │
│   │  User interrupts: "Wait, what about tomorrow?"                          │
│   │  <═══════════════════════════════════════                               │
│   │                                                                         │
│   │   │  BidiAudioInputEvent │                    │                  │       │
│   │   │ ────────────────────>│                    │                  │       │
│   │   │                     │ Send to model      │                  │       │
│   │   │                     │ ───────────────────────────────────────>      │
│   │   │                     │                    │                  │       │
│   │                                                                         │
│  t=2.1s ─────────────────────────────────────────────────────────────────   │
│   │                                                                         │
│   │  Model detects speech via VAD (Voice Activity Detection)                │
│   │                                                                         │
│   │   │                     │                    │  Nova textOutput │       │
│   │   │                     │                    │  '{"interrupted":true}'  │
│   │   │                     │ <──────────────────────────────────────│       │
│   │   │                     │                    │                  │       │
│   │   │                     │ Translate to:      │                  │       │
│   │   │                     │ BidiInterruptionEvent                 │       │
│   │   │                     │                    │                  │       │
│   │                                                                         │
│  t=2.2s ─────────────────────────────────────────────────────────────────   │
│   │                                                                         │
│   │  Interruption hook invoked, audio buffer cleared                        │
│   │                                                                         │
│   │   │                     │ invoke_callbacks_async(               │       │
│   │   │                     │   BidiInterruptionHookEvent)          │       │
│   │   │                     │                    │                  │       │
│   │   │                     │                    │ _buffer.clear()  │       │
│   │   │                     │ ──────────────────>│ (stop playback)  │       │
│   │   │                     │                    │                  │       │
│   │   │  BidiInterruptionEvent                   │                  │       │
│   │   │  {reason: "user_speech"}                 │                  │       │
│   │   │ <────────────────────                    │                  │       │
│   │   │                     │                    │                  │       │
│   │                                                                         │
│  t=2.3s ─────────────────────────────────────────────────────────────────   │
│   │                                                                         │
│   │  Model processes new input and responds                                 │
│   │  "Tomorrow will be partly cloudy with..."                               │
│   │  ════════════════════════════════════════════════════>                  │
│   │                                                                         │
│   │   │  BidiResponseStartEvent                  │                  │       │
│   │   │ <────────────────────                    │                  │       │
│   │   │                     │                    │                  │       │
│   │   │  BidiTranscriptStreamEvent               │                  │       │
│   │   │  "Tomorrow will be partly cloudy..."     │                  │       │
│   │   │ <────────────────────                    │                  │       │
│   │   │                     │                    │                  │       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6. Connection Timeout & Restart Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION TIMEOUT & RESTART FLOW                        │
│                                                                             │
│  Nova Sonic has an 8-minute connection limit. The SDK handles this          │
│  transparently by automatically reconnecting and replaying message history. │
│                                                                             │
│  User               Agent Loop                    Model                     │
│   │                     │                           │                       │
│   │                     │                           │                       │
│  t=0min ───────── Connection established ───────────────────────────────    │
│   │                     │                           │                       │
│   │                     │ BidiConnectionStartEvent  │                       │
│   │ <────────────────────                           │                       │
│   │                     │                           │                       │
│   │  ... normal conversation for ~8 minutes ...     │                       │
│   │                     │                           │                       │
│  t=8min ───────── Connection timeout ───────────────────────────────────    │
│   │                     │                           │                       │
│   │                     │   ValidationException     │                       │
│   │                     │   (InternalErrorCode=531) │                       │
│   │                     │ <──────────────────────────│                       │
│   │                     │                           │                       │
│   │                     │ Convert to BidiModelTimeoutError                  │
│   │                     │                           │                       │
│   │  BidiConnectionRestartEvent                     │                       │
│   │  {timeout_error: ...}                           │                       │
│   │ <────────────────────                           │                       │
│   │                     │                           │                       │
│   │                     │ _restart_connection():    │                       │
│   │                     │                           │                       │
│   │                     │ 1. _send_gate.clear()     │                       │
│   │                     │    (block new sends)      │                       │
│   │                     │                           │                       │
│   │                     │ 2. Invoke hook:           │                       │
│   │                     │    BidiBeforeConnectionRestartEvent               │
│   │                     │                           │                       │
│   │                     │ 3. model.stop()           │                       │
│   │                     │    (close old connection) │                       │
│   │                     │                           │                       │
│   │                     │ 4. model.start(           │  New HTTP/2 stream    │
│   │                     │      system_prompt,       │ ─────────────────────>│
│   │                     │      tools,               │                       │
│   │                     │      messages ◄── Full history replayed!          │
│   │                     │    )                      │                       │
│   │                     │                           │                       │
│   │                     │ 5. Start new _run_model() │                       │
│   │                     │    task                   │                       │
│   │                     │                           │                       │
│   │                     │ 6. Invoke hook:           │                       │
│   │                     │    BidiAfterConnectionRestartEvent                │
│   │                     │                           │                       │
│   │                     │ 7. _send_gate.set()       │                       │
│   │                     │    (allow sends again)    │                       │
│   │                     │                           │                       │
│   │  ... conversation continues seamlessly ...      │                       │
│   │                     │                           │                       │
│  t=16min ───────── Next timeout, repeat... ─────────────────────────────    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Examples

### Example 1: Basic Voice Assistant

```python
import asyncio
from strands.experimental.bidi import (
    BidiAgent,
    BidiNovaSonicModel,
    BidiAudioIO,
    BidiAudioStreamEvent,
    BidiTranscriptStreamEvent,
    BidiResponseStartEvent,
    BidiResponseCompleteEvent,
    BidiConnectionCloseEvent,
)

async def main():
    # 1. Create model and agent
    model = BidiNovaSonicModel(
        model_id="amazon.nova-sonic-v1:0",
        provider_config={
            "audio": {
                "input_rate": 16000,
                "output_rate": 24000,
                "channels": 1,
                "voice": "matthew",
            }
        }
    )

    agent = BidiAgent(
        model=model,
        system_prompt="You are a helpful voice assistant.",
    )

    # 2. Create audio I/O handler
    audio_io = BidiAudioIO()

    # 3. Run agent - this handles the event loop automatically
    await agent.run(
        inputs=[audio_io.input()],   # Captures microphone audio
        outputs=[audio_io.output()], # Plays speaker audio
    )

asyncio.run(main())
```

**Event Flow During Execution:**

```
1. agent.run() calls agent.start()
   └── BidiConnectionStartEvent emitted

2. audio_io.input() captures microphone
   └── Yields BidiAudioInputEvent every ~100ms

3. agent.send(BidiAudioInputEvent) forwards to model
   └── Nova processes audio (STT + LLM + TTS)

4. agent.receive() yields events:
   ├── BidiTranscriptStreamEvent (user speech transcript)
   ├── BidiResponseStartEvent
   ├── BidiTranscriptStreamEvent (assistant response)
   ├── BidiAudioStreamEvent (audio chunks)
   └── BidiResponseCompleteEvent

5. audio_io.output() receives BidiAudioStreamEvent
   └── Decodes base64 and plays through speaker
```

### Example 2: Manual Event Loop with Custom Handling

```python
import asyncio
import base64
from strands.experimental.bidi import (
    BidiAgent,
    BidiNovaSonicModel,
    BidiTextInputEvent,
    BidiAudioStreamEvent,
    BidiTranscriptStreamEvent,
    BidiResponseStartEvent,
    BidiResponseCompleteEvent,
    BidiInterruptionEvent,
    BidiConnectionCloseEvent,
    BidiUsageEvent,
    BidiErrorEvent,
)

async def main():
    agent = BidiAgent(
        model=BidiNovaSonicModel(),
        system_prompt="You are a helpful assistant.",
    )

    # Start connection - yields BidiConnectionStartEvent internally
    await agent.start()

    try:
        # Send text input
        await agent.send(BidiTextInputEvent(
            text="What's the capital of France?",
            role="user"
        ))

        # Process all response events
        async for event in agent.receive():

            # Connection lifecycle
            if isinstance(event, BidiResponseStartEvent):
                print(f"[Response started: {event['response_id']}]")

            elif isinstance(event, BidiResponseCompleteEvent):
                print(f"[Response complete: {event['stop_reason']}]")

            # Content events
            elif isinstance(event, BidiTranscriptStreamEvent):
                role = event["role"]
                text = event["text"]
                is_final = event["is_final"]
                print(f"[{role}] {text}" + (" (final)" if is_final else ""))

            elif isinstance(event, BidiAudioStreamEvent):
                # Decode and process audio
                audio_bytes = base64.b64decode(event["audio"])
                sample_rate = event["sample_rate"]
                print(f"[Audio chunk: {len(audio_bytes)} bytes @ {sample_rate}Hz]")
                # ... play audio with PyAudio, sounddevice, etc.

            # Control events
            elif isinstance(event, BidiInterruptionEvent):
                print(f"[Interrupted: {event['reason']}]")

            elif isinstance(event, BidiUsageEvent):
                print(f"[Tokens: in={event['input_tokens']}, out={event['output_tokens']}]")

            elif isinstance(event, BidiErrorEvent):
                print(f"[Error: {event['message']}]")

            elif isinstance(event, BidiConnectionCloseEvent):
                print(f"[Connection closed: {event['reason']}]")
                break  # Exit loop

    finally:
        await agent.stop()

asyncio.run(main())
```

**Console Output:**

```
[Response started: resp_abc123]
[user] What's the capital of France? (final)
[assistant] The capital
[assistant] The capital of France
[assistant] The capital of France is Paris. (final)
[Audio chunk: 4800 bytes @ 24000Hz]
[Audio chunk: 4800 bytes @ 24000Hz]
[Audio chunk: 4800 bytes @ 24000Hz]
[Response complete: complete]
[Tokens: in=12, out=8]
```

### Example 3: Tool Execution with Weather API

```python
import asyncio
from strands.experimental.bidi import (
    BidiAgent,
    BidiNovaSonicModel,
    BidiAudioIO,
    stop_conversation,
)
from strands.tools import tool
from strands.types import ToolUseStreamEvent, ToolResultMessageEvent

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to get weather for
    """
    # In real app, call weather API
    weather_data = {
        "New York": "72°F, Sunny",
        "London": "58°F, Cloudy",
        "Tokyo": "68°F, Clear",
    }
    return weather_data.get(city, f"Weather data not available for {city}")

async def main():
    agent = BidiAgent(
        model=BidiNovaSonicModel(),
        tools=[get_weather, stop_conversation],
        system_prompt="""You are a weather assistant.
        Use the get_weather tool when users ask about weather.
        Say goodbye and use stop_conversation when user wants to end.""",
    )

    await agent.start()

    try:
        # Send voice query (or text for testing)
        await agent.send("What's the weather in New York?")

        async for event in agent.receive():
            if isinstance(event, ToolUseStreamEvent):
                tool_use = event["current_tool_use"]
                print(f"[Tool Call] {tool_use['name']}({tool_use['input']})")

            elif isinstance(event, ToolResultMessageEvent):
                result = event["message"]["content"][0]["toolResult"]
                print(f"[Tool Result] {result['content']}")

            elif isinstance(event, BidiTranscriptStreamEvent):
                if event["is_final"]:
                    print(f"[{event['role']}] {event['text']}")

    finally:
        await agent.stop()

asyncio.run(main())
```

**Event Sequence:**

```
1. User: "What's the weather in New York?"

2. Model processes and decides to call tool:
   └── ToolUseStreamEvent {name: "get_weather", input: {city: "New York"}}

3. Agent loop spawns _run_tool() task:
   ├── Executes get_weather("New York")
   ├── Returns "72°F, Sunny"
   └── Sends ToolResultEvent back to model

4. Model incorporates result and responds:
   └── BidiTranscriptStreamEvent "The weather in New York is 72°F and sunny!"

5. User: "Thanks, goodbye"

6. Model calls stop_conversation tool:
   └── ToolUseStreamEvent {name: "stop_conversation", input: {}}

7. Agent emits close event:
   └── BidiConnectionCloseEvent {reason: "user_request"}

8. receive() loop breaks, session ends
```

### Example 4: Handling Connection Restarts

```python
import asyncio
from strands.experimental.bidi import (
    BidiAgent,
    BidiNovaSonicModel,
    BidiConnectionStartEvent,
    BidiConnectionRestartEvent,
    BidiTranscriptStreamEvent,
)

async def main():
    agent = BidiAgent(
        model=BidiNovaSonicModel(),
        system_prompt="You are a helpful assistant for long conversations.",
    )

    await agent.start()

    message_count = 0

    try:
        async for event in agent.receive():

            if isinstance(event, BidiConnectionStartEvent):
                print(f"[Connected: {event['connection_id']}]")

            elif isinstance(event, BidiConnectionRestartEvent):
                # This happens every ~8 minutes
                print("[Connection restarting due to timeout...]")
                print("[Message history will be replayed automatically]")
                # Connection restarts transparently - no action needed

            elif isinstance(event, BidiTranscriptStreamEvent):
                if event["is_final"] and event["role"] == "assistant":
                    message_count += 1
                    print(f"[Message #{message_count}] {event['text'][:50]}...")

    finally:
        await agent.stop()
        print(f"[Session ended after {message_count} messages]")

asyncio.run(main())
```

**Long Conversation Timeline:**

```
t=0:00   [Connected: conn_abc123]
t=0:01   [Message #1] Hello! How can I help you today?...
t=2:30   [Message #15] That's a great question about...
t=5:00   [Message #42] Based on our earlier discussion...
t=8:00   [Connection restarting due to timeout...]
         [Message history will be replayed automatically]
t=8:02   [Connected: conn_def456]  # New connection ID
t=8:03   [Message #43] Continuing where we left off...  # Seamless!
t=12:00  [Message #89] ...
t=16:00  [Connection restarting due to timeout...]
...
```

### Example 5: Using Hooks for Custom Behavior

```python
import asyncio
from strands.experimental.bidi import (
    BidiAgent,
    BidiNovaSonicModel,
    BidiAudioIO,
)
from strands.experimental.bidi.types import (
    BidiBeforeInvocationEvent,
    BidiInterruptionHookEvent,
    BidiBeforeConnectionRestartEvent,
    BidiAfterConnectionRestartEvent,
)

# Define hook handlers
async def on_invocation_start(event: BidiBeforeInvocationEvent):
    print("[Hook] Conversation starting...")

async def on_interruption(event: BidiInterruptionHookEvent):
    print(f"[Hook] User interrupted! Reason: {event.reason}")
    # Could log analytics, adjust UI, etc.

async def on_before_restart(event: BidiBeforeConnectionRestartEvent):
    print("[Hook] Connection about to restart...")
    # Could show loading indicator

async def on_after_restart(event: BidiAfterConnectionRestartEvent):
    if event.exception:
        print(f"[Hook] Restart failed: {event.exception}")
    else:
        print("[Hook] Connection restored successfully!")

async def main():
    agent = BidiAgent(
        model=BidiNovaSonicModel(),
        system_prompt="You are a helpful voice assistant.",
    )

    # Register hooks
    agent.hooks.add_callback(BidiBeforeInvocationEvent, on_invocation_start)
    agent.hooks.add_callback(BidiInterruptionHookEvent, on_interruption)
    agent.hooks.add_callback(BidiBeforeConnectionRestartEvent, on_before_restart)
    agent.hooks.add_callback(BidiAfterConnectionRestartEvent, on_after_restart)

    audio_io = BidiAudioIO()

    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output()],
    )

asyncio.run(main())
```

---

## Event Reference Table

### Input Events

| Event | Type String | Fields | Origin | Destination |
|-------|-------------|--------|--------|-------------|
| `BidiTextInputEvent` | `bidi_text_input` | `text: str`, `role: Role` | User app | Model |
| `BidiAudioInputEvent` | `bidi_audio_input` | `audio: str` (base64), `format: AudioFormat`, `sample_rate: AudioSampleRate`, `channels: AudioChannel` | Microphone/Audio | Model |
| `BidiImageInputEvent` | `bidi_image_input` | `image: str` (base64), `mime_type: str` | Camera/Image | Model |

### Output Events

| Event | Type String | Fields | Origin | Destination |
|-------|-------------|--------|--------|-------------|
| `BidiConnectionStartEvent` | `bidi_connection_start` | `connection_id: str`, `model: str` | Model impl | User app |
| `BidiConnectionRestartEvent` | `bidi_connection_restart` | `timeout_error: BidiModelTimeoutError` | Agent loop | User app |
| `BidiConnectionCloseEvent` | `bidi_connection_close` | `connection_id: str`, `reason: str` | Model/Agent | User app |
| `BidiResponseStartEvent` | `bidi_response_start` | `response_id: str` | Model | User app |
| `BidiResponseCompleteEvent` | `bidi_response_complete` | `response_id: str`, `stop_reason: StopReason` | Model | User app |
| `BidiAudioStreamEvent` | `bidi_audio_stream` | `audio: str` (base64), `format`, `sample_rate`, `channels` | Model | User app |
| `BidiTranscriptStreamEvent` | `bidi_transcript_stream` | `text: str`, `role: Role`, `is_final: bool`, `delta`, `current_transcript` | Model | User app |
| `BidiInterruptionEvent` | `bidi_interruption` | `reason: str` | Model (VAD) | User app |
| `BidiUsageEvent` | `bidi_usage` | `input_tokens`, `output_tokens`, `total_tokens`, `modality_details` | Model | User app |
| `BidiErrorEvent` | `bidi_error` | `message: str`, `code: str`, `details: dict` | Any | User app |

### Tool Events

| Event | Type String | Fields | Origin | Destination |
|-------|-------------|--------|--------|-------------|
| `ToolUseStreamEvent` | `tool_use_stream` | `delta`, `current_tool_use: {toolUseId, name, input}` | Model | Agent loop + User |
| `ToolResultEvent` | `tool_result` | `tool_result: ToolResult` | Tool executor | Model |
| `ToolResultMessageEvent` | `tool_result_message` | `message: Message` | Agent loop | User app |

### Type Definitions

```python
Role = Literal["user", "assistant"]
StopReason = Literal["complete", "error", "interrupted", "tool_use"]
AudioFormat = Literal["pcm", "wav", "opus", "mp3"]
AudioSampleRate = Literal[16000, 24000, 48000]
AudioChannel = Literal[1, 2]  # mono, stereo
```

---

## Summary

The Bidi Agent event system provides:

1. **Clear Event Origins**: Each event type has a well-defined source (user, model, or agent loop)
2. **Typed Architecture**: All events extend `TypedEvent` for consistent handling
3. **Async Flow**: Events flow through queues enabling concurrent processing
4. **Automatic Recovery**: Connection timeouts handled transparently with history replay
5. **Hook Integration**: Lifecycle events can trigger custom callbacks
6. **Tool Support**: Bidirectional tool events enable model-driven actions

For the complete architecture overview, see [BIDI_ARCHITECTURE.md](./BIDI_ARCHITECTURE.md).
