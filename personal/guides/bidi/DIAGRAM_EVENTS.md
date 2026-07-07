# Bidi Architecture Diagram: Event Mapping Guide

This document maps the visual architecture diagram to the actual SDK events, explaining how each component corresponds to specific event types in the Strands Bidi Agent system.

---

## Table of Contents

1. [Original Diagram (ASCII Representation)](#original-diagram-ascii-representation)
2. [Component-to-Event Mapping](#component-to-event-mapping)
3. [Enhanced Diagram with Events](#enhanced-diagram-with-events)
4. [Detailed Component Analysis](#detailed-component-analysis)
5. [Event Flow by Layer](#event-flow-by-layer)
6. [Complete Mapping Reference](#complete-mapping-reference)

---

## Original Diagram (ASCII Representation)

Your architecture diagram shows the Bidi Agent system in three layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                            USER                                  │
│                                                                  │
│                      ┌──────────────┐                           │
│                      │  Microphone  │                           │
│                      └──────┬───────┘                           │
│                             │                                    │
│                             ▼                                    │
│   ┌──────────────┐   ┌──────────────┐                           │
│   │  Text Input  │   │ Audio Input  │                           │
│   └──────┬───────┘   └──────┬───────┘                           │
│          │                  │                                    │
│          └────────┬─────────┘                                    │
│                   ▼                                              │
│            ┌──────────────┐                                      │
│            │ Input Events │                                      │
│            └──────┬───────┘                                      │
└───────────────────┼──────────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────┼──────────────────────────────────────────────┐
│                   │         BIDI AGENT                           │
│            ┌──────▼───────┐                                      │
│            │  Agent Loop  │                                      │
│            └──────┬───────┘                                      │
│                   │                                              │
│                   ▼                                              │
│            ┌──────────────────┐                                  │
│            │ Model Connection │◄────────┐                        │
│            └──────┬───────────┘         │                        │
│                   │               ┌─────┴────────┐               │
│                   │               │    Tool      │               │
│                   │               │  Execution   │               │
│                   │               └──────────────┘               │
│                   ▼                                              │
│            ┌──────────────┐                                      │
│            │Output Events │                                      │
│            └──────┬───────┘                                      │
└───────────────────┼──────────────────────────────────────────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                          OUTPUT                                  │
│                                                                  │
│   ┌──────────────┐               ┌──────────────┐               │
│   │ Audio Output │               │ Text Output  │               │
│   └──────┬───────┘               └──────┬───────┘               │
│          │                              │                        │
│          ▼                              ▼                        │
│   ┌──────────────┐               ┌──────────────┐               │
│   │   Speakers   │               │  Console/UI  │               │
│   └──────────────┘               └──────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component-to-Event Mapping

| Diagram Component | SDK Event Type | Description |
|-------------------|----------------|-------------|
| **Microphone** | (Hardware) | Physical audio capture device |
| **Audio Input** | `BidiAudioInputEvent` | Base64-encoded PCM audio chunks |
| **Text Input** | `BidiTextInputEvent` | User text messages |
| **Input Events** | `BidiInputEvent` (union) | `BidiTextInputEvent \| BidiAudioInputEvent \| BidiImageInputEvent` |
| **Agent Loop** | `_BidiAgentLoop` | Event queue + `_run_model()` task |
| **Model Connection** | `BidiModel.send()` / `receive()` | HTTP/2 stream to Nova Sonic |
| **Tool Execution** | `ToolUseStreamEvent` → `ToolResultEvent` | Bidirectional tool flow |
| **Output Events** | `BidiOutputEvent` (union) | All model response events |
| **Audio Output** | `BidiAudioStreamEvent` | Base64-encoded TTS audio |
| **Text Output** | `BidiTranscriptStreamEvent` | Speech-to-text transcripts |
| **Speakers** | (Hardware) | Audio playback device |
| **Console/UI** | (Application) | User interface display |

---

## Enhanced Diagram with Events

Here's your diagram annotated with the actual SDK event types flowing through each connection:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  USER                                        │
│                                                                             │
│                           ┌──────────────┐                                  │
│                           │  Microphone  │                                  │
│                           │  (PyAudio)   │                                  │
│                           └──────┬───────┘                                  │
│                                  │ PCM bytes                                │
│                                  ▼                                          │
│   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│   │    Text Input    │    │   Audio Input    │    │   Image Input    │     │
│   │                  │    │                  │    │   (optional)     │     │
│   └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘     │
│            │                       │                       │                │
│            │ BidiTextInputEvent    │ BidiAudioInputEvent   │ BidiImageInput │
│            │ {text, role}          │ {audio, sample_rate,  │ {image,        │
│            │                       │  channels, format}    │  mime_type}    │
│            └───────────────────────┼───────────────────────┘                │
│                                    │                                        │
│                                    ▼                                        │
│                         ┌────────────────────┐                              │
│                         │    Input Events    │                              │
│                         │   (BidiInputEvent) │                              │
│                         └─────────┬──────────┘                              │
│                                   │                                         │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │ await agent.send(event)
                                    ▼
┌───────────────────────────────────┼─────────────────────────────────────────┐
│                                   │           BIDI AGENT                     │
│                         ┌─────────▼──────────┐                              │
│                         │     Agent Loop     │                              │
│                         │  (_BidiAgentLoop)  │                              │
│                         │                    │                              │
│                         │  - _send_gate      │                              │
│                         │  - _event_queue    │                              │
│                         │  - _task_pool      │                              │
│                         └─────────┬──────────┘                              │
│                                   │                                         │
│                   ┌───────────────┴───────────────┐                         │
│                   │                               │                         │
│                   ▼                               ▼                         │
│        ┌────────────────────┐          ┌────────────────────┐              │
│        │  model.send()      │          │   model.receive()  │              │
│        │                    │          │                    │              │
│        │ Nova Protocol:     │          │ Nova Protocol:     │              │
│        │ - contentStart     │          │ - completionStart  │              │
│        │ - textInput        │          │ - textOutput       │              │
│        │ - audioInput       │          │ - audioOutput      │              │
│        │ - contentEnd       │          │ - toolUse          │              │
│        └─────────┬──────────┘          └─────────┬──────────┘              │
│                  │                               │                          │
│                  │    ┌──────────────────────────┼──────────────────┐       │
│                  │    │     Model Connection     │                  │       │
│                  │    │    (BidiNovaSonicModel)  │                  │       │
│                  │    │                          │                  │       │
│                  │    │  HTTP/2 Bidirectional    │                  │       │
│                  │    │  Stream (Bedrock API)    │                  │       │
│                  │    └──────────────────────────┼──────────────────┘       │
│                  │                               │                          │
│                  │                               │                          │
│                  │         ┌─────────────────────┼───────────┐              │
│                  │         │                     │           │              │
│                  │         │   Tool Execution    │           │              │
│                  │         │                     │           │              │
│                  │         │ ┌─────────────────┐ │           │              │
│                  │         │ │ToolUseStreamEvent│◄┘           │              │
│                  │         │ │{name, input,    │             │              │
│                  │         │ │ toolUseId}      │             │              │
│                  │         │ └────────┬────────┘             │              │
│                  │         │          │                      │              │
│                  │         │          ▼ _run_tool()          │              │
│                  │         │ ┌─────────────────┐             │              │
│                  │         │ │  Tool Executor  │             │              │
│                  │         │ │  (ToolRegistry) │             │              │
│                  │         │ └────────┬────────┘             │              │
│                  │         │          │                      │              │
│                  │         │          ▼                      │              │
│                  │         │ ┌─────────────────┐             │              │
│                  │         │ │ ToolResultEvent │─────────────┘              │
│                  │         │ │{toolUseId,      │ Sent back to model         │
│                  │         │ │ content}        │                            │
│                  │         │ └─────────────────┘                            │
│                  │         │                                                │
│                  │         └────────────────────────────────────┘           │
│                  │                                                          │
│                  │         Events translated and queued:                    │
│                  │                                                          │
│                  │         ┌─────────────────────────────────────┐          │
│                  │         │         Output Events                │          │
│                  │         │                                      │          │
│                  │         │ - BidiResponseStartEvent             │          │
│                  │         │ - BidiTranscriptStreamEvent          │          │
│                  │         │ - BidiAudioStreamEvent               │          │
│                  │         │ - BidiResponseCompleteEvent          │          │
│                  │         │ - BidiUsageEvent                     │          │
│                  │         │ - BidiInterruptionEvent              │          │
│                  │         │ - BidiConnectionCloseEvent           │          │
│                  │         │                                      │          │
│                  │         └──────────────────┬──────────────────┘          │
│                  │                            │                             │
└──────────────────┼────────────────────────────┼─────────────────────────────┘
                   │                            │ async for event in agent.receive()
                   │              ┌─────────────┴─────────────┐
                   │              │                           │
                   │              ▼                           ▼
┌──────────────────┼──────────────────────────────────────────────────────────┐
│                  │                    OUTPUT                                 │
│                  │                                                          │
│                  │    ┌─────────────────────┐    ┌─────────────────────┐    │
│                  │    │    Audio Output     │    │    Text Output      │    │
│                  │    │                     │    │                     │    │
│                  │    │ BidiAudioStreamEvent│    │BidiTranscriptStream │    │
│                  │    │ {audio: base64,     │    │Event                │    │
│                  │    │  format: "pcm",     │    │{text, role,         │    │
│                  │    │  sample_rate: 24000,│    │ is_final}           │    │
│                  │    │  channels: 1}       │    │                     │    │
│                  │    └──────────┬──────────┘    └──────────┬──────────┘    │
│                  │               │                          │               │
│                  │               │ base64.decode()          │ print()       │
│                  │               │ play_audio()             │ display()     │
│                  │               ▼                          ▼               │
│                  │    ┌─────────────────────┐    ┌─────────────────────┐    │
│                  │    │      Speakers       │    │     Console/UI      │    │
│                  │    │   (PyAudio/Sound)   │    │   (Terminal/App)    │    │
│                  │    └─────────────────────┘    └─────────────────────┘    │
│                  │                                                          │
└──────────────────┴──────────────────────────────────────────────────────────┘
```

---

## Detailed Component Analysis

### Layer 1: User (Input Sources)

#### Microphone → Audio Input

```
Physical Flow:
  Microphone (hardware)
       │
       │ PyAudio callback captures PCM bytes
       ▼
  _BidiAudioInput._buffer (internal buffer)
       │
       │ Periodically yields chunks
       ▼
  BidiAudioInputEvent created
```

**SDK Event:**
```python
BidiAudioInputEvent(
    type="bidi_audio_input",
    audio="<base64-encoded-pcm>",
    format="pcm",
    sample_rate=16000,  # or 24000, 48000
    channels=1,         # mono
)
```

**Code Location:** `src/strands/experimental/bidi/io/audio.py`

#### Text Input

```
Physical Flow:
  Keyboard / stdin / UI text field
       │
       │ User types message
       ▼
  BidiTextInputEvent created
```

**SDK Event:**
```python
BidiTextInputEvent(
    type="bidi_text_input",
    text="Hello, how are you?",
    role="user",
)
```

**Code Location:** `src/strands/experimental/bidi/types/events.py`

---

### Layer 2: BidiAgent (Processing)

#### Agent Loop

The Agent Loop is the central orchestrator that:
1. Receives input events via `send()`
2. Forwards to model via `model.send()`
3. Receives model events via `model.receive()`
4. Queues events for user via `_event_queue`
5. Spawns tool execution tasks

```
┌─────────────────────────────────────────────────────────────┐
│                      _BidiAgentLoop                          │
│                                                             │
│  ┌─────────────┐                    ┌─────────────────────┐ │
│  │ send()      │                    │ _run_model() task   │ │
│  │             │                    │                     │ │
│  │ wait gate   │                    │ async for event     │ │
│  │ model.send()│                    │   in model.receive()│ │
│  └─────────────┘                    │                     │ │
│                                     │ if Transcript:      │ │
│                                     │   append messages   │ │
│                                     │ if ToolUse:         │ │
│                                     │   spawn _run_tool() │ │
│                                     │ if Interruption:    │ │
│                                     │   invoke hook       │ │
│                                     │                     │ │
│                                     │ put in queue        │ │
│                                     └──────────┬──────────┘ │
│                                                │            │
│                                     ┌──────────▼──────────┐ │
│                                     │   _event_queue      │ │
│                                     │   (maxsize=1)       │ │
│                                     └──────────┬──────────┘ │
│                                                │            │
│                                     ┌──────────▼──────────┐ │
│                                     │   receive()         │ │
│                                     │   generator         │ │
│                                     │                     │ │
│                                     │   yield events      │ │
│                                     │   to user           │ │
│                                     └─────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Code Location:** `src/strands/experimental/bidi/agent/loop.py`

#### Model Connection

The Model Connection translates between SDK events and provider-specific protocols:

```
SDK Events                     Nova Sonic Protocol
────────────                   ───────────────────

BidiTextInputEvent    ──────►  contentStart + textInput + contentEnd
BidiAudioInputEvent   ──────►  contentStart + audioInput (streaming)

                      ◄──────  completionStart      → BidiResponseStartEvent
                      ◄──────  textOutput           → BidiTranscriptStreamEvent
                      ◄──────  audioOutput          → BidiAudioStreamEvent
                      ◄──────  toolUse              → ToolUseStreamEvent
                      ◄──────  completionEnd        → BidiResponseCompleteEvent
                      ◄──────  usageEvent           → BidiUsageEvent
```

**Code Location:** `src/strands/experimental/bidi/models/nova_sonic.py`

#### Tool Execution (Bidirectional)

Tool execution creates a feedback loop between model and agent:

```
                    Model Connection
                          │
                          │ toolUse event
                          ▼
              ┌───────────────────────┐
              │  ToolUseStreamEvent   │
              │  {name: "weather",    │
              │   input: {city: "NYC"}│
              │   toolUseId: "abc123"}│
              └───────────┬───────────┘
                          │
                          │ _run_tool() spawned
                          ▼
              ┌───────────────────────┐
              │   Tool Executor       │
              │                       │
              │   get_weather("NYC")  │
              │   returns "72F, Sunny"│
              └───────────┬───────────┘
                          │
                          │ ToolResultEvent created
                          ▼
              ┌───────────────────────┐
              │   ToolResultEvent     │
              │  {toolUseId: "abc123",│
              │   content: "72F..."}  │
              └───────────┬───────────┘
                          │
                          │ Sent back to model
                          ▼
                    Model Connection
                          │
                          │ Model incorporates result
                          │ and continues response
                          ▼
```

**Events in sequence:**
1. `ToolUseStreamEvent` - Model requests tool (Model → Agent)
2. `ToolResultMessageEvent` - Result added to messages (Internal)
3. `ToolResultEvent` - Result sent to model (Agent → Model)

**Code Location:** `src/strands/experimental/bidi/agent/loop.py` (lines 241-298)

---

### Layer 3: Output (Delivery)

#### Audio Output → Speakers

```
BidiAudioStreamEvent received
        │
        │ event["audio"] (base64 string)
        ▼
base64.b64decode()
        │
        │ PCM bytes
        ▼
_BidiAudioOutput._buffer
        │
        │ PyAudio callback reads from buffer
        ▼
    Speakers
```

**SDK Event:**
```python
BidiAudioStreamEvent(
    type="bidi_audio_stream",
    audio="<base64-encoded-pcm>",
    format="pcm",
    sample_rate=24000,
    channels=1,
)
```

**Code Location:** `src/strands/experimental/bidi/io/audio.py`

#### Text Output → Console/UI

```
BidiTranscriptStreamEvent received
        │
        │ event["text"], event["role"], event["is_final"]
        ▼
Application processes:
  - Print to console
  - Update UI
  - Save to transcript log
```

**SDK Event:**
```python
BidiTranscriptStreamEvent(
    type="bidi_transcript_stream",
    text="The weather in NYC is sunny!",
    role="assistant",
    is_final=True,
    delta={"text": "sunny!"},
    current_transcript="The weather in NYC is sunny!",
)
```

**Code Location:** `src/strands/experimental/bidi/types/events.py`

---

## Event Flow by Layer

### Complete Event Lifecycle

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           EVENT LIFECYCLE                                   │
│                                                                            │
│  LAYER 1: INPUT                                                            │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                            │
│    [Microphone]     [Keyboard]      [Camera]                               │
│         │               │               │                                  │
│         ▼               ▼               ▼                                  │
│  BidiAudioInput   BidiTextInput   BidiImageInput                          │
│  Event            Event           Event                                    │
│         │               │               │                                  │
│         └───────────────┼───────────────┘                                  │
│                         │                                                  │
│                         ▼                                                  │
│                  agent.send(event)                                         │
│                                                                            │
│  LAYER 2: PROCESSING                                                       │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                            │
│              ┌──────────────────────────────────────────────┐              │
│              │               _BidiAgentLoop                  │              │
│              │                                              │              │
│              │   send() ──► model.send() ──► Nova Sonic     │              │
│              │                                   │          │              │
│              │                                   ▼          │              │
│              │   Nova Events (contentStart, audioInput...)  │              │
│              │                                   │          │              │
│              │                                   ▼          │              │
│              │              ┌─────────────────────┐         │              │
│              │              │   MODEL PROCESSES   │         │              │
│              │              │   STT + LLM + TTS   │         │              │
│              │              └─────────────────────┘         │              │
│              │                                   │          │              │
│              │                                   ▼          │              │
│              │   Nova Events (textOutput, audioOutput...)   │              │
│              │                                   │          │              │
│              │                                   ▼          │              │
│              │   model.receive() ◄─── event translation     │              │
│              │         │                                    │              │
│              │         ▼                                    │              │
│              │   ┌──────────────────────────────────────┐   │              │
│              │   │  Event Processing in _run_model()    │   │              │
│              │   │                                      │   │              │
│              │   │  BidiTranscriptStreamEvent:          │   │              │
│              │   │    → append to messages (if final)   │   │              │
│              │   │    → queue for user                  │   │              │
│              │   │                                      │   │              │
│              │   │  ToolUseStreamEvent:                 │   │              │
│              │   │    → spawn _run_tool() task          │   │              │
│              │   │    → queue for user                  │   │              │
│              │   │                                      │   │              │
│              │   │  BidiInterruptionEvent:              │   │              │
│              │   │    → invoke hook callbacks           │   │              │
│              │   │    → queue for user                  │   │              │
│              │   │                                      │   │              │
│              │   │  All other events:                   │   │              │
│              │   │    → queue for user                  │   │              │
│              │   └──────────────────────────────────────┘   │              │
│              │                                   │          │              │
│              │                                   ▼          │              │
│              │                           _event_queue       │              │
│              │                                   │          │              │
│              └───────────────────────────────────┼──────────┘              │
│                                                  │                         │
│                                                  ▼                         │
│                                     agent.receive() yields                 │
│                                                                            │
│  LAYER 3: OUTPUT                                                           │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                            │
│                 ┌─────────────────┬─────────────────┐                      │
│                 │                 │                 │                      │
│                 ▼                 ▼                 ▼                      │
│    BidiAudioStreamEvent  BidiTranscript   BidiResponse                    │
│                          StreamEvent      CompleteEvent                    │
│                 │                 │                 │                      │
│                 ▼                 ▼                 ▼                      │
│          [Speakers]       [Console/UI]      [App Logic]                   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Mapping Reference

### Input Events (User → Agent → Model)

| Diagram Box | SDK Event | Fields | Protocol Translation |
|-------------|-----------|--------|---------------------|
| Microphone | (Hardware) | - | - |
| Audio Input | `BidiAudioInputEvent` | `audio`, `format`, `sample_rate`, `channels` | Nova: `contentStart` + `audioInput` |
| Text Input | `BidiTextInputEvent` | `text`, `role` | Nova: `contentStart` + `textInput` + `contentEnd` |
| Image Input | `BidiImageInputEvent` | `image`, `mime_type` | Nova: `contentStart` + `imageInput` + `contentEnd` |

### Processing Events (Internal)

| Diagram Box | SDK Component | Role | Key Methods |
|-------------|---------------|------|-------------|
| Agent Loop | `_BidiAgentLoop` | Event orchestration | `send()`, `receive()`, `_run_model()` |
| Model Connection | `BidiNovaSonicModel` | Protocol translation | `send()`, `receive()`, `_convert_nova_event()` |
| Tool Execution | `_run_tool()` task | Tool invocation | Via `ToolExecutor._stream()` |

### Output Events (Model → Agent → User)

| Diagram Box | SDK Event | Fields | Nova Source |
|-------------|-----------|--------|-------------|
| Audio Output | `BidiAudioStreamEvent` | `audio`, `format`, `sample_rate`, `channels` | `audioOutput` |
| Text Output | `BidiTranscriptStreamEvent` | `text`, `role`, `is_final`, `delta` | `textOutput` |
| Response Start | `BidiResponseStartEvent` | `response_id` | `completionStart` |
| Response End | `BidiResponseCompleteEvent` | `response_id`, `stop_reason` | `completionEnd` |
| Usage | `BidiUsageEvent` | `input_tokens`, `output_tokens` | `usageEvent` |
| Interruption | `BidiInterruptionEvent` | `reason` | `stopReason=INTERRUPTED` |
| Tool Request | `ToolUseStreamEvent` | `current_tool_use` | `toolUse` |

### Lifecycle Events

| Event | Trigger | Purpose |
|-------|---------|---------|
| `BidiConnectionStartEvent` | `model.receive()` starts | Connection established |
| `BidiConnectionRestartEvent` | 8-min timeout | Transparent reconnection |
| `BidiConnectionCloseEvent` | `stop_conversation` tool or error | Session ended |
| `BidiErrorEvent` | Exception during processing | Error notification |

---

## Summary

Your architecture diagram accurately represents the three-layer event flow in the Strands Bidi Agent:

1. **User Layer**: Input devices generate `BidiInputEvent` types (audio, text, image)
2. **Agent Layer**: `_BidiAgentLoop` orchestrates bidirectional flow, with `BidiModel` translating between SDK events and provider protocols
3. **Output Layer**: `BidiOutputEvent` types (audio, transcript, etc.) delivered to speakers and UI

The **Tool Execution** bidirectional arrow represents the `ToolUseStreamEvent` → `ToolResultEvent` cycle where the model can request actions and receive results.

For complete event flow examples with code, see [BIDI_EVENT_FLOW.md](./BIDI_EVENT_FLOW.md).
For architecture overview, see [BIDI_ARCHITECTURE.md](./BIDI_ARCHITECTURE.md).
