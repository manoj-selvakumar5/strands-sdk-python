# A2A Protocol - Blog Research

**Date:** 2026-02-04
**Status:** Research complete, ready to write

## Title Ideas

- "A2A Protocol: Making Agents Talk Across Frameworks"
- "Breaking Agent Silos: Cross-System Interoperability"
- "Building Polyglot AI Systems: Strands Meets Other Frameworks"

## Why This Blog?

- A2A is Google open standard, not Strands-specific
- Enables cross-framework agent communication
- Enterprise appeal: multi-vendor systems
- Only mentioned in passing in existing blogs

## Key Code Locations

```
src/strands/multiagent/a2a/
├── a2a_agent.py           # A2AAgent client
├── executor.py            # StrandsA2AExecutor
├── server/
│   ├── a2a_server.py      # A2AServer setup
│   └── task_store.py      # InMemoryTaskStore
└── types/                 # AgentCard, Part conversions
```

Also: `docs/A2A.md` - comprehensive internal docs

## Blog Outline

### 1. What is A2A?
- Google open standard for agent interoperability
- Peer-to-peer communication without orchestrator
- Cross-framework: Strands + LangChain + AutoGen + custom
- Discovery via AgentCard

### 2. AgentCard Discovery

```json
// GET /.well-known/agent.json
{
  "name": "my-agent",
  "description": "Does X, Y, Z",
  "skills": [
    {"name": "search", "description": "Web search"}
  ],
  "url": "https://my-agent.example.com"
}
```

- Auto-extracted skills from tool registry
- Custom skill definitions for grouping
- Enables dynamic agent networks

### 3. A2AServer Setup

```python
from strands import Agent
from strands.multiagent.a2a import A2AServer

agent = Agent(tools=[search, calculator])
server = A2AServer(
    agent=agent,
    name="my-agent",
    http_url="https://my-agent.example.com"  # For load balancer
)
server.run(host="0.0.0.0", port=8000)
```

- FastAPI/Starlette integration
- `serve_at_root` for path-based routing
- Production deployment patterns

### 4. A2AAgent Client

```python
from strands.multiagent.a2a import A2AAgent

remote = A2AAgent(url="https://other-agent.example.com")
response = await remote.invoke("Please analyze this data")
```

- Calling remote agents
- Streaming responses (SSE)
- Error handling

### 5. Streaming Architecture
- `enable_a2a_compliant_streaming` flag
- Content type translation (Strands ContentBlock <-> A2A Part)
- Artifact tracking for files/images
- Server-Sent Events (SSE)

### 6. AWS SigV4 Authentication

```python
from strands.multiagent.a2a import SigV4HTTPXAuth

auth = SigV4HTTPXAuth(service="bedrock-agentcore", region="us-east-1")
remote = A2AAgent(url="https://agentcore.example.com", auth=auth)
```

- Required for Amazon Bedrock AgentCore
- Custom httpx auth class
- Common pitfalls (connection header issue)

### 7. Task Stores for Long-Running Operations
- `InMemoryTaskStore` (default)
- Custom implementations (Redis, DynamoDB)
- Queue management for async scenarios
- Push notification callbacks

### 8. Load Balancer Deployment
- `http_url` parameter for public discovery
- Path-based routing support (ALB, NLB)
- Multi-agent networks on Kubernetes

## Unique Angles

1. **Cross-framework demo** - Strands calling LangChain agent
2. **Enterprise architecture** - multi-vendor agent networks
3. **AWS integration** - SigV4 for AgentCore
4. **Production deployment** - load balancers, task stores

## Comparison: A2A vs Swarm vs Graph

| Aspect | A2A | Swarm | Graph |
|--------|-----|-------|-------|
| Scope | Distributed | Local | Local |
| Standard | Google open | SDK-native | SDK-native |
| Routing | Discovery | Autonomous | Deterministic |
| Framework | Cross-framework | Strands only | Strands only |

## Code Examples Needed

- [ ] Basic A2AServer setup
- [ ] A2AAgent client calling remote
- [ ] Streaming response handling
- [ ] SigV4 auth for AgentCore
- [ ] Custom TaskStore implementation

## References

- `docs/A2A.md` - comprehensive internal guide
- `personal/guides/2025-12-xx-a2a-server-client-guide.md` - existing notes
