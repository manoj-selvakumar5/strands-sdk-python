# Strands Agents — Complete Capabilities Overview

## Quick Reference

| Models | Tools & Extensions | Multi-Agent | Observability & Safety | Deploy & Scale |
|--------|-------------------|-------------|------------------------|----------------|
| ✓ Amazon Bedrock | ✓ MCP native (1000s of tools) | ✓ Swarm orchestration | ✓ OpenTelemetry tracing | ✓ Python & TypeScript SDKs |
| ✓ OpenAI | ✓ Custom @tool decorator | ✓ Graph workflows | ✓ Strands Evaluations | ✓ Lambda / Fargate |
| ✓ Anthropic | ✓ Multimodal (images, video, docs) | ✓ A2A protocol | ✓ Guardrails (PII, content) | ✓ ECS / EKS |
| ✓ Google Gemini | ✓ Voice streaming | ✓ Tool-based handoffs | ✓ Hooks & lifecycle events | ✓ VPC endpoints |
| ✓ Mistral | ✓ Human-in-the-loop | ✓ Nested graphs | ✓ Session persistence | ✓ On-premises |
| ✓ Ollama / llama.cpp | ✓ Hot reload | ✓ Conditional routing | ✓ Structured output | ✓ Custom providers |
| ✓ LiteLLM | ✓ Async & streaming | | ✓ Prompt caching | |

---

## 1. Build Agents Your Way

- **Python & TypeScript SDKs** with simple, intuitive APIs
- **12+ Model Providers**: Amazon Bedrock (default), Anthropic, OpenAI, Google Gemini, Mistral, Ollama, LiteLLM, llama.cpp, LlamaAPI, Writer, SageMaker, custom
- **Deploy Anywhere**: Lambda, Fargate, ECS/EKS, containers, VPC endpoints, on-premises
- **Voice-Ready**: Bidirectional streaming for real-time voice agents
- **Structured Output**: Native Pydantic/Zod model support with automatic validation

## 2. Multi-Agent Orchestration

- **Swarm**: Self-organizing teams with shared context, autonomous collaboration, tool-based handoffs
- **Graph**: Directed workflows, conditional edges, cyclic support (feedback loops), nested graphs
- **A2A Protocol**: Agent discovery & communication, HTTP service wrapper, AgentCard publishing
- **Coordination**: Tool-based handoffs, conditional routing, shared context propagation

## 3. Powerful Tools & Extensions

- **@tool Decorator**: Pydantic/Zod schemas, type hints, docstrings, async/generator support
- **Tool Loading**: Functions, file paths, modules, directory watching with hot reload
- **MCP Native**: Full Model Context Protocol—connect to 1000s of pre-built tools
- **Execution Control**: Sequential/Concurrent executors, interrupts, human-in-the-loop
- **Multimodal**: Images (PNG/JPEG/GIF/WebP), Videos (MP4/MOV/MKV), Documents (PDF/CSV/DOCX/XLSX)

## 4. Production-Grade Observability & Safety

- **OpenTelemetry Native**: v1.37 semantic conventions, OTLP exporters, distributed tracing
- **Strands Evaluations**: Systematically evaluate agent behavior, measure improvements, deploy with confidence
- **Hooks System**: 8+ lifecycle events (BeforeModelCall, AfterToolCall, MessageAdded, etc.)
- **Bedrock Guardrails**: Content/Topic/Word/PII policies, contextual grounding
- **Security**: Content redaction, IAM-scoped tools, VPC endpoints

## 5. Developer Experience

- **Simple Invocation**: `agent("prompt")`, `agent.stream_async()`, `agent.tool.name()`
- **Hot Reload**: Automatic tool reloading during development
- **Agent State**: JSON-serializable persistent state across invocations
- **Memory Management**: Sliding window, summarization, session persistence (File/S3/custom)
- **Prompt Caching**: SystemContentBlock caching for improved performance
