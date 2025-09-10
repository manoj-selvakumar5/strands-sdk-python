# Latest Features

This document tracks the newest features added to the Strands Python SDK, organized by month.

## September 2025

### Async Generator Tools
- **Async generator tools** - Full async support for tool generators, enabling streaming and long-running operations (#788)

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
- **List prompts and get prompt methods** - Enhanced MCP client capabilities for prompt management (#160)
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