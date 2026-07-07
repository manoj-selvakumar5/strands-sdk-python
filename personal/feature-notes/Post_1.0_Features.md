# Strands Agents SDK: Features Added After Version 1.0

## Executive Summary

**Version 1.0 Release Date**: July 15, 2025

**Current Version**: v1.18.0 (as of November 22, 2025)

**Timeline**: Approximately 4 months of active development post-1.0

**Total Commits After 1.0**: 212 commits across 18 minor version releases

**Blog Post Reference**: [Introducing Strands Agents 1.0](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-1-0-production-ready-multi-agent-orchestration-made-simple/)

---

## Core Features Added After 1.0 (Organized by Category)

### 1. PROTOCOL INTEGRATION

#### A2A (Agent-to-Agent) Protocol - August 2025
The A2A protocol enables standardized agent discovery and communication:

- **FileParts and DataParts support** (#596) - Enhanced multimodal data handling including images, videos, documents, and structured JSON data
- **Tools as skills** (#287) - Automatic conversion of tools into discoverable skills for other agents
- **Containerized deployment support** (#524) - Docker/Kubernetes compatibility with volume mounts and load balancer integration
- **Configurable request handler** (#601) - Custom task stores, queue managers, and push notification support
- **A2AServer** - Wraps Strands agents with HTTP service (FastAPI/Starlette) and publishes AgentCard for discovery
- **StrandsA2AExecutor** - Converts between A2A protocol messages and Strands ContentBlocks
- **Streaming responses** - Real-time A2A streaming support

#### MCP (Model Context Protocol) Enhancements - August-October 2025
Building on pre-1.0 MCP support with significant improvements:

- **MCP async call tool** (#406, August 2025) - Asynchronous tool execution for concurrent operations
- **List prompts and get prompt methods** (#160, August 2025) - Enhanced prompt management capabilities
- **Pagination for list_tools_sync** (#436, August 2025) - Improved handling of large tool sets
- **MCP Client configuration** (#657, August 2025) - Server initialization timeout options
- **Structured content retention** (#528, August 2025) - Preserve structured content in AgentTool responses
- **MCP timeout issue fixes** (#922, October 2025) - More reliable connections
- **Idempotent instrumentation** (#892, October 2025) - Prevent recursion errors
- **MCP ToolProvider integration** (#895, October 2025) - Experimental agent-managed MCP connections via ToolProvider interface
- **MCP elicitation support** (#1094, October 2025) - Dynamic tool discovery capabilities
- **MCPAgentTool timeout configuration** (#1184, November 2025) - Allow setting timeout when creating MCPAgentTool for better control
- **MCP 5xx error handling** (#1169, November 2025) - Don't hang when MCP server returns 5xx errors
- **MCP connection protection** (#1231, November 2025) - Protect connection on non-fatal client side timeout errors

### 2. MULTI-AGENT ORCHESTRATION ENHANCEMENTS

#### Swarm Orchestrator - August-November 2025
- **Session persistence for Swarm** (#1110, #1071, November 2025) - Full session persistence enabling multi-agent conversations to be saved and resumed
- **Stream_async for Swarm** (#961, October 2025) - Async streaming support with comprehensive event system
- **Configurable entry point** (#851, September 2025) - Flexible agent workflow initialization
- **Swarm initialization optimization** (#1107, October 2025) - Lazy initialization - only initialize agents when actually invoked for better resource management
- **Swarm handoff improvements** (#1147, November 2025) - Switch to handoff node only after current node stops for smoother transitions

#### Graph Orchestrator - August-October 2025
- **Session persistence for Graph** (#1110, #1071, November 2025) - Full session persistence with repository pattern management
- **Stream_async for Graph** (#961, October 2025) - Async streaming support with BeforeMultiAgentInvokeEvent and AfterMultiAgentInvokeEvent
- **Cyclic graph support** (#497, August 2025) - Allow feedback loops in multi-agent workflows

#### Multi-Agent Infrastructure
- **Multiagent hooks and serialization** (#1070, October 2025) - Hook event support for multi-agent systems with serialize/deserialize functions for AgentResult
- **MultiAgent HookEvent base class** (#925, September 2025) - New base class for better event inheritance
- **Multi-agent input handling** (#1196, November 2025) - Enhanced input handling for multi-agent systems
- **Shared thread context** (#1146, November 2025) - Share thread context across multi-agent operations for better coordination

### 3. HOOKS & EVENTS SYSTEM

#### Stable Hooks API - September 2025
- **Stable hooks API** (#926) - ModelCall and ToolCall events marked as non-experimental with improved naming:
  - BeforeModelCallEvent
  - AfterModelCallEvent
  - BeforeToolCallEvent
  - AfterToolCallEvent
- **Tool call cancellation** (#964, October 2025) - Before tool call event can now cancel tool execution for better control flow
- **Async hooks** (#1119, November 2025) - Support for asynchronous hook execution enabling non-blocking hook operations

#### Typed Events System - July-August 2025
- **Core typed hooks & callbacks** (#304, July 2025) - Fundamental system for extensible agent behavior
- **TypedEvent inheritance** (#755, #745, August 2025) - Robust callback behavior and event handling
- **Message append hooks** (#385, July 2025) - Hooks triggered when new messages are appended

### 4. TOOL SYSTEM ENHANCEMENTS

#### Tool Execution & Management - August-October 2025
- **Tool executors** (#658, August 2025) - New tool execution framework (Sequential, Concurrent, Custom)
- **Concurrent executor optimization** (#954, October 2025) - Removed no-op gather for better performance
- **Module-based tool loading** (#989, October 2025) - Import tools from Python modules with `tools=["my_module.tools"]` syntax
- **Tool hot reload support** (#928, September 2025) - Added `supports_hot_reload` property to PythonAgentTool
- **Output schema support** (#818, September 2025) - Optional outputSchema for structured tool responses
- **Async generator tools** (#788, September 2025) - Full async support for streaming and long-running operations

#### Tool Optimization & Reliability - October-November 2025
- **Skip model invocation optimization** (#1068, October 2025) - Skip redundant model calls when ToolUse blocks already exist
- **Invalid tool name transformation** (#1091, October 2025) - Transform invalid tool names to prevent session poisoning
- **Orphaned ToolUse cleanup** (#1123, November 2025) - Automatic cleanup of broken conversation states
- **Tool executor context handling** (#1128, November 2025) - Fixed handling of None structured output context
- **ToolContext enhancements** (#557, August 2025) - Exposed tool_use and agent through ToolContext
- **String descriptions in Annotated parameters** (#1089, November 2025) - Support string descriptions in Annotated tool parameters for better documentation
- **Security: tool name collision prevention** (#1214, November 2025) - Prevent tool name and sys modules collisions in tool_loader for improved security

### 5. INTERRUPTS SYSTEM - October 2025

A completely new capability enabling human-in-the-loop workflows:

- **Hook-based interrupts** (#987) - Interrupt agent execution via BeforeToolCallEvent hooks with InterruptDecision support
- **Decorated tool interrupts** (#1041) - Interrupt support directly in @tool decorated functions for fine-grained control
- **Direct tool call interrupt handling** (#1097) - Prevent interrupts during direct tool invocation for consistent behavior
- **Interruptible multi-agent hooks** (#1207, November 2025) - Hook interface enabling interrupts in multi-agent orchestration
- **Shared interrupt state** (#1148, November 2025) - Share interrupt state across agents in multi-agent workflows
- **Interrupt context separation** (#1194, November 2025) - Improved interrupt activation with separate context setting

### 6. STRUCTURED OUTPUT SYSTEM - October 2025

Major enhancement for type-safe responses:

- **Structured output in agent loop** (#943) - Native Pydantic model support via `structured_output_model` parameter with:
  - Automatic validation against Pydantic schemas
  - Retry logic on validation failures
  - Streaming support
  - Dedicated StructuredOutputEvent system
- **Improved circular reference handling** (#817, September 2025) - Enhanced detection and handling
- **ToolChoice for structured output** (#720, September 2025) - Bedrock and Anthropic support for forced tool calls
- **LiteLLM structured output** (#1021, October 2025) - Enhanced handling for LiteLLM provider
- **Structured output span** (#655, August 2025) - Enhanced observability

### 7. SESSION MANAGEMENT - July-November 2025

#### Core Session Features - July-August 2025
- **Session persistence** (#302, August 2025) - Persistent storage for maintaining conversation state
- **Conversation manager storage** (#441, August 2025) - Store conversation managers directly in sessions
- **Message content redaction** (#446, August 2025) - Redact sensitive content from messages
- **Agent State management** (#292, July 2025) - Persistent agent state across interactions

#### Session Performance - October-November 2025
- **Concurrent message reading** (#897, October 2025) - Improved performance for session managers
- **Multiagent session persistence** (#1110, #1071, November 2025) - Full support for Graph and Swarm orchestrators with repository pattern

### 8. TELEMETRY & OBSERVABILITY

#### OpenTelemetry Updates - September-November 2025
- **OTEL v1.37 semantic conventions** (#952, October 2025) - Updated traces to match latest standards
- **Time to first byte metrics** (#997, October 2025) - Added `timeToFirstByteMs` metric with updated semantic conventions
- **Event serialization fix** (#977, October 2025) - Removed double serialization in telemetry pipeline
- **Cache usage metrics** (#825, September 2025) - OpenTelemetry span attributes for cache read/write input tokens
- **Tool definitions in traces** (#1113, November 2025) - Add tool definitions to traces via semconv opt-in
- **Telemetry opt-in attributes update** (#1152, November 2025) - Updated opt-in attributes to internal

#### Earlier Telemetry Features - June-August 2025
- **OpenTelemetry exporter arguments** (#365, June 2025) - Exposed initialization arguments in API
- **Meter initialization** (#219, June 2025) - Enhanced telemetry capabilities
- **Cached token metrics** (#531, August 2025) - Token usage metrics for Amazon Bedrock

### 9. MODEL PROVIDER ENHANCEMENTS

#### New Model Providers - June-September 2025
- **Writer model provider** (#228, June 2025) - Support for Writer AI models
- **Mistral model support** (#284, June 2025) - Integration with Mistral AI models
- **Gemini model provider** (#725, September 2025) - Full feature compatibility with Google's Gemini
- **llama.cpp model provider** (#585, September 2025) - Native local inference capabilities

#### Bedrock Enhancements - September-November 2025
- **Region-aware default model IDs** (#835, September 2025) - Automatic model ID formatting with fallback warnings
- **VPC endpoint support** (#502, August 2025) - Secure AWS deployments
- **Claude citation support** (#631, August 2025) - Enhanced traceability
- **Default read timeout** (#829, September 2025) - Configurable 120-second default
- **Decoupled ContentBlock handling** (#836, September 2025) - Improved separation between Strands and BedrockModel
- **Redacted content handling** (#848, September 2025) - Support for redacted reasoning content in streaming
- **Bedrock throttling retry** (#1096, October 2025) - Enhanced retry logic for various throttling exceptions
- **SystemContentBlock prompt caching** (#1112, November 2025) - Provider-agnostic prompt caching starting with Bedrock

#### Provider-Specific Improvements
- **Gemini asyncio fixes** (#932, #955, October 2025) - Fixed event loop closed errors
- **Gemini error message handling** (#1062, November 2025) - Robust handling of non-JSON error messages
- **OpenAI error handling** (#918, October 2025) - Improved error handling
- **OpenAI reasoningContent handling** (#1099, October 2025) - Drop reasoningContent when not supported
- **OpenAI reasoning content** (#187, June 2025) - Enhanced reasoning capabilities
- **Anthropic context overflow handling** (#1137, November 2025) - Better detection of "prompt is too long" errors
- **Configuration validation** (#819, September 2025) - Warnings for unknown properties across all providers

#### LiteLLM Enhancements - November 2025
- **SystemContentBlocks in LiteLLMModel** (#1141, November 2025) - Prompt caching support for LiteLLM provider
- **LiteLLM cache token fix** (#1233, November 2025) - Fixed cacheWriteInputTokens population from correct field
- **LiteLLM stream validation** (#1183, November 2025) - Add validation for stream parameter

### 10. GUARDRAILS - August-November 2025

- **ToolResult redaction** (#1080, November 2025) - Proper redaction of toolResult blocks when guardrails detect sensitive content
- **Guardrails trace level support** (#1072, November 2025) - Fixed message redaction with `guardrails_trace="enabled_full"` mode

### 11. CONVERSATION MANAGEMENT - June 2025

- **Summarization strategy** (#112, June 2025) - Implement summarization for conversation managers to handle long conversations

### 12. AGENT CONFIGURATION - October 2025 (Experimental)

- **JSON-based agent configuration** (#935) - Declarative agent configuration from JSON files via `config_to_agent()` function with:
  - Support for model, prompt, tools, and name configuration
  - JSON schema validation
  - Enables configuration-as-code workflows

### 13. EVENT LOOP & EXECUTION

- **Model execution handling** (#958, October 2025) - Enhanced event loop to better handle model execution
- **Agent invoke flexibility** (#653, July 2025) - Support for agent invoke with no input or Message input
- **MultiAgent `__call__` implementation** (#645, July 2025) - Direct callable interface for MultiAgentBase

### 14. API IMPROVEMENTS

- **invocation_state parameter** (#966, October 2025) - Replaced generic `**kwargs` with typed `invocation_state` dictionary parameter across Agent and MultiAgent APIs for better type safety

### 15. CACHING & PERFORMANCE - November 2025

- **SystemContentBlock prompt caching** (#1112) - Provider-agnostic prompt caching support for improved performance and reduced costs, starting with Amazon Bedrock

---

## Feature Timeline by Month

### November 2025 (v1.15.0-v1.18.0)
- SystemContentBlock prompt caching
- Multiagent session persistence
- Multiple error handling improvements (Anthropic context overflow, Gemini error messages, orphaned ToolUse cleanup, tool executor context)
- Guardrails enhancements (ToolResult redaction, trace level support)
- **v1.16-v1.18 additions:**
  - Interruptible multi-agent hooks
  - Async hooks support
  - Shared interrupt state and thread context
  - Multi-agent input handling
  - Swarm handoff improvements
  - MCP reliability (timeout config, 5xx handling, connection protection)
  - LiteLLM enhancements (SystemContentBlocks, cache tokens, stream validation)
  - Tool definitions in telemetry traces
  - Security: tool name collision prevention
  - String descriptions in Annotated tool parameters
  - PrintingCallbackHandler verbose output option

### October 2025 (v1.11.0-v1.14.0)
- OTEL v1.37 semantic conventions
- Tool call cancellation
- Concurrent message reading
- Model execution handling
- Multiple provider fixes (Gemini, OpenAI, Bedrock)
- MCP improvements
- Interrupts system (hook-based, decorated tools, direct tool calls)
- Structured output in agent loop
- Multi-agent streaming (stream_async)
- Tool system enhancements (module loading, elicitation, optimization)
- JSON-based agent configuration
- invocation_state parameter
- Time to first byte metrics

### September 2025 (v1.9.0-v1.10.0)
- Gemini model provider
- llama.cpp model provider
- Stable hooks API
- Tool hot reload
- Output schema support
- Async generator tools
- Multiple Bedrock enhancements
- Swarm configurable entry point
- Cache usage metrics
- Improved circular reference handling
- Configuration validation

### August 2025 (v1.3.0-v1.8.0)
- A2A protocol features
- MCP enhancements (async, pagination, prompts)
- Tool executors
- Session persistence
- VPC endpoint support
- Claude citation support
- TypedEvent system
- Conversation manager storage
- Message content redaction
- Cyclic graph support
- Hooks for MultiAgents

### July 2025 (v1.1.0-v1.2.0)
- Core typed hooks & callbacks
- Before/after tool call hooks
- Message append hooks
- Agent State management
- Agent invoke flexibility
- MultiAgent `__call__` implementation

### June 2025 (v1.0.1)
- Writer model provider
- Mistral model support
- OpenAI reasoning content
- OpenTelemetry exporter arguments
- Meter initialization
- Summarization strategy

---

## Key Statistics

- **18 minor version releases** after 1.0.0
- **212 commits** of improvements and new features
- **6+ new model providers** added (Writer, Mistral, Gemini, llama.cpp, and improvements to existing ones)
- **2 major protocol integrations** (A2A and enhanced MCP)
- **3 new orchestration patterns** (enhanced Swarm, Graph, and multi-agent capabilities)
- **New system-level capabilities**: Interrupts, Structured Output, Advanced Tool Executors, Async Hooks

---

## Major Capability Categories

The features can be grouped into these strategic pillars:

1. **Protocol Integration** (A2A, MCP) - Enable agent interoperability
2. **Multi-Agent Orchestration** (Swarm, Graph) - Coordinate multiple agents
3. **Production Readiness** (Sessions, Telemetry, Guardrails) - Enterprise deployment
4. **Developer Experience** (Hooks, Events, Configuration) - Extensibility and ease of use
5. **Model Provider Ecosystem** (6+ new providers) - Flexibility and choice
6. **Performance & Reliability** (Caching, Error Handling, Optimization) - Production quality
7. **Advanced AI Features** (Structured Output, Interrupts, Reasoning) - Cutting-edge capabilities

---

## Comparison with 1.0 Baseline

Based on the 1.0 announcement blog post, the core features at 1.0 included:

### What was IN 1.0:
- Single Agent execution
- Basic tool system with @tool decorator
- Model provider support (Bedrock, Anthropic, OpenAI, Ollama, etc.)
- Native async support and stream_async method
- Agents-as-tools pattern
- Basic multi-agent primitives (early versions of Swarm/Graph)
- Event-driven execution model

### What was ADDED after 1.0:
- Complete A2A protocol integration
- Comprehensive MCP enhancements
- Full session persistence (including multi-agent)
- Interrupts system for human-in-the-loop
- Structured output with Pydantic models
- Advanced tool executors
- Stable hooks API
- OpenTelemetry v1.37 compliance
- Prompt caching
- Multiple new model providers
- Production-grade error handling
- Guardrails enhancements
- JSON-based configuration

---

## Conclusion

This comprehensive analysis shows that the Strands SDK has seen tremendous growth post-1.0, with significant additions in protocol integration, multi-agent capabilities, production features, and developer experience enhancements. The SDK has evolved from a solid foundation to a truly enterprise-ready, protocol-native, multi-agent orchestration platform.

**Development Velocity**: Averaging ~46 commits per month over 4 months demonstrates active, sustained development and community engagement.

**Strategic Direction**: The post-1.0 features show a clear focus on:
- **Interoperability** (A2A, MCP)
- **Production readiness** (Sessions, Telemetry, Error Handling)
- **Developer experience** (Hooks, Configuration, Type Safety)
- **Advanced AI capabilities** (Structured Output, Interrupts, Reasoning)
