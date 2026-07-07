# BIDI Voice Assistants - Blog Research

**Date:** 2026-02-04
**Status:** Research complete, ready to write

## Title Ideas

- "Building Real-Time Voice Assistants with Strands BIDI"
- "From Text to Voice: Adding Audio Streaming to Your Agents"
- "Interruption Handling in AI Conversations: The BIDI Approach"

## Why This Blog?

- Zero external coverage of BIDI feature
- High demand for voice assistant tutorials
- Showcases SDK differentiation from competitors
- Experimental but mature implementation

## Key Code Locations

```
src/strands/experimental/bidi/
├── bidi_agent.py          # Main BidiAgent class
├── agent_loop.py          # _BidiAgentLoop event processing
├── models/
│   ├── nova_sonic.py      # Amazon Nova Sonic (HTTP/2)
│   ├── openai_realtime.py # OpenAI Realtime (WebSocket)
│   └── gemini_live.py     # Gemini Live (WebSocket)
└── events.py              # All BIDI event types
```

## Blog Outline

### 1. Introduction: Why BIDI?
- Traditional agents: request/response overhead
- BIDI: persistent connection, sub-second latency
- Use cases: voice assistants, live chat, interactive apps

### 2. Setup: BidiAgent + Provider

```python
from strands.experimental.bidi import BidiAgent
from strands.experimental.bidi.models import BidiNovaSonicModel

async with BidiAgent(model=BidiNovaSonicModel(), tools=[calculator]) as agent:
    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output()],
        invocation_state={"user_id": "123"}
    )
```

### 3. Audio Configuration
- Formats: PCM, WAV, Opus, MP3
- Sample rates: 16kHz, 24kHz, 48kHz
- Base64 encoding for JSON transport
- Input/output channel configuration

### 4. Interruption Handling
- `BidiInterruptionEvent` for detecting user interrupts
- Graceful conversation flow
- `stop_conversation` built-in tool
- UX patterns for voice apps

### 5. Tool Execution During Streaming
- Concurrent execution with `_TaskPool`
- Tools run parallel to model responses
- Message lock ensures history consistency
- `invocation_state` for passing context to tools

### 6. Connection Recovery
- 8-minute Nova Sonic timeout
- `BidiModelTimeoutError` with `restart_config`
- `BidiBeforeConnectionRestartEvent` / `AfterConnectionRestartEvent`
- Message history preserved across restarts

### 7. Multi-Modal Support
- `BidiTextInputEvent` - text messages
- `BidiAudioInputEvent` - audio streams
- `BidiImageInputEvent` - image data
- Mixed modality in single conversation

### 8. Provider Comparison

| Provider | Transport | Best For |
|----------|-----------|----------|
| Nova Sonic | HTTP/2 event streams | AWS ecosystem |
| OpenAI Realtime | WebSocket | Cross-platform |
| Gemini Live | WebSocket | Google ecosystem |

### 9. When to Use BIDI vs Traditional

| Criteria | Traditional | BIDI |
|----------|-------------|------|
| Latency needs | Tolerant | Sub-second |
| Connection type | Per-request | Persistent |
| Audio support | No | Yes |
| Python version | 3.10+ | 3.12+ |

## Unique Angles

1. **Voice assistant tutorial** - step-by-step with working code
2. **Interruption UX** - patterns for natural conversations
3. **Provider comparison** - practical selection guide
4. **Production resilience** - timeout handling, recovery

## Code Examples Needed

- [ ] Basic voice assistant setup
- [ ] Interruption handling demo
- [ ] Multi-modal conversation
- [ ] Tool execution during streaming
- [ ] Connection recovery pattern

## References

- `docs/bidi/ARCHITECTURE.md` - internal architecture
- `docs/bidi/DIAGRAM_EVENTS.md` - event flow diagrams
- `docs/bidi/EVENT_FLOW.md` - detailed event lifecycle
