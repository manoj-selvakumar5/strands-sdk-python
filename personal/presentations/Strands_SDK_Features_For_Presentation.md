# Strands Python SDK - Complete Feature Overview
## PowerPoint Presentation Guide

This document organizes all Strands SDK features into logical groups optimized for creating PowerPoint slides.

---

## PRESENTATION FLOW RECOMMENDATION

### Opening Slides
1. **Title Slide**: "Strands Python SDK - Build Production-Ready AI Agents"
2. **Value Proposition**: "Model-driven AI agents in just a few lines of code"
3. **Agenda**: Overview of 16 feature categories

### Main Content (15-20 slides organized in 6 sections)
- Section 1: Foundation (3-4 slides)
- Section 2: Building Blocks (3-4 slides)
- Section 3: Orchestration (2-3 slides)
- Section 4: Advanced Capabilities (3-4 slides)
- Section 5: Production Features (2-3 slides)
- Section 6: Developer Experience (2 slides)

### Closing Slides
- Key Differentiators
- Experimental/Roadmap Features
- Getting Started / Resources

---

## KEY DIFFERENTIATORS
*Suggested for emphasis throughout presentation*

1. **Model Agnostic** - 12+ providers, easy switching
2. **MCP Native** - First-class Model Context Protocol support
3. **Multi-Agent Orchestration** - Swarm & Graph built-in
4. **Production Ready** - Sessions, telemetry, guardrails
5. **Developer Friendly** - @tool decorator, hot reload, type safety
6. **Extensible** - Hooks, custom providers, tool executors
7. **A2A Protocol** - Agent discovery and communication
8. **Streaming First** - Real-time responses everywhere

---

# SECTION 1: FOUNDATION

## 1. CORE ARCHITECTURE & AGENT LOOP

**Slide Title**: "Foundation - The Agent Loop"

### Core Concepts
- **Event-driven execution model** - Core agent processing cycle
- **Automatic tool orchestration** - Seamless tool selection and execution
- **Message-based conversation** - Structured message history management
- **State persistence** - Agent state across interactions
- **Retry logic** - Exponential backoff for throttling (4s → 240s, max 6 attempts)

### Agent Types
- **Single Agent** - Standalone agent execution
- **AgentResult** - Comprehensive execution results with metrics
- **Agent invocation flexibility** - Support for no input, text, or Message input

### Core Abstractions
- **ContentBlocks** - Unified content representation (text, images, video, documents)
- **Messages** - Structured conversation format (user/assistant roles)
- **ToolSpec** - JSON Schema-based tool specifications
- **ToolUse/ToolResult** - Tool invocation and response protocol

**Slide Layout Suggestion**: Diagram showing agent loop flow with model → tool → model cycle

---

## 2. MODEL PROVIDERS (12+ Providers)

**Slide Title**: "Model Agnostic - 12+ Providers Supported"

### Cloud Providers

#### Amazon Bedrock (Default)
- Region-aware model IDs with automatic formatting
- VPC endpoint support for secure deployments
- Application inference profiles
- Bedrock-specific guardrails integration
- Claude citation support
- Throttling retry with enhanced logic
- Default 120s read timeout
- ReasoningContent handling (redacted content support)

#### Anthropic
- Direct API integration
- Context overflow detection and handling
- ToolChoice support for structured output
- Prompt caching support

#### Google Gemini
- Full feature compatibility
- Asyncio fixes for event loop
- Non-JSON error message handling
- Multi-modal support

#### OpenAI
- Enhanced error handling
- ReasoningContent support (drop when not supported)
- Streaming support

#### AWS SageMaker
- SageMaker endpoint integration

### Open Source / Local Providers
- **Ollama** - Local model hosting
- **llama.cpp** - Native local inference
- **LlamaAPI** - Llama hosted API

### Multi-Model Providers
- **LiteLLM** - Universal LLM gateway (100+ models)
  - Enhanced structured output handling
- **Writer** - Writer AI models
- **Mistral AI** - Mistral models
- **Cohere** - Cohere models

### Cross-Provider Features
- **Streaming support** - Real-time response streaming (enable/disable per model)
- **Configuration validation** - Warnings for unknown properties
- **Custom providers** - Extensible provider interface
- **Model-agnostic prompt caching** - SystemContentBlock caching

**Slide Layout Suggestion**: Logo grid of all providers with cloud/local/multi-model grouping

---

## 3. TOOL SYSTEM BASICS

**Slide Title**: "Tools - Give Your Agents Capabilities"

### Simple Tool Definition
```python
@tool
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    return f"Sunny in {location}"
```

### Core Features
- **@tool decorator** - Python function → agent tool
- **Automatic metadata extraction** - From docstrings and type hints
- **JSON Schema generation** - Automatic input validation
- **ToolContext injection** - Access to tool_use, agent, invocation_state
- **Output schema support** - Structured tool responses

### Tool Loading Methods
1. **Direct registration** - `tools=[tool1, tool2]`
2. **Module-based loading** - `tools=["my_module.tools"]`
3. **Hot reload from directory** - `load_tools_from_directory=True`
   - Automatic tool discovery from `./tools/`
   - File watcher for changes
   - Dynamic tool reloading

**Slide Layout Suggestion**: Code example + 3 loading methods diagram

---

# SECTION 2: BUILDING BLOCKS

## 4. TOOL SYSTEM DEEP DIVE

**Slide Title**: "Advanced Tool Capabilities"

### Tool Execution
**Tool Executors Framework**:
- **SequentialExecutor** - Tools run one at a time
- **ConcurrentExecutor** - Parallel tool execution
- Optimized gather operations
- Context handling for structured output

### Advanced Features
- **Async generator tools** - Full async support, streaming, long-running operations
- **Tool interrupts** - Pause execution for human-in-the-loop
  - Hook-based interrupts via BeforeToolCallEvent
  - Decorated tool interrupts (@tool with interrupt support)
  - Direct tool call interrupt prevention
- **Tool result redaction** - Guardrail-based content filtering
- **Invalid tool name transformation** - Prevent session poisoning
- **Skip model invocation optimization** - Skip redundant calls when ToolUse exists
- **Orphaned ToolUse cleanup** - Automatic cleanup of broken conversation states

**Slide Layout Suggestion**: Split into "Execution Patterns" and "Advanced Features" columns

---

## 5. MODEL CONTEXT PROTOCOL (MCP)

**Slide Title**: "MCP Native - First-Class Protocol Support"

### MCP Client
- **Background thread management** - Non-blocking MCP communication
- **Context manager pattern** - Proper resource cleanup
- **Transport abstraction** - stdio, SSE, HTTP
- **Timeout control** - Configurable startup (default 30s) and execution timeouts
- **Client reuse** - Across multiple sessions

### MCP Operations
**Synchronous & Asynchronous Support**:
- `list_tools_sync()` / `list_tools_async()`
- `call_tool_sync()` / `call_tool_async()`
- `list_prompts_sync()` / `get_prompt_sync()`
- **Pagination support** - For large tool sets
- **Tool elicitation** - Dynamic tool discovery from servers

### Integration Features
- **MCPAgentTool adapter** - MCP tools → Strands AgentTools
- **Structured content retention** - Preserve structured data in responses
- **Idempotent instrumentation** - Prevent recursion errors
- **Timeout issue fixes** - Reliable connections
- **OpenTelemetry integration** - Distributed tracing

### Experimental: MCP ToolProvider
- **Agent-managed MCP connections** - Dynamic tool lifecycle
- **ToolProvider interface** - For multi-agent systems

**Slide Layout Suggestion**: Architecture diagram showing MCP server → Client → Agent flow

---

## 6. CONVERSATION MANAGEMENT

**Slide Title**: "Smart Conversation Management"

### Conversation Managers

#### 1. SlidingWindowConversationManager (Default)
- Fixed window size (default 40 messages)
- Tool result truncation (`should_truncate_results`)
- Preserves tool use/result pairs
- **Proactive trimming** via `apply_management()`
- **Reactive recovery** via `reduce_context()`

#### 2. SummarizingConversationManager
- LLM-powered summarization
- Replace old messages with summary
- Custom summarization prompts
- Reactive-only (no proactive trimming)

#### 3. NullConversationManager
- No management (keep all messages)
- For short conversations or manual control

### Context Management
- **ContextWindowOverflowException** - Input too large
- **MaxTokensReachedException** - Output hit limit (unrecoverable)
- **Automatic retry** - After context reduction
- **Store conversation managers in sessions** - Persistence

**Slide Layout Suggestion**: 3-column comparison table of manager types

---

# SECTION 3: ORCHESTRATION

## 7. MULTI-AGENT ORCHESTRATION

**Slide Title**: "Multi-Agent Systems - Swarm & Graph"

### Swarm Orchestrator
**Self-organizing collaborative teams**:
- **Shared working memory** - `SharedContext` for coordination
- **Tool-based coordination** - Agents use tools to delegate
- **Autonomous collaboration** - No central control
- **Dynamic task distribution** - Based on capabilities
- **Configurable entry point** - Flexible workflow initialization
- **Lazy initialization** - Don't initialize until invoked
- **Async streaming support** - `stream_async()` for Swarm
- **Session persistence** - Save and resume multi-agent conversations

### Graph Orchestrator
**Deterministic workflow execution**:
- **Directed graph execution** - Dependency-based flow
- **Agents & MultiAgents as nodes** - Compose Swarms, Graphs
- **Output propagation** - Along edges
- **Cyclic graph support** - Feedback loops
- **Multi-modal inputs** - Rich content support
- **Nested graphs** - Graph as node in another Graph
- **Max execution limits** - `max_node_executions`, `execution_timeout`
- **Async streaming support** - `stream_async()` for Graph
- **Session persistence** - Repository pattern for multi-agent state

### Multi-Agent Features
- **Hooks for MultiAgents** - Cross-agent coordination
- **MultiAgent HookEvent base class** - Event inheritance
- **BeforeMultiAgentInvokeEvent / AfterMultiAgentInvokeEvent** - Lifecycle hooks
- **Serialize/deserialize AgentResult** - For persistence
- **MultiAgent `__call__`** - Direct callable interface

**Slide Layout Suggestion**: Side-by-side visual of Swarm (mesh network) vs Graph (directed graph)

---

## 8. AGENT-TO-AGENT (A2A) PROTOCOL

**Slide Title**: "A2A Protocol - Agent Discovery & Communication"

### A2A Server
**Expose agents via standardized protocol**:
- **HTTP service wrapper** - FastAPI & Starlette support
- **AgentCard publishing** - At `/.well-known/agent.json`
- **Agent discovery** - Metadata about capabilities
- **Skills auto-discovery** - Tools → Skills conversion
- **Streaming responses** - Real-time A2A streaming

### A2A Features
- **FileParts support** - Images, videos, documents
- **DataParts support** - Structured JSON data
- **Tools as skills** - Reusable capabilities
- **Containerized deployment** - Docker/K8s support with volume mounts
- **Load balancer support** - Path preservation/stripping
- **Configurable request handler** - Custom task stores, queues, push notifications

### A2A Executor
- **Message conversion** - A2A ↔ Strands ContentBlocks
- **Task state management** - Working, complete, failed
- **StrandsA2AExecutor** - Execution engine

**Slide Layout Suggestion**: Architecture diagram with agent discovery flow

---

# SECTION 4: ADVANCED CAPABILITIES

## 9. STREAMING & ASYNC

**Slide Title**: "Real-Time Streaming & Async Support"

### Invocation Patterns
1. **Synchronous** - `agent("hello")` - Blocks until complete
2. **Asynchronous** - `agent.invoke_async("hello")` - Non-blocking
3. **Streaming async** - `agent.stream_async("hello")` - Real-time events

### Stream Event Types

**Raw Events (from provider)**:
- MessageStartEvent
- ContentBlockStartEvent
- ContentBlockDeltaEvent (text, toolUse, reasoningContent, citation)
- ContentBlockStopEvent
- MessageStopEvent
- MetadataEvent

**Typed Events (to user)**:
- InitEventLoopEvent
- StartEventLoopEvent
- ModelStreamChunkEvent
- TextStreamEvent
- ToolUseStreamEvent
- ReasoningTextStreamEvent
- CitationStreamEvent
- ModelMessageEvent
- ToolResultMessageEvent
- AgentResultEvent
- EventLoopStopEvent

### Callback Handlers
- **PrintingCallbackHandler** - Default stdout streaming
- **null_callback_handler** - Silent mode
- **CompositeCallbackHandler** - Multiple handlers
- **Custom handlers** - User-defined callbacks

### Architecture
- **ThreadPoolExecutor** - For sync calls
- **process_stream()** - Stream processing pipeline
- **State management** - Accumulated text, tool use, reasoning
- **Blank text handling** - Prevent API errors

**Slide Layout Suggestion**: Flow diagram showing 3 invocation patterns

---

## 10. HOOKS & EVENTS SYSTEM

**Slide Title**: "Extensibility - Hooks & Events"

### Stable Hooks (Production-Ready)
- **BeforeModelCallEvent** - Before model invocation
- **AfterModelCallEvent** - After model response
- **BeforeToolCallEvent** - Before tool execution
  - Can cancel tool execution
  - Interrupt support
- **AfterToolCallEvent** - After tool completion
- **BeforeInvocationEvent** - Before agent processes input
- **AfterInvocationEvent** - After agent completes
- **AgentInitializedEvent** - Agent creation
- **MessageAddedEvent** - Message appended to history

### Hook Features
- **TypedEvent system** - Strongly-typed events
- **HookProvider interface** - Composable hook objects
- **HookRegistry** - Event registration
- **Value modification** - Hooks can transform inputs/outputs
- **Async hook support** - Non-blocking callbacks
- **MultiAgent hooks** - Cross-agent coordination
- **Hook chaining** - Ordered execution

### Experimental Hooks
- BeforeToolInvocationEvent / AfterToolInvocationEvent
- BeforeModelInvocationEvent / AfterModelInvocationEvent

**Slide Layout Suggestion**: Timeline diagram showing hook execution points

---

## 11. STRUCTURED OUTPUT & GUARDRAILS

**Slide Title**: "Type Safety & Content Safety"

### Structured Output (Pydantic Integration)
- **Native Pydantic model support** - Type-safe responses
- **`structured_output_model` parameter** - In agent loop
- **Automatic validation** - Against Pydantic schema
- **Retry logic** - On validation failures
- **Streaming support** - With structured output
- **StructuredOutputEvent system** - Dedicated events
- **JSON Schema generation** - From Pydantic models
- **Circular reference handling** - Improved detection
- **ToolChoice support** - Force tool calls (Bedrock/Anthropic)

### Guardrails (Amazon Bedrock)

**Guardrail Types**:
1. **Content Policy** - Filter insults, hate, sexual, violence, misconduct, prompt attacks
2. **Topic Policy** - Block/deny specific topics
3. **Word Policy** - Custom words, managed word lists (profanity)
4. **Sensitive Information Policy**
   - PII detection (30+ entity types: email, phone, SSN, credit cards, etc.)
   - Custom regex patterns
   - Anonymization or blocking
5. **Contextual Grounding Policy** - Ensure responses grounded in context

**Guardrail Features**:
- **GuardrailConfig** - Configure identifier, version, processing mode
- **Trace support** - `trace="enabled"` or `"enabled_full"`
- **ToolResult redaction** - Proper handling of sensitive content
- **Message redaction** - When using trace modes
- **Input/output assessment** - Guardrail evaluation on both sides

**Slide Layout Suggestion**: Split slide - Structured Output (left) / Guardrails (right)

---

# SECTION 5: PRODUCTION FEATURES

## 12. SESSION PERSISTENCE & OBSERVABILITY

**Slide Title**: "Production-Ready - Sessions & Telemetry"

### Session Management

**Session Managers**:
1. **FileSessionManager** - Local file-based storage
2. **S3SessionManager** - AWS S3 storage
3. **RepositorySessionManager** - Abstract repository pattern

**Session Features**:
- **Persistent conversation state** - Across interactions
- **Session metadata** - Custom key-value data
- **Message content redaction** - Sensitive data filtering
- **Concurrent message reading** - Performance optimization
- **Multiagent session persistence** - Full Graph/Swarm support

### OpenTelemetry Integration
- **Automatic span creation** - Agent, model, tool spans
- **OTEL v1.37 semantic conventions** - Updated traces
- **Distributed tracing** - Across agents and tools
- **Custom attributes** - Model, provider, tool metadata

### Metrics & Monitoring
- **EventLoopMetrics** - Usage, latency, stop reason
- **Token usage** - Input, output, total, cached tokens
- **Cache metrics** - Read/write input tokens
- **Time to first byte (TTFB)** - Latency tracking
- **Execution time** - Per agent, tool, model call
- **Throttling metrics** - Retry attempts

### Telemetry Features
- **MetricsClient** - Programmatic access
- **Tracer** - `get_tracer()` for custom spans
- **StrandsTelemetry** - Global telemetry config
- **Exporter arguments** - OTLP endpoint configuration
- **Meter initialization** - For custom metrics
- **Event serialization** - Fixed double serialization

**Slide Layout Suggestion**: Split into "Sessions" and "Observability" sections

---

## 13. PERFORMANCE & ERROR HANDLING

**Slide Title**: "Optimized for Production"

### Performance Optimizations
- **Prompt caching** - Provider-agnostic via SystemContentBlock
  - Improved performance and reduced costs
  - Starting with Amazon Bedrock
- **Concurrent tool execution** - Parallel tool calls
- **Lazy initialization** - Swarm agents
- **Skip redundant model calls** - When ToolUse already present
- **Concurrent message reading** - Session managers
- **Optimized gather operations** - In tool executors

### Error Handling
**Typed Exceptions**:
- **ContextWindowOverflowException** - Input too large
- **MaxTokensReachedException** - Output hit limit (unrecoverable)
- **MCPInitializationException** - MCP startup failures

**Provider-Specific Handling**:
- **Anthropic context overflow** - Proper error mapping
- **Gemini error messages** - Non-JSON handling
- **Bedrock throttling retry** - Enhanced retry logic with exponential backoff
- **OpenAI reasoningContent** - Drop when not supported
- **Tool executor context** - None handling for structured output
- **Orphaned ToolUse cleanup** - Automatic conversation state repair

**Slide Layout Suggestion**: Performance (top) / Error Handling (bottom)

---

# SECTION 6: DEVELOPER EXPERIENCE

## 14. DEVELOPER EXPERIENCE

**Slide Title**: "Built for Developers"

### Configuration
- **JSON-based agent configuration** (Experimental) - `config_to_agent()`
  - Model, prompt, tools, name
  - JSON schema validation
- **Environment variable support** - For API keys, endpoints
- **Typed parameters** - `invocation_state` instead of `**kwargs`
- **Configuration warnings** - Unknown model properties

### Testing & Debugging
- **Trace levels** - enabled, disabled, enabled_full
- **Logging** - Structured logging throughout
- **Agent state introspection** - Access to messages, state, metrics
- **Dry-run support** - Test without execution

### Documentation & Type Safety
- **Type hints** - Full typing support throughout
- **Docstring extraction** - For automatic tool documentation
- **Comprehensive guides**:
  - Conversation Management Guide
  - Streaming and Async Guide
  - MCP Features Guide (Jupyter notebook)
  - Strands Protocol Integration Guide (A2A/MCP)
  - Max Tokens Examples (notebooks + Python)
- **API reference** - Auto-generated from code

**Slide Layout Suggestion**: 3 columns - Configuration / Testing / Documentation

---

## 15. ADVANCED FEATURES

**Slide Title**: "Advanced Capabilities"

### Citations (Amazon Bedrock)
- **Bedrock citation support** - Enhanced traceability
- **Citation streaming** - Real-time citation events
- **Citation content** - Structured citation data with references

### Reasoning Content (Extended Thinking)
- **ReasoningContent support** - Extended thinking (Claude)
- **Reasoning text streaming** - Stream reasoning process
- **Redacted content** - Handle sensitive reasoning
- **Reasoning signature** - Cryptographic signatures
- **Provider compatibility** - Drop when not supported (OpenAI)

### Rich Media Support
- **Image support** - JPEG, PNG, GIF, WebP
- **Video support** - MP4, MOV, MKV, WebM, FLV, AVI
- **Document support** - PDF, CSV, DOC, DOCX, XLS, XLSX, HTML, TXT, MD
- **Multi-modal messages** - Rich content in conversations
- **FileParts & DataParts** - For A2A communication

**Slide Layout Suggestion**: 3 sections - Citations / Reasoning / Media

---

# CLOSING SECTION

## 16. EXPERIMENTAL & ROADMAP

**Slide Title**: "What's Next - Experimental Features"

### Current Experimental Features
- **JSON-based agent configuration** - Declarative agents from config files
- **A2A protocol integration** - Expect breaking changes as protocol evolves
- **MCP ToolProvider** - Agent-managed MCP lifecycle
- **Experimental hooks** - Tool/Model invocation events (BeforeToolInvocationEvent, etc.)

### These Features May Change
- API signatures may evolve
- Breaking changes possible in minor versions
- Feedback welcome from early adopters

**Slide Layout Suggestion**: "Experimental" label with disclaimer about API stability

---

## GETTING STARTED

**Slide Title**: "Get Started in Minutes"

### Quick Start
```python
from strands import Agent
from strands.models.bedrock import BedrockModel

@tool
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    return f"Sunny in {location}"

agent = Agent(
    model=BedrockModel(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
    tools=[get_weather]
)

result = agent("What's the weather in Seattle?")
print(result.output)
```

### Resources
- **Documentation**: https://docs.aws.amazon.com/strands/
- **GitHub**: https://github.com/aws/strands-sdk-python
- **Examples**: https://github.com/aws/strands-sdk-python/tree/main/examples
- **PyPI**: `pip install strands`

**Slide Layout Suggestion**: Code example (large) + resource links (bottom)

---

## SUMMARY - KEY TAKEAWAYS

**Slide Title**: "Why Choose Strands?"

### 8 Key Differentiators
1. **Model Agnostic** - Switch between 12+ providers effortlessly
2. **MCP Native** - First-class Model Context Protocol support
3. **Multi-Agent Ready** - Built-in Swarm & Graph orchestrators
4. **Production Proven** - Sessions, telemetry, guardrails out of the box
5. **Developer Friendly** - Simple @tool decorator, hot reload, full type safety
6. **Highly Extensible** - Hooks system, custom providers, tool executors
7. **A2A Protocol** - Standardized agent discovery and communication
8. **Streaming First** - Real-time responses across all operations

### The Strands Promise
"Build sophisticated AI agents with production-grade reliability in just a few lines of code"

**Slide Layout Suggestion**: Large numbers 1-8 with icons for each differentiator

---

## APPENDIX: FEATURE STATISTICS

**For reference / backup slides**:

### By the Numbers
- **12+ Model Providers** - Cloud, local, and multi-model gateways
- **4 Agent Types** - Single, Swarm, Graph, A2A
- **3 Conversation Managers** - Sliding Window, Summarizing, Null
- **3 Session Managers** - File, S3, Repository
- **8+ Stable Hook Events** - Plus 4 experimental
- **10+ Stream Event Types** - Raw and typed events
- **5 Guardrail Types** - Content, topic, word, PII, grounding
- **30+ PII Entity Types** - Comprehensive sensitive data detection
- **3 Tool Executors** - Sequential, Concurrent, Custom

### Coverage
- **Multi-modal**: Images, videos, documents, structured data
- **Protocols**: A2A, MCP, HTTP, stdio, SSE
- **Frameworks**: FastAPI, Starlette
- **Standards**: OpenTelemetry, JSON Schema, Pydantic
- **Cloud**: AWS (Bedrock, SageMaker, S3), GCP (Gemini), Azure (OpenAI)

---

*End of Feature Documentation for PowerPoint*
