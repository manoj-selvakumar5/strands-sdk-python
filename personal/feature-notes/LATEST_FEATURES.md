# Latest Features

This document tracks the newest features added to the Strands Python SDK, organized by month.

## November 2025

### Caching & Performance
- **SystemContentBlock prompt caching** - Provider-agnostic prompt caching support via SystemContentBlock for improved performance and reduced costs, starting with Bedrock (#1112)

### Session Management
- **Multiagent session persistence** - Full session persistence support for Graph and Swarm orchestrators including repository pattern management, enabling multi-agent conversations to be saved and resumed (#1110, #1071)

### Error Handling
- **Anthropic context overflow handling** - Better detection and handling of "prompt is too long" errors from Anthropic API with proper ContextWindowOverflowException mapping (#1137)
- **Gemini error message handling** - Robust handling of non-JSON error messages from Gemini API preventing parsing failures (#1062)
- **Orphaned ToolUse cleanup** - Automatic cleanup of orphaned tool use messages to prevent broken conversation states (#1123)
- **Tool executor context handling** - Fixed handling of None structured output context in tool executors for more reliable execution (#1128)

### Guardrails
- **ToolResult redaction** - Proper redaction of toolResult blocks when guardrails detect sensitive content (#1080)
- **Guardrails trace level support** - Fixed message redaction when using `guardrails_trace="enabled_full"` mode (#1072)

## October 2025

### Telemetry & Observability
- **OTEL v1.37 semantic conventions** - Updated traces to match OpenTelemetry v1.37 semantic conventions for better observability (#952)
- **Event serialization fix** - Removed double serialization for events in telemetry pipeline (#977)

### Hooks & Events System
- **Tool call cancellation** - Before tool call event can now cancel tool execution for better control flow (#964)

### Session Management
- **Concurrent message reading** - Implemented concurrent message reading for session managers improving performance (#897)

### Event Loop
- **Model execution handling** - Enhanced event loop to better handle model execution (#958)

### Model Providers
- **Gemini asyncio fixes** - Fixed event loop closed error from Gemini asyncio operations (#932, #955)
- **OpenAI error handling** - Improved error handling for OpenAI models (#918)

### MCP (Model Context Protocol)
- **Timeout issue fixes** - Fixed MCP timeout issues for more reliable connections (#922)
- **Idempotent instrumentation** - Made MCP instrumentation idempotent to prevent recursion errors (#892)

### Tool System
- **Concurrent executor optimization** - Removed no-op gather in concurrent tool executor for better performance (#954)
- **Module-based tool loading** - Refactored tool loading to support importing tools from Python modules with `tools=["my_module.tools"]` syntax (#989)
- **Skip model invocation optimization** - Skip redundant model calls when the latest message already contains ToolUse blocks for improved performance (#1068)
- **Invalid tool name transformation** - Transform invalid tool names on sending to provider to prevent session poisoning with invalid references (#1091)
- **MCP elicitation support** - Support for MCP server tool elicitation capabilities enabling dynamic tool discovery (#1094)

### Agent Configuration (Experimental)
- **JSON-based agent configuration** - Declarative agent configuration from JSON files via `config_to_agent()` function with support for model, prompt, tools, and name configuration including JSON schema validation (#935)

### Structured Output System
- **Structured output in agent loop** - Native Pydantic model support in agent loop via `structured_output_model` parameter with validation, retry logic, streaming support, and dedicated StructuredOutputEvent system (#943)

### Interrupts System
- **Hook-based interrupts** - Interrupt agent execution via BeforeToolCallEvent hooks with InterruptDecision support enabling human-in-the-loop workflows (#987)
- **Decorated tool interrupts** - Interrupt support directly in @tool decorated functions for fine-grained control (#1041)
- **Direct tool call interrupt handling** - Prevent interrupts during direct tool invocation for consistent behavior (#1097)

### Multi-Agent Orchestrators
- **Stream_async for multiagent** - Async streaming support for Graph and Swarm orchestrators with comprehensive event system (BeforeMultiAgentInvokeEvent, AfterMultiAgentInvokeEvent) (#961)
- **Multiagent hooks and serialization** - Hook event support for multi-agent systems with serialize/deserialize functions for AgentResult enabling persistence (#1070)
- **MCP ToolProvider integration** - Experimental agent-managed MCP connections via ToolProvider interface for dynamic tool lifecycle management (#895)
- **Swarm initialization optimization** - Don't initialize agents on swarm construction, only when actually invoked for better resource management (#1107)

### Telemetry & Observability (Additional)
- **Time to first byte metrics** - Added `timeToFirstByteMs` metric to spans with updated semantic conventions and tool mappings for better latency tracking (#997)

### API Changes
- **invocation_state parameter** - Replaced generic `**kwargs` with typed `invocation_state` dictionary parameter across Agent and MultiAgent APIs for better type safety and clarity (#966)

### Model Provider Enhancements
- **Bedrock throttling retry** - Enhanced retry logic for various Bedrock throttling exception cases improving reliability (#1096)
- **OpenAI reasoningContent handling** - Drop reasoningContent from requests when not supported by the model to prevent API errors (#1099)
- **LiteLLM structured output** - Enhanced structured output handling for LiteLLM provider with improved logic (#1021)

## September 2025

### Model Provider Expansion
- **Gemini model provider** - Support for Google's Gemini AI models with full feature compatibility (#725)
- **llama.cpp model provider** - Native support for llama.cpp models with local inference capabilities (#585)

### Hooks & Events System
- **Stable hooks API** - ModelCall and ToolCall events marked as non-experimental with improved naming (BeforeModelCallEvent, AfterModelCallEvent, BeforeToolCallEvent, AfterToolCallEvent) (#926)
- **MultiAgent HookEvent base class** - New base class for multi-agent hook events enabling better event inheritance (#925)

### Tool System
- **Tool hot reload support** - Added `supports_hot_reload` property to PythonAgentTool for dynamic tool reloading (#928)
- **Output schema support** - Optional outputSchema support for tool specifications enabling structured tool responses (#818)
- **Async generator tools** - Full async support for tool generators, enabling streaming and long-running operations (#788)

### Bedrock Model Enhancements
- **Region-aware default model IDs** - Automatic model ID formatting based on AWS region with fallback warnings (#835)
- **ToolChoice for structured output** - Bedrock and Anthropic ToolChoice support in structured_output for forced tool calls (#720)
- **Default read timeout** - Configurable 120-second default read timeout for Bedrock model calls (#829)
- **Decoupled ContentBlock handling** - Improved separation between Strands ContentBlock and BedrockModel implementations (#836)
- **Redacted content handling** - Support for handling redacted reasoning content in Bedrock streaming responses (#848)

### Swarm Orchestrator
- **Configurable entry point** - Make swarm entry point configurable for flexible agent workflow initialization (#851)

### Observability & Telemetry
- **Cache usage metrics** - OpenTelemetry span attributes for cache read/write input tokens enabling cost monitoring (#825)

### Structured Output
- **Improved circular reference handling** - Enhanced detection and handling of circular references in structured output schemas (#817)

### Developer Experience
- **Model configuration validation** - Warnings emitted for unknown model configuration properties across all providers (#819)

## August 2025

### Multi-Agent Orchestrators
- **Swarm orchestrator** - Multi-agent orchestrator with tracing capabilities for coordinated agent workflows (#416, #461)
- **Graph orchestrator** - Multi-agent orchestrator supporting multi-modal inputs and complex workflow graphs (#336, #430)
- **Hooks for MultiAgents** - Enable hooks functionality across multi-agent systems (#760)

### Session Management
- **Session persistence** - Persistent session storage for maintaining conversation state across interactions (#302)
- **Conversation manager storage** - Store conversation managers directly in sessions (#441)
- **Message content redaction** - Ability to redact sensitive content from messages in sessions (#446)

### Cloud & Model Integration
- **VPC endpoint support** - BedrockModel now supports VPC endpoints for secure AWS deployments (#502)
- **Claude citation support** - Added citation capabilities with BedrockModel for enhanced traceability (#631)

### Event System
- **Typed events system** - TypedEvent inheritance for robust callback behavior and event handling (#755, #745)

### MCP (Model Context Protocol) Enhancements
- **MCP async call tool** - Async support for MCP tool execution (#406)
- **List prompts and get prompt methods*3* - Enhanced MCP client capabilities for prompt management (#160)
- **Pagination for list_tools_sync** - Improved handling of large tool sets (#436)
- **Structured content retention** - Retain structured content in AgentTool responses (#528)

### A2A (Agent-to-Agent) Features
- **FileParts and DataParts support** - Enhanced data handling for agent communications (#596)
- **Tools as skills** - Treat tools as reusable skills across agents (#287)
- **Containerized deployment support** - Support mounts for containerized deployments (#524)
- **Configurable request handler** - Customizable request handling for A2A interactions (#601)

### Tool System
- **Tool executors** - New tool execution framework for enhanced tool management (#658)
- **Cached token metrics** - Token usage metrics support for Amazon Bedrock (#531)
- **ToolContext enhancements** - Exposed tool_use and agent through ToolContext to decorated tools (#557)
- **Structured output span** - Enhanced structured output capabilities (#655)
- **MCP Client configuration** - Server initialization timeout options (#657)

### Graph Capabilities
- **Cyclic graph support** - Allow cyclic graphs in multi-agent workflows (#497)

## July 2025

### Hooks & Callbacks System
- **Core typed hooks & callbacks** - Fundamental system for extensible agent behavior (#304)
- **Before/after tool call hooks** - Hooks that can update values during tool execution (#352)
- **Message append hooks** - Hooks triggered when new messages are appended to agent messages (#385)

### Agent Features
- **Agent State management** - Persistent agent state across interactions (#292)
- **Agent invoke flexibility** - Support for agent invoke with no input or Message input (#653)
- **MultiAgent `__call__` implementation** - Direct callable interface for MultiAgentBase (#645)

## June 2025

### Model Provider Expansion
- **Writer model provider** - Support for Writer AI models (#228)
- **Mistral model support** - Integration with Mistral AI models (#284)
- **OpenAI reasoning content** - Enhanced reasoning capabilities for OpenAI models (#187)

### Structured Output
- **Pydantic model support** - Full structured output support using Pydantic models for type-safe responses (#60)

### Observability & Telemetry
- **OpenTelemetry exporter arguments** - Exposed OpenTelemetry exporter initialization arguments in API (#365)
- **Meter initialization** - Enhanced telemetry capabilities with meter initialization (#219)

### Conversation Management
- **Summarization strategy** - Implement summarization strategy for conversation managers to handle long conversations (#112)