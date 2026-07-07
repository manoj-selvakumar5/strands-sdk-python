# SDK Architecture Map

**Date:** 2026-01-31
**Context:** SDK Fundamentals - Learning Guide
**Source:** `src/strands/`

---

## 1. Directory Structure

```
src/strands/
├── agent/              -- Agent class, AgentResult, conversation managers
├── event_loop/         -- Core reasoning loop (model -> tools -> recurse)
├── models/             -- Model provider adapters (Bedrock, OpenAI, etc.)
├── tools/              -- Tool system (@tool, registry, executors)
├── hooks/              -- Lifecycle event system
├── types/              -- Type definitions (Message, ContentBlock, etc.)
├── telemetry/          -- Observability (metrics, tracing)
├── session/            -- Session persistence (save/restore)
├── multiagent/         -- Multi-agent patterns (Graph, Swarm)
├── handlers/           -- Callback handlers (legacy)
├── experimental/       -- Experimental features (BIDI streaming, steering)
├── interrupt.py        -- Human-in-the-loop interrupt system
└── __init__.py         -- Public exports
```

### agent/

The entry point for most users. Contains the core `Agent` class and everything directly attached to it.

| File | Key Classes | What It Does |
|---|---|---|
| `agent.py` | `Agent` | Main agent orchestrator. Receives input, calls model, runs tools, returns results. |
| `base.py` | `AgentBase` | Abstract base class defining the agent interface. |
| `agent_result.py` | `AgentResult` | Return value from agent invocations (message, stop_reason, metrics, state). |
| `state.py` | `AgentState` | Internal agent state management. |
| `a2a_agent.py` | `A2AAgent` | Agent-to-Agent protocol implementation. |
| `conversation_manager/` | `SlidingWindowConversationManager`, `SummarizingConversationManager`, `NullConversationManager` | Strategies for managing conversation history length. |

**When you'd look here:** Creating an agent, understanding the agent lifecycle, customizing conversation management, investigating how `agent()` calls work.

### event_loop/

The heart of the SDK. This is where the "think -> act -> observe -> repeat" loop lives.

| File | Key Functions/Classes | What It Does |
|---|---|---|
| `event_loop.py` | `event_loop_cycle()` | Core async loop: call model, process response, execute tools, recurse. |
| `streaming.py` | `stream_messages()` | Handles streaming model responses chunk by chunk. |
| `_retry.py` | `ModelRetryStrategy` | Configurable retry logic for model calls (exponential backoff). |
| `_recover_message_on_max_tokens_reached.py` | `recover_message_on_max_tokens_reached()` | Recovers partial messages when the model hits token limits. |

**When you'd look here:** Debugging the agent loop, understanding how tool results flow back to the model, investigating retry behavior, understanding streaming.

### models/

Model provider adapters. Each file adapts a specific LLM provider to the SDK's common `Model` interface.

| File | Key Classes | Provider |
|---|---|---|
| `model.py` | `Model` (abstract) | Base interface all providers implement |
| `bedrock.py` | `BedrockModel` | Amazon Bedrock (default) |
| `anthropic.py` | `AnthropicModel` | Anthropic API direct |
| `openai.py` | `OpenAIModel` | OpenAI / Azure OpenAI |
| `litellm.py` | `LiteLLMModel` | LiteLLM (multi-provider proxy) |
| `ollama.py` | `OllamaModel` | Ollama (local models) |
| `llamaapi.py` | `LlamaAPIModel` | LlamaAPI |
| `llamacpp.py` | `LlamaCppModel` | llama.cpp (local) |
| `mistral.py` | `MistralModel` | Mistral AI |
| `gemini.py` | `GeminiModel` | Google Gemini |
| `sagemaker.py` | `SageMakerModel` | Amazon SageMaker endpoints |
| `writer.py` | `WriterModel` | Writer AI |
| `_validation.py` | -- | Shared validation utilities |

**When you'd look here:** Configuring a specific model provider, understanding how model responses are parsed, adding support for a new provider.

### tools/

Everything related to the tool system.

| File/Dir | Key Classes | What It Does |
|---|---|---|
| `decorator.py` | `@tool`, `DecoratedFunctionTool`, `FunctionToolMetadata` | The `@tool` decorator and function-to-tool conversion. |
| `registry.py` | `ToolRegistry` | Central dict of `{name: AgentTool}`. Registration, discovery, validation. |
| `tools.py` | `PythonAgentTool`, `normalize_tool_spec()` | Module-based tool implementation and spec normalization. |
| `tool_provider.py` | `ToolProvider` | Abstract base for tool providers (e.g., MCP). |
| `executors/` | `ConcurrentToolExecutor`, `SequentialToolExecutor` | Execution strategies for tool calls. |
| `mcp/` | MCP tool integration | Model Context Protocol tool server/client support. |
| `structured_output/` | Structured output tooling | Forces model output into Pydantic schemas. |
| `_caller.py` | `_ToolCaller` | Internal tool calling logic. |
| `_validator.py` | -- | Tool input validation. |
| `loader.py` | `ToolLoader` | Loading tools from files and modules. |
| `watcher.py` | `ToolWatcher` | Hot-reload watcher for tool file changes. |

**When you'd look here:** Creating tools, understanding how tools are registered, debugging tool execution, working with MCP tools, understanding structured output.

### hooks/

The lifecycle event and callback system.

| File | Key Classes | What It Does |
|---|---|---|
| `registry.py` | `HookRegistry`, `HookProvider`, `HookCallback`, `BaseHookEvent`, `HookEvent` | Core registry that stores and dispatches callbacks. |
| `events.py` | `AgentInitializedEvent`, `BeforeInvocationEvent`, `AfterInvocationEvent`, `BeforeModelCallEvent`, `AfterModelCallEvent`, `BeforeToolCallEvent`, `AfterToolCallEvent`, `MessageAddedEvent` | All hook event types with their fields. |

**When you'd look here:** Building custom hooks, understanding the agent lifecycle, implementing logging/metrics/guardrails.

### types/

All TypedDict and type definitions used across the SDK.

| File | Key Types | What It Defines |
|---|---|---|
| `content.py` | `Message`, `ContentBlock`, `Role`, `Messages` | Core message and content types. |
| `tools.py` | `ToolSpec`, `ToolUse`, `ToolResult`, `ToolContext`, `AgentTool` | Tool-related types. |
| `streaming.py` | `StopReason` | Model stop reasons (end_turn, tool_use, max_tokens). |
| `exceptions.py` | `ContextWindowOverflowException`, `EventLoopException`, etc. | SDK exception types. |
| `media.py` | `ImageContent`, `DocumentContent`, `VideoContent` | Media content types. |
| `interrupt.py` | `Interrupt`, `_Interruptible` | Interrupt types for human-in-the-loop. |
| `_events.py` | `TypedEvent`, `ToolResultEvent`, `ToolStreamEvent`, etc. | Internal event types for the event loop. |
| `agent.py` | `AgentInput` | Input types for agent invocation. |
| `session.py` | -- | Session-related types. |
| `multiagent.py` | -- | Multi-agent types. |
| `a2a.py` | -- | Agent-to-Agent protocol types. |
| `guardrails.py` | -- | Guardrail types. |

**When you'd look here:** Understanding data structures, type checking, finding the definition of a specific type.

### telemetry/

Observability: metrics, tracing, and instrumentation.

| File | Key Classes | What It Does |
|---|---|---|
| `metrics.py` | `EventLoopMetrics`, `Trace` | Metrics collection for agent operations. |
| `tracer.py` | `Tracer`, `get_tracer()` | OpenTelemetry tracer integration. |
| `config.py` | -- | Telemetry configuration. |
| `metrics_constants.py` | -- | Metric name constants. |

**When you'd look here:** Setting up observability, understanding what metrics are collected, integrating with monitoring systems.

### session/

Session persistence -- save and restore agent state across invocations.

| File | Key Classes | What It Does |
|---|---|---|
| `session_manager.py` | `SessionManager` | Base session management interface. |
| `file_session_manager.py` | `FileSessionManager` | Save/load sessions to local files. |
| `s3_session_manager.py` | `S3SessionManager` | Save/load sessions to Amazon S3. |
| `repository_session_manager.py` | `RepositorySessionManager` | Save/load via custom repository backend. |
| `session_repository.py` | `SessionRepository` | Abstract repository interface. |

**When you'd look here:** Persisting conversations, resuming agent sessions, building custom storage backends.

### multiagent/

Multi-agent orchestration patterns.

| File | Key Classes | What It Does |
|---|---|---|
| `base.py` | `MultiAgentBase` | Base class for multi-agent orchestrators. |
| `graph.py` | `GraphAgent` | DAG-based agent orchestration (nodes with edges). |
| `swarm.py` | `SwarmAgent` | Swarm pattern (agents hand off to each other). |
| `a2a/` | -- | Agent-to-Agent protocol implementation. |

**When you'd look here:** Building multi-agent systems, understanding orchestration patterns, implementing custom agent flows.

### experimental/

Features that are not yet stable. APIs may change.

| Dir | What It Contains |
|---|---|
| `bidi/` | Bidirectional streaming (real-time audio conversations). |
| `hooks/` | Experimental hook extensions. |
| `steering/` | Agent steering / behavioral control. |
| `tools/` | Experimental tool features. |
| `agent_config.py` | Experimental agent configuration. |

**When you'd look here:** Cutting-edge features, real-time audio, experimental APIs.

### Other Top-Level Files

| File | What It Does |
|---|---|
| `__init__.py` | Public exports: `Agent`, `tool`, `ToolContext`, `ModelRetryStrategy` |
| `interrupt.py` | `Interrupt`, `InterruptException` -- human-in-the-loop system |
| `_async.py` | Async utility for running coroutines |
| `_identifier.py` | Agent identification utilities |
| `_exception_notes.py` | Exception note helpers |
| `handlers/` | Legacy callback handler system (being replaced by hooks) |

---

## 2. Dependency Graph

Here is how the major components depend on each other:

```
                        ┌─────────┐
                        │  Agent  │
                        └────┬────┘
                             │
              ┌──────────────┼──────────────────┐
              │              │                  │
              v              v                  v
    ┌──────────────┐  ┌────────────┐  ┌──────────────────┐
    │ ToolRegistry │  │   Model    │  │   HookRegistry   │
    │  {name:Tool} │  │ (provider) │  │  {event:[cbs]}   │
    └──────┬───────┘  └─────┬──────┘  └────────┬─────────┘
           │                │                   │
           │         ┌──────┴──────┐            │
           │         │  EventLoop  │◄───────────┘
           │         │  (cycle)    │
           │         └──────┬──────┘
           │                │
           v                v
    ┌──────────────┐  ┌────────────┐
    │ ToolExecutor │  │  Messages  │
    │ (concurrent/ │  │  (list of  │
    │  sequential) │  │  Message)  │
    └──────────────┘  └────────────┘
                             ^
                             │
                    ┌────────┴────────┐
                    │ Conversation    │
                    │ Manager         │
                    └─────────────────┘
```

**Reading the graph:**
- `Agent` owns a `ToolRegistry`, a `Model`, and a `HookRegistry`
- `Agent` also owns a `ConversationManager` and a `Messages` list
- The `EventLoop` is the core loop that uses the `Model` to generate responses, the `ToolExecutor` to run tools, and the `HookRegistry` to fire events
- Everything produces and consumes `Messages` -- they are the common currency
- The `ConversationManager` operates on `Messages` to keep them within limits

---

## 3. Public API -- What You Actually Import

For most users, you only need a handful of imports:

### Core (always needed)

```python
from strands import Agent, tool
```

- `Agent` -- the main agent class
- `tool` -- the `@tool` decorator

### Model Providers (pick one)

```python
from strands.models.bedrock import BedrockModel     # Amazon Bedrock (default)
from strands.models.anthropic import AnthropicModel  # Anthropic direct
from strands.models.openai import OpenAIModel        # OpenAI / Azure
from strands.models.ollama import OllamaModel        # Ollama (local)
from strands.models.litellm import LiteLLMModel      # LiteLLM (multi-provider)
```

### Tool Context (when tools need agent access)

```python
from strands.types.tools import ToolContext
```

### Hooks (for lifecycle customization)

```python
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import (
    AgentInitializedEvent,
    BeforeInvocationEvent,
    AfterInvocationEvent,
    BeforeModelCallEvent,
    AfterModelCallEvent,
    BeforeToolCallEvent,
    AfterToolCallEvent,
    MessageAddedEvent,
)
```

### Conversation Management (if customizing)

```python
from strands.agent.conversation_manager import (
    SlidingWindowConversationManager,
    SummarizingConversationManager,
    NullConversationManager,
)
```

### Tool Executors (if customizing)

```python
from strands.tools.executors import ConcurrentToolExecutor, SequentialToolExecutor
```

### Sessions (if persisting state)

```python
from strands.session import FileSessionManager, S3SessionManager
```

### Multi-Agent (for orchestration)

```python
from strands.multiagent.graph import GraphAgent
from strands.multiagent.swarm import SwarmAgent
```

### Retry Strategy (if customizing)

```python
from strands import ModelRetryStrategy
```

---

## 4. Where to Go Next

Now that you understand the core architecture, here are the advanced topics and where to find them:

| Topic | What It Is | Where to Look |
|---|---|---|
| **Multi-Agent (Graph)** | DAG-based orchestration with nodes and edges | `src/strands/multiagent/graph.py` |
| **Multi-Agent (Swarm)** | Agent handoff pattern | `src/strands/multiagent/swarm.py` |
| **Sessions** | Save/restore agent state | `src/strands/session/` |
| **Observability** | Metrics, tracing, OpenTelemetry | `src/strands/telemetry/` |
| **BIDI Streaming** | Real-time audio conversations | `src/strands/experimental/bidi/` |
| **Interrupts** | Human-in-the-loop (pause/resume) | `src/strands/interrupt.py`, `src/strands/types/interrupt.py` |
| **MCP Tools** | Model Context Protocol tool servers | `src/strands/tools/mcp/` |
| **Structured Output** | Force model output into Pydantic schemas | `src/strands/tools/structured_output/` |
| **Agent-to-Agent (A2A)** | Inter-agent communication protocol | `src/strands/multiagent/a2a/`, `src/strands/agent/a2a_agent.py` |
| **Guardrails** | Content safety and filtering | `src/strands/types/guardrails.py` |

### Cross-References to Other Guides in This Series

- **Tools deep dive:** `04-tools.md` -- @tool decorator, ToolSpec, ToolUse, ToolResult, ToolContext, executors
- **Hooks deep dive:** `05-hooks.md` -- All hook events, HookProvider pattern, practical examples
- **Messages deep dive:** `06-messages-and-conversation.md` -- ContentBlock types, conversation flow, management strategies

---

## Quick Reference Card

```
# Minimal agent
from strands import Agent, tool

@tool
def my_tool(x: str) -> str:
    """Does something."""
    return x.upper()

agent = Agent(tools=[my_tool])
result = agent("Process this")
print(result)

# Key objects
agent.messages          # Conversation history (list of Message dicts)
agent.system_prompt     # System prompt (str)
agent.tool_registry     # ToolRegistry (dict-like, {name: AgentTool})
agent.tool_names        # List of registered tool names

# Agent result
result = agent("hello")
result.message          # Final assistant message
result.stop_reason      # Why the model stopped ("end_turn", "tool_use", etc.)
result.metrics          # EventLoopMetrics
result.state            # AgentState
str(result)             # Extracts text from the final message
```

**Key source files for the entire SDK:**
- `src/strands/__init__.py` -- Public API surface
- `src/strands/agent/agent.py` -- `Agent` class
- `src/strands/event_loop/event_loop.py` -- Core reasoning loop
- `src/strands/tools/decorator.py` -- `@tool` decorator
- `src/strands/tools/registry.py` -- `ToolRegistry`
- `src/strands/hooks/events.py` -- Hook event types
- `src/strands/hooks/registry.py` -- `HookRegistry`
- `src/strands/types/content.py` -- `Message`, `ContentBlock`
- `src/strands/types/tools.py` -- `ToolSpec`, `ToolUse`, `ToolResult`, `ToolContext`
