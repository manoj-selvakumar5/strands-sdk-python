# Python Samples Catalog

> 63 samples in the [strands-agents/samples](https://github.com/strands-agents/samples) repository

Back to [README.md](README.md) | See also [Features-Coverage.md](Features-Coverage.md)

---

## Tutorials (17 samples)

| Sample | Level | Description | Key Features |
|--------|-------|-------------|--------------|
| first-agent | Beginner | Create first agent with default Bedrock model | Agent, BedrockModel, @tool |
| ollama-model | Beginner | Use Ollama for local model inference | OllamaModel |
| openai-model | Beginner | Configure OpenAI GPT models | OpenAIModel |
| aws-services | Intermediate | Connect to Bedrock KB and DynamoDB | BedrockModel, AWS SDK, RAG |
| mcp-tools | Intermediate | Integrate MCP servers | MCPClient |
| custom-tools | Beginner | Create custom tools with @tool | @tool decorator |
| streaming | Intermediate | Stream responses with callbacks | stream_async(), callbacks |
| guardrails | Intermediate | Bedrock Guardrails integration | Guardrails |
| memory | Intermediate | Build persistent agents | Memory tools |
| observability | Intermediate | Add tracing and metrics | Telemetry, tracing |
| bidi-streaming | Advanced | Real-time bidirectional streaming | BidiAgent |
| agent-as-tool | Intermediate | Use agents as tools | Agent composition |
| swarm | Advanced | Self-organizing agent swarm | Swarm (Experimental) |
| graph | Advanced | DAG-based orchestration | Graph (Experimental) |
| lambda | Advanced | Deploy to AWS Lambda | Lambda |
| fargate | Advanced | Deploy to AWS Fargate | Fargate, containers |
| agentcore | Advanced | Deploy to Bedrock AgentCore | AgentCore |

---

## Real-World Samples (18 samples)

| Sample | Level | Description | Key Features |
|--------|-------|-------------|--------------|
| restaurant-assistant | Intermediate | Multi-restaurant reservations | Agent, @tool, conversation |
| scrum-master | Intermediate | JIRA-integrated agile assistant | Agent, MCP, structured output |
| aws-assistant-mcp | Intermediate | AWS cloud operations assistant | MCPClient |
| startup-advisor | Intermediate | Business advisory agent | MCPClient |
| personal-assistant | Advanced | Multi-agent with calendar, web, dev tools | Multi-agent |
| code-assistant | Intermediate | AI coding companion | Agent, code tools |
| whatsapp-fintech | Advanced | WhatsApp fintech bot | Messaging integration |
| data-warehouse-optimizer | Advanced | Multi-agent SQL optimizer | Multi-agent, SQL |
| finance-swarm | Advanced | Equity research swarm | Swarm, financial tools |
| email-assistant | Advanced | Email with RAG and image gen | Multi-modal, ImageContent |
| personal-finance | Intermediate | Budget analysis | Memory, multi-agent |
| medical-docs | Advanced | Medical document extraction | DocumentContent |
| aws-audit | Intermediate | AWS compliance checker | AWS tools |
| research-agent | Advanced | Autonomous research with hot-reload | ToolWatcher |
| airline-assistant | Advanced | 4 orchestration strategies | ReAct, REWOO patterns |
| lambda-error-analysis | Advanced | Lambda error diagnostics | Event-driven |
| financial-advisor | Advanced | Wealth advisory system | Financial tools |
| ads-crypto | Advanced | Ad creation with crypto payments | Payment integration |

---

## Integrations (12 samples)

| Sample | Level | Description | Key Features |
|--------|-------|-------------|--------------|
| a2a-protocol | Advanced | Agent-to-agent protocol | A2A (Experimental) |
| native-a2a | Advanced | Native A2A support | A2A (Experimental) |
| data-processing | Advanced | Glue, Athena, EMR interface | AWS data tools |
| neptune | Advanced | Graph database integration | Neptune |
| arize | Intermediate | Arize observability | OpenInference |
| aurora-dsql | Advanced | Aurora distributed SQL | Aurora DSQL |
| nova-act | Advanced | Browser automation | Nova Act |
| nova-sonic | Advanced | Real-time voice | BidiNovaSonicModel |
| supabase | Intermediate | Supabase backend | MCPClient |
| tavily | Intermediate | Web search APIs | Tavily tools |
| guardrails | Intermediate | NeMo, GuardRails AI, Llama Firewall | Third-party guardrails |
| zep-ai | Intermediate | Graph-based memory | Zep integration |

---

## UX Demos (5 samples)

| Sample | Level | Description | Key Features |
|--------|-------|-------------|--------------|
| streamlit-template | Advanced | Streamlit with Cognito, ECS | Agent, Streamlit |
| video-games-sales | Intermediate | SQL generation and visualization | SQL tools |
| hvac-analytics | Advanced | HVAC sensor analytics | Code generation |
| triage-agent | Advanced | Medical AI triage (25+ tools) | MCPClient, session |
| playground | Intermediate | Interactive SDK playground | Multiple features |

---

## Agentic RAG (3 samples)

| Sample | Level | Description | Key Features |
|--------|-------|-------------|--------------|
| corrective-rag | Advanced | Query refinement with fallback | RAG, web search |
| adaptive-rag | Advanced | Self-correcting SQL generation | SQL, self-correction |
| hybrid-rag | Advanced | OpenSearch + Redshift | Hybrid RAG |

---

## Edge & Robotics (1 sample)

| Sample | Level | Description | Key Features |
|--------|-------|-------------|--------------|
| spot-agent | Advanced | Boston Dynamics Spot control | Physical AI |

---

## Evaluations (7 samples)

| Sample | Level | Description | Key Features |
|--------|-------|-------------|--------------|
| built-in-evaluators | Intermediate | Built-in evaluation tools | Eval framework |
| custom-evaluators | Intermediate | Custom evaluation functions | Custom evaluators |
| dataset-generation | Intermediate | Generate test datasets | Dataset generation |
| trajectory-eval | Advanced | Agent trajectory evaluation | Trajectory analysis |
| multi-turn-sim | Advanced | Multi-turn conversation simulation | Multi-turn testing |
| multi-agent-eval | Advanced | Multi-agent system evaluation | Multi-agent eval |
| ab-testing | Advanced | A/B testing models | A/B testing |
