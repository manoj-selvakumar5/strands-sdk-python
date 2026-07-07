# Strands SDK Timeline

A comprehensive timeline of the Strands Agents SDK evolution from initial release to current version.

**Total Releases:** 37 versions (v0.1.0 to v1.18.0)
**Current Version:** v1.18.0 (December 2025)
**Status:** Production/Stable

---

## Pre-1.0 Era: Foundation

### v0.1.0 - v0.1.9 | Initial Foundation
The foundational releases establishing the core agent framework.

| Version | Key Features |
|---------|--------------|
| v0.1.0 | Core agent framework, event-driven agent loop |
| v0.1.1-v0.1.3 | Early stability improvements |
| v0.1.4 | Initial release milestones |
| v0.1.8 | Relaxed docstring_parser dependency |
| v0.1.9 | `@tool` decorator returns AgentTool that also acts as a function |

**Capabilities Introduced:**
- Basic tool system with `@tool` decorator
- Amazon Bedrock as default model provider
- Event-driven agent loop architecture
- Simple API: `Agent("prompt")`

---

### v0.2.0 - v0.2.1 | Executor Framework
Introduction of the tool execution framework.

| Version | Key Features |
|---------|--------------|
| v0.2.0 | Executor framework with yield-based tool execution |
| v0.2.1 | Tool parallel execution with sleep handling |

**Capabilities Introduced:**
- Sequential and concurrent tool executors
- Async generator tools support

---

### v0.3.0 | Breaking Changes
Stabilization release with breaking changes.

| Version | Key Features |
|---------|--------------|
| v0.3.0 | Set `load_tools_from_directory` to default False |

---

## v1.0.0 Era: Production Release (October 2025)

### v1.0.0 | Official Production Release
The milestone release marking the SDK as production-ready.

| Version | Key Features |
|---------|--------------|
| v1.0.0 | Removed "preview" designation, stable API contract |
| v1.0.1 | Telemetry fix: Proper trace grouping for agent-as-tool |

**Capabilities Introduced:**
- Production-ready stability
- Session management foundations
- Multi-agent basics

---

## v1.1.x - v1.5.x Era: Core Features

### v1.1.0 | Agent Tracing
| Version | Key Features |
|---------|--------------|
| v1.1.0 | Include agent trace into tool for nested agent execution |

---

### v1.2.0 | MCP Enhancements
| Version | Key Features |
|---------|--------------|
| v1.2.0 | Add `list_prompts`, `get_prompt` methods for MCP |

**Capabilities Introduced:**
- Extended Model Context Protocol (MCP) client capabilities

---

### v1.3.0 | Error Handling
| Version | Key Features |
|---------|--------------|
| v1.3.0 | Dedicated `MaxTokensReachedException` for max token encounters |

**Capabilities Introduced:**
- Better event loop error handling
- Typed exceptions for error recovery

---

### v1.4.0 | Structured Output
| Version | Key Features |
|---------|--------------|
| v1.4.0 | Prevent `conversation_history` modification when prompt is passed |

**Capabilities Introduced:**
- Structured output stability improvements

---

### v1.5.0 | Cost Tracking
| Version | Key Features |
|---------|--------------|
| v1.5.0 | Cached token metrics support for Amazon Bedrock |

**Capabilities Introduced:**
- Token usage tracking for cost monitoring
- Cache read/write metrics

---

## v1.6.x - v1.9.x Era: Platform Expansion

### v1.6.0 | API Restructuring
| Version | Key Features |
|---------|--------------|
| v1.6.0 | Move `AgentInput` to types submodule |

---

### v1.7.0 - v1.7.1 | Tool Loading
| Version | Key Features |
|---------|--------------|
| v1.7.0 | Fix: Load tools with same tool name |
| v1.7.1 | Only add signature to reasoning blocks if signature provided |

**Capabilities Introduced:**
- Better tool name collision handling
- Reasoning content handling improvements

---

### v1.8.0 | Local Inference
| Version | Key Features |
|---------|--------------|
| v1.8.0 | llama.cpp model provider, ToolChoice validation |

**Capabilities Introduced:**
- Local inference capabilities via llama.cpp
- Model config validation

---

### v1.9.0 - v1.9.1 | Provider Documentation
| Version | Key Features |
|---------|--------------|
| v1.9.0 | Documentation improvements across all providers |
| v1.9.1 | Tool choice parameter handling fix |

---

## v1.10.x - v1.18.x Era: Enterprise Features (November-December 2025)

### v1.10.0 | Multi-Agent Hooks
| Version | Key Features |
|---------|--------------|
| v1.10.0 | New `BaseHookEvent` for multiagent use |

**Capabilities Introduced:**
- Hook event inheritance system
- Cross-agent coordination via hooks

---

### v1.11.0 | Error Mapping
| Version | Key Features |
|---------|--------------|
| v1.11.0 | Map LiteLLM context-window errors to `ContextWindowOverflowException` |

**Capabilities Introduced:**
- Standardized error handling across providers

---

### v1.12.0 | SageMaker Fixes
| Version | Key Features |
|---------|--------------|
| v1.12.0 | Fix `additional_args` passing in `SageMakerAIModel` |

---

### v1.13.0 | Interrupts
| Version | Key Features |
|---------|--------------|
| v1.13.0 | Interrupts in decorated tools: `@tool(interrupt=True)` |

**Capabilities Introduced:**
- Human-in-the-loop capabilities
- Tool execution interruption

---

### v1.14.0 | Tool Validation
| Version | Key Features |
|---------|--------------|
| v1.14.0 | Transform invalid tool usages on sending |

**Capabilities Introduced:**
- Prevent session poisoning from malformed tool names

---

### v1.15.0 | Prompt Caching
| Version | Key Features |
|---------|--------------|
| v1.15.0 | `SystemContentBlock` prompt caching (provider-agnostic) |

**Capabilities Introduced:**
- Significant cost reduction and latency improvements
- Provider-agnostic caching mechanism

---

### v1.16.0 | Async Hooks & Enhanced Tooling
| Version | Key Features |
|---------|--------------|
| v1.16.0 | Async hooks, SystemContentBlocks in LiteLLM, string descriptions in Annotated parameters |

**Capabilities Introduced:**
- Async hook support for non-blocking event handling
- Tool definitions in traces via semconv opt-in
- Shared interrupt state and thread context
- Handle "prompt is too long" from Anthropic
- Gemini non-JSON error message handling

---

### v1.17.0 | MCP Timeout & Swarm Improvements
| Version | Key Features |
|---------|--------------|
| v1.17.0 | MCPAgentTool timeout configuration, Swarm handoff improvements |

**Capabilities Introduced:**
- Allow setting timeout when creating MCPAgentTool
- Swarm: Switch to handoff node only after current node stops
- A2A: Base64 decode byte data for ContentBlocks
- LiteLLM stream parameter validation

---

### v1.18.0 | Multi-Agent Interrupts (Current)
| Version | Key Features |
|---------|--------------|
| v1.18.0 | Interruptible multi-agent hook interface, verbose PrintingCallbackHandler |

**Capabilities Introduced:**
- Interruptible multi-agent hook interface
- Optional verbose output for PrintingCallbackHandler
- Multi-agent input improvements
- Security: Prevent tool name and sys modules collisions in tool_loader
- MCP connection protection on non-fatal timeout errors
- LiteLLM cacheWriteInputTokens fix

---

## Current Capabilities Summary (v1.18.0)

| Category | Features |
|----------|----------|
| **Model Providers** | 12+ providers: Amazon Bedrock, Anthropic, OpenAI, Google Gemini, Ollama, llama.cpp, LiteLLM, AWS SageMaker, Mistral AI, Writer, Cohere, LlamaAPI |
| **Multi-Agent** | Swarm & Graph orchestrators with session persistence, lazy initialization, async streaming |
| **A2A Protocol** | Agent-to-Agent communication, AgentCard publishing, skills auto-discovery |
| **MCP Integration** | Full Model Context Protocol support, 1000s of pre-built tools, tool elicitation |
| **Tool System** | @tool decorator, interrupts, parallel execution, invalid name handling, hot reload |
| **Session Persistence** | FileSessionManager, S3SessionManager, RepositorySessionManager |
| **Prompt Caching** | Provider-agnostic SystemContentBlock caching for cost optimization |
| **Guardrails** | Amazon Bedrock content filtering, PII detection (30+ entity types), topic/word policies |
| **Structured Output** | Pydantic model validation, automatic retry on validation failures |
| **Observability** | OpenTelemetry v1.37 semantic conventions, distributed tracing, token metrics |
| **Streaming** | Synchronous, asynchronous, and streaming invocation patterns |
| **Conversation Management** | SlidingWindow, Summarizing, and Null conversation managers |

---

## Version Distribution

```
Pre-1.0:     v0.1.0 ──────────────────────────────────► v0.3.0
             │ Foundation │ Executors │ Breaking │

v1.0.x:      v1.0.0 ────► v1.0.1
             │ Production Release │

v1.1-1.5:    v1.1.0 ─► v1.2.0 ─► v1.3.0 ─► v1.4.0 ─► v1.5.0
             │Trace│ │ MCP │ │Error│ │Struct│ │Cost│

v1.6-1.9:    v1.6.0 ─► v1.7.x ─► v1.8.0 ─► v1.9.x
             │ API │ │Tools│ │llama│ │Docs│

v1.10-1.18:  v1.10.0 ─► v1.11.0 ─► v1.12.0 ─► v1.13.0 ─► v1.14.0 ─► v1.15.0 ─► v1.16.0 ─► v1.17.0 ─► v1.18.0
             │Hooks│  │Error│   │Sage│   │Interrupt│ │Valid│  │Cache│  │Async│   │MCP│    │Multi│
```

---

*Last updated: December 2025*
