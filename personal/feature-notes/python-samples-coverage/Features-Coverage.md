# SDK Features Coverage

> 95+ features tracked | ~37% have dedicated samples

Back to [README.md](README.md) | See also [Samples-Catalog.md](Samples-Catalog.md)

---

## Core Features

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Core Agent** | Agent class (create, __call__) | GA | first-agent, all samples |
| **Core Agent** | stream_async() | GA | streaming, playground |
| **Core Agent** | invoke_async() | GA | *None* |
| **Core Agent** | structured_output() | GA | *None* |
| **Core Agent** | Agent properties (system_prompt, tool_names, messages) | GA | *None dedicated* |
| **Model Providers** | BedrockModel | GA | first-agent, most samples |
| **Model Providers** | OpenAIModel | GA | openai-model |
| **Model Providers** | OllamaModel | GA | ollama-model |
| **Model Providers** | AnthropicModel, GeminiModel | GA | *None* |
| **Model Providers** | LiteLLMModel, MistralModel, SageMakerModel | GA | *None* |
| **Model Providers** | LlamaCppModel, LlamaAPIModel, WriterModel | GA | *None* |

---

## Tools & MCP

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Tools** | @tool decorator | GA | first-agent, custom-tools |
| **Tools** | ToolRegistry, ToolLoader | GA | *None dedicated* |
| **Tools** | ToolWatcher (hot reload) | GA | research-agent |
| **Tools** | Executors (Sequential, Concurrent) | GA | *None* |
| **Tools** | ToolContext, StructuredOutputTool, PythonAgentTool | GA | *None* |
| **MCP** | MCPClient | GA | mcp-tools, aws-assistant-mcp |
| **MCP** | MCPAgentTool | GA | *None* |

---

## Multi-Agent & Orchestration

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Multi-Agent** | Agent-as-Tool | GA | agent-as-tool, personal-assistant |
| **Multi-Agent** | Swarm | Experimental | swarm, finance-swarm |
| **Multi-Agent** | Graph | Experimental | graph, data-warehouse-optimizer |
| **Multi-Agent** | A2A Protocol | Experimental | a2a-protocol, native-a2a |

---

## Conversation & Session

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Conversation** | ConversationManagers (Null, SlidingWindow, Summarizing) | GA | *None* |
| **Session** | SessionManagers (File, S3, Repository) | GA | *None* |
| **Interrupts** | Interrupt class, InterruptException, resume | GA | *None* |

---

## Hooks System

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Hooks** | HookRegistry, HookProvider | GA | *None* |
| **Hooks** | Events: AgentInitialized, BeforeInvocation, AfterInvocation | GA | *None* |
| **Hooks** | Events: MessageAdded, BeforeToolCall, AfterToolCall | GA | *None* |
| **Hooks** | Events: BeforeModelCall, AfterModelCall | GA | *None* |

---

## Streaming & BiDi

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Streaming** | Text streaming | GA | streaming |
| **Streaming** | Stream events (Text, ToolUse, Citation, Reasoning) | GA | *None dedicated* |
| **BiDi** | BidiAgent | Experimental | bidi-streaming |
| **BiDi** | BidiNovaSonicModel | Experimental | nova-sonic |
| **BiDi** | BidiGeminiLiveModel, BidiOpenAIRealtimeModel | Experimental | *None* |
| **BiDi** | BidiTextIO, BidiAudioIO | Experimental | *None dedicated* |

---

## Content & Media

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Content** | ImageContent | GA | email-assistant |
| **Content** | DocumentContent | GA | medical-docs |
| **Content** | VideoContent | GA | *None* |
| **Content** | CachePoint, ReasoningContentBlock, Citations | GA | *None* |

---

## Guardrails & Safety

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Guardrails** | Bedrock Guardrails, GuardrailConfig | GA | guardrails |
| **Guardrails** | Third-party (NeMo, GuardRails AI, Llama Firewall) | GA | guardrails (integrations) |

---

## Observability & Handlers

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Observability** | Telemetry, Tracing, Metrics | GA | observability, arize |
| **Observability** | Trace class | GA | *None* |
| **Handlers** | PrintingCallbackHandler, null_callback_handler | GA | *None* |
| **Exceptions** | ModelThrottled, ContextWindowOverflow | GA | *None* |

---

## Evaluations & Deployment

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Evaluations** | Built-in evaluators | GA | built-in-evaluators |
| **Evaluations** | Custom evaluators, Dataset gen, Trajectory, A/B | GA | multiple eval samples |
| **Deployment** | AWS Lambda | GA | lambda |
| **Deployment** | AWS Fargate | GA | fargate, streamlit-template |
| **Deployment** | Bedrock AgentCore | GA | agentcore |

---

## Experimental Features

| Category | Feature | Status | Sample(s) |
|----------|---------|--------|-----------|
| **Steering** | SteeringHandler, LLMSteeringHandler, SteeringContext | Experimental | *None* |
| **Experimental** | config_to_agent(), ToolProvider interface | Experimental | *None* |

---

# Priority Gaps: Features Needing Samples

## High Priority (Core features, essential for adoption)

| Feature | Why Important | Suggested Sample |
|---------|---------------|------------------|
| **structured_output()** | Core workflow for type-safe responses | "Type-safe agent output" tutorial |
| **ConversationManagers** | Essential for production long conversations | "Managing conversation history" tutorial |
| **Hooks system** | Extensibility, logging, monitoring | "Custom logging with hooks" tutorial |
| **Interrupts** | Human-in-the-loop workflows | "Human approval workflows" tutorial |
| **SessionManagers** | Production persistence requirement | "Persistent sessions with S3" tutorial |

## Medium Priority (Popular providers/features)

| Feature | Why Important | Suggested Sample |
|---------|---------------|------------------|
| **AnthropicModel** | Popular provider (Claude direct) | "Using Claude without Bedrock" tutorial |
| **GeminiModel** | Popular provider | "Using Gemini models" tutorial |
| **LiteLLMModel** | Multi-provider routing | "Switch providers dynamically" tutorial |
| **ToolExecutors** | Performance tuning | "Concurrent tool execution" tutorial |
| **Stream events** | Real-time UI updates | "Building streaming UIs" tutorial |

## Lower Priority (Advanced/Niche)

| Feature | Why Important | Notes |
|---------|---------------|-------|
| BidiGemini/OpenAI | Provider-specific BiDi | When demand increases |
| Steering | Experimental | Wait for GA |
| VideoContent | Specialized use case | When adoption grows |
| Handlers | Debugging utility | Documentation may suffice |
