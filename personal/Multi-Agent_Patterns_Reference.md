# Multi-Agent Patterns in Strands Agents

> Comprehensive reference for all multi-agent orchestration and coordination patterns in the Strands ecosystem

**Last Updated**: January 2026
**SDK Version**: strands-agents (Python)

---

## Quick Overview

The Strands Agents ecosystem provides **5 distinct multi-agent patterns**:

### Primary Orchestration Patterns
| Pattern | Type | Cycles | Parallel | Package | Best For |
|---------|------|--------|----------|---------|----------|
| **Swarm** | Autonomous collaboration | ✅ (with detection) | ❌ Sequential | SDK + tools | Creative problem-solving, exploration |
| **Graph** | Structured + LLM decisions | ✅ (with limits) | ✅ Branches | SDK + tools | Conditional logic, business processes |
| **Workflow** | Deterministic DAG | ❌ No cycles | ✅ Automatic | tools only | Repeatable pipelines, automation |

### Coordination Patterns
| Pattern | Type | Package | Best For |
|---------|------|---------|----------|
| **Agents as Tools** | Hierarchical delegation | SDK | Domain specialization, task routing |
| **A2A Protocol** | Cross-system bridge | SDK | Inter-agent communication, integration |

---

## 1. Swarm Pattern

**Location**: `src/strands/multiagent/swarm.py`
**Status**: Experimental

### Overview
Self-organizing collaborative agent teams where agents autonomously coordinate through tool-based handoffs. Agents share a working memory and decide which specialist to hand off to next.

### Key Characteristics
- **Control**: Autonomous (agents decide the path)
- **Coordination**: `handoff_to_agent` tool (auto-injected)
- **Execution**: Sequential handoffs between agents
- **State**: Shared context + full conversation history
- **Cycles**: Yes (with repetitive handoff detection)

### Core API

```python
from strands import Agent
from strands.multiagent import Swarm

# Create specialized agents
researcher = Agent(name="researcher", prompt="You research topics thoroughly")
analyst = Agent(name="analyst", prompt="You analyze data and trends")
writer = Agent(name="writer", prompt="You write polished reports")

# Create swarm
swarm = Swarm(
    nodes=[researcher, analyst, writer],
    entry_point=researcher,              # First agent to start
    max_handoffs=20,                     # Limit handoff count
    max_iterations=20,                   # Limit total executions
    execution_timeout=900.0,             # Total timeout (seconds)
    repetitive_handoff_detection_window=5  # Detect ping-ponging
)

# Execute
result = swarm("Research AI trends, analyze findings, and write a report")

# Async execution
result = await swarm.invoke_async(task)

# Streaming
async for event in swarm.stream_async(task):
    print(event)
```

### How Handoffs Work

Agents automatically receive a `handoff_to_agent` tool:
```python
# Agent calls this to hand off
handoff_to_agent(
    agent_name="analyst",
    message="Here are the research findings...",
    context={"sources": [...]}
)
```

### Shared Context

```python
# Agents can read/write shared knowledge
# Available via SharedContext in the swarm
# JSON-serializable values only
```

### When to Use Swarm

✅ **Best For**:
- Multidisciplinary problems requiring diverse expertise
- Exploratory tasks where the path isn't predetermined
- Collaborative brainstorming and synthesis
- Tasks benefiting from emergent agent coordination

❌ **Not Best For**:
- Strictly sequential processes
- When you need guaranteed execution order
- High-performance parallel processing

### Examples
- **Incident Response**: monitoring_agent → network_specialist → database_admin
- **Software Development**: researcher → architect → coder → reviewer
- **Content Creation**: researcher → fact_checker → writer → editor

---

## 2. Graph Pattern

**Location**: `src/strands/multiagent/graph.py`
**Status**: Experimental

### Overview
Structured, developer-defined flowchart where nodes (agents) execute based on dependency edges. The LLM can make path decisions at each node, and the graph supports conditional routing and cycles.

### Key Characteristics
- **Control**: Structured (developer defines topology, LLM decides paths)
- **Coordination**: Developer-defined edges with optional conditions
- **Execution**: Dependency-based, can branch in parallel
- **State**: Full shared transcript across all agents
- **Cycles**: Yes (feedback loops with execution limits)

### Core API

```python
from strands import Agent
from strands.multiagent import GraphBuilder

# Create agents
validator = Agent(name="validator", prompt="Validate input data")
processor = Agent(name="processor", prompt="Process valid data")
error_handler = Agent(name="error_handler", prompt="Handle errors")

# Build graph
builder = GraphBuilder()

# Add nodes
builder.add_node(validator, "validate")
builder.add_node(processor, "process")
builder.add_node(error_handler, "error")

# Add conditional edges
def if_valid(state):
    result = state.results.get("validate")
    return result and "valid" in str(result.result).lower()

builder.add_edge("validate", "process", condition=if_valid)
builder.add_edge("validate", "error", condition=lambda s: not if_valid(s))

# Configuration
builder.set_entry_point("validate")
builder.set_max_node_executions(10)  # For cyclic graphs
builder.set_execution_timeout(600.0)

# Build and execute
graph = builder.build()
result = graph("Process this customer data: {...}")

# Async execution
result = await graph.invoke_async(task)

# Streaming
async for event in graph.stream_async(task):
    print(event)
```

### Advanced Features

**Cyclic Graphs** (Feedback Loops):
```python
builder.add_node(writer, "write")
builder.add_node(reviewer, "review")
builder.add_node(improver, "improve")

builder.add_edge("write", "review")
builder.add_edge("review", "improve")
builder.add_edge("improve", "write")  # Cycle back

builder.set_max_node_executions(5)  # Prevent infinite loops
```

**Nested Graphs**:
```python
# Graphs can contain other Graphs or Swarms as nodes
inner_graph = builder1.build()
builder2.add_node(inner_graph, "subprocess")
```

**Node Reset Control**:
```python
builder.reset_on_revisit(True)   # Reset state when node revisited
builder.reset_on_revisit(False)  # Keep state across executions
```

### When to Use Graph

✅ **Best For**:
- Business processes with conditional branching
- Interactive customer support routing
- Data validation with error paths
- Iterative refinement workflows (write → review → improve)
- Complex decision trees

❌ **Not Best For**:
- Simple sequential tasks
- Highly autonomous, exploratory work
- When structure would constrain creativity

### Examples
- **Customer Support**: Route based on intent (order question → order_agent, technical issue → tech_support)
- **Content Pipeline**: write → review → (approved → publish | rejected → revise)
- **Data Processing**: validate → (valid → process | invalid → error_handler)

---

## 3. Workflow Pattern

**Location**: `strands-agents-tools` package (NOT in SDK)
**Status**: Available in tools package

### Overview
Pre-defined Task Graph (DAG) that executes as a single, non-conversational tool. Designed for repeatable, deterministic processes with automatic parallel execution of independent tasks.

### Key Characteristics
- **Control**: Deterministic (fixed by dependency graph)
- **Coordination**: Task dependencies (developer-defined)
- **Execution**: Parallel (automatic for independent tasks)
- **State**: Task-specific context (curated summaries, not full history)
- **Cycles**: NO (strictly DAG only)

### Core API

```python
from strands import Agent
from strands_tools import workflow

# Option 1: Use workflow as a tool
agent = Agent(
    name="coordinator",
    prompt="You coordinate data processing workflows",
    tools=[workflow]
)

# Agent can invoke workflow operations
result = agent("Create a data analysis workflow with these steps: extract, analyze, report")

# Workflow operations available:
# - action="create": Define workflow with tasks
# - action="start": Execute workflow
# - action="status": Check progress
# - action="pause": Pause execution
# - action="resume": Resume paused workflow
# - action="delete": Remove workflow

# Option 2: Sequential approach without workflow tool
researcher = Agent(prompt="Research specialist")
analyst = Agent(prompt="Analysis specialist")
writer = Agent(prompt="Report writer")

def data_pipeline(topic):
    research = researcher(f"Research {topic}")
    analysis = analyst(f"Analyze: {research}")
    report = writer(f"Write report: {analysis}")
    return report

result = data_pipeline("Q4 sales trends")
```

### Task Definition

When creating workflows, tasks are defined with:
- `task_id`: Unique identifier
- `description`: What the task does
- `system_prompt`: Agent prompt for this task
- `dependencies`: List of task_ids that must complete first
- `priority`: Execution priority

### Key Differences from Graph

| Aspect | Workflow | Graph |
|--------|----------|-------|
| Cycles | ❌ NO (DAG only) | ✅ YES (with limits) |
| LLM Path Decisions | ❌ NO (deterministic) | ✅ YES (at each node) |
| Parallel Execution | ✅ Automatic for independent tasks | ✅ Possible on branches |
| Context | Task-specific summaries | Full conversation transcript |
| Interface | Single tool invocation | Multi-node orchestrator |
| Error Handling | Systemic (halts downstream) | Controllable (error edges) |

### When to Use Workflow

✅ **Best For**:
- Automated data pipelines (extract → transform → load)
- Standard business processes (employee onboarding steps)
- Repeatable operations with clear dependencies
- When parallel execution can improve throughput
- Encapsulating complex processes as a single tool

❌ **Not Best For**:
- Processes requiring iteration or feedback loops
- Highly dynamic or exploratory tasks
- When you need full conversation history
- When LLM should decide the path

### Examples
- **Data Pipeline**: extract_data → [analyze_sales || analyze_trends] → generate_report
- **Employee Onboarding**: create_accounts || assign_training || send_welcome_email
- **ETL Process**: extract → transform → validate → load

---

## 4. Agents as Tools Pattern

**Location**: SDK via `@tool` decorator
**Status**: GA (Generally Available)

### Overview
Hierarchical multi-agent architecture where specialized agents are wrapped as callable tools for orchestrator agents. Creates clear orchestrator-specialist relationships.

### Key Characteristics
- **Control**: Hierarchical (orchestrator delegates to specialists)
- **Coordination**: Function calls via `@tool` decorator
- **Execution**: Nested invocations
- **Architecture**: Orchestrator → Specialist → Sub-specialist (unlimited depth)

### Core API

```python
from strands import Agent, tool

# Step 1: Create specialized agents as tools
@tool
def research_assistant(query: str) -> str:
    """Research topics and gather comprehensive information."""
    agent = Agent(
        name="researcher",
        prompt="You are a specialized research assistant with expertise in data gathering...",
        tools=[web_search, retrieve_docs]
    )
    response = agent(query)
    return str(response)

@tool
def product_recommendation_assistant(query: str) -> str:
    """Provide personalized product recommendations."""
    agent = Agent(
        name="product_specialist",
        prompt="You are a product recommendation expert...",
        tools=[search_products, get_reviews, check_inventory]
    )
    response = agent(query)
    return str(response)

@tool
def trip_planning_assistant(query: str) -> str:
    """Plan trips and provide travel recommendations."""
    agent = Agent(
        name="travel_planner",
        prompt="You are a travel planning specialist...",
        tools=[get_weather, search_flights, find_hotels]
    )
    response = agent(query)
    return str(response)

# Step 2: Create orchestrator agent
orchestrator = Agent(
    name="orchestrator",
    prompt="""You are a helpful assistant that routes queries to specialized agents.

    Use research_assistant for general research queries.
    Use product_recommendation_assistant for shopping and product queries.
    Use trip_planning_assistant for travel and trip planning queries.

    You can call multiple specialists if needed to provide comprehensive answers.""",
    tools=[research_assistant, product_recommendation_assistant, trip_planning_assistant]
)

# Execute
result = orchestrator("I need hiking boots for a trip to Patagonia next month")
# Orchestrator will:
# 1. Call trip_planning_assistant to get weather/terrain info for Patagonia
# 2. Call product_recommendation_assistant to suggest appropriate boots
# 3. Synthesize both responses into comprehensive answer
```

### Execution Flow

```
User Query: "I need hiking boots for Patagonia next month"
    ↓
Orchestrator Agent
    ├─→ trip_planning_assistant(query="Patagonia weather conditions next month")
    │   └─→ Returns: "Cold, wet, rocky terrain. Temperatures 0-10°C..."
    │
    └─→ product_recommendation_assistant(query="hiking boots for cold wet rocky terrain")
        └─→ Returns: "Waterproof boots with ankle support, insulated..."
    ↓
Orchestrator synthesizes responses
    ↓
Final Answer to User
```

### Best Practices

1. **Clear Tool Descriptions**: Write detailed docstrings
   ```python
   @tool
   def specialist(query: str) -> str:
       """Detailed description of what this specialist does and when to use it."""
   ```

2. **Focused System Prompts**: Keep each specialist narrowly scoped
   ```python
   prompt="You ONLY handle X. Refuse queries about Y or Z."
   ```

3. **Type Safety**: Use proper type hints
   ```python
   @tool
   def specialist(query: str, context: dict[str, Any]) -> str:
       ...
   ```

4. **Consistent Response Format**: Return structured, parseable responses

### When to Use Agents as Tools

✅ **Best For**:
- Domain-specific expertise (legal, medical, technical specialists)
- Task routing based on user intent
- Hierarchical problem decomposition
- Combining multiple perspectives on a single query
- Clear separation of concerns

❌ **Not Best For**:
- Peer collaboration scenarios
- When agents need to negotiate or coordinate directly
- Circular dependencies between specialists

### Examples
- **Customer Service**: orchestrator → [billing_specialist, technical_support, order_tracking]
- **Content Creation**: orchestrator → [researcher, fact_checker, writer, editor]
- **Healthcare**: orchestrator → [symptom_analyzer, prescription_assistant, appointment_scheduler]

---

## 5. A2A (Agent-to-Agent) Protocol

**Location**: `src/strands/multiagent/a2a/`
**Status**: Experimental

### Overview
Enables standardized communication between agents using the Agent-to-Agent (A2A) protocol. Makes Strands Agents compatible with other A2A-compliant agent systems.

### Key Characteristics
- **Control**: Protocol-based (HTTP/REST)
- **Coordination**: RESTful API endpoints
- **Discovery**: AgentCard for metadata publication
- **Interoperability**: Works with any A2A-compliant system

### Core API

```python
from strands import Agent
from strands.multiagent.a2a import A2AServer

# Create a Strands agent
agent = Agent(
    name="my_agent",
    prompt="You are a helpful assistant specializing in data analysis"
)

# Wrap it with A2A server
server = A2AServer(
    agent=agent,
    host="127.0.0.1",
    port=9000,
    http_url="https://my-agent.example.com",  # Public URL for discovery
    version="1.0.0",
    skills=[...]  # Optional: Define agent skills
)

# Start server
# Now other A2A-compliant agents can discover and communicate with your agent
```

### A2A Protocol Features

**1. Agent Discovery**:
- `public_agent_card` property exposes agent metadata
- Skills, capabilities, and contact information
- Other agents can discover via standard A2A endpoints

**2. Standardized Communication**:
- REST API for agent-to-agent requests
- Streaming support for real-time responses
- Task-based request/response model

**3. Task Management**:
- Task store for persistence
- Status tracking and updates
- Artifact handling

**4. Push Notifications**:
- Optional push notification system
- Real-time updates on task progress

### When to Use A2A

✅ **Best For**:
- Cross-system agent communication
- Building agent marketplaces or directories
- Integrating with external A2A-compliant agents
- Standardized agent APIs
- Multi-vendor agent ecosystems

❌ **Not Best For**:
- Internal-only agent coordination
- Simple tool-based delegation
- When protocol overhead isn't justified

### Examples
- **Agent Marketplace**: Publish agents for discovery by other systems
- **Federated Agents**: Agents from different organizations collaborating
- **Third-Party Integration**: Integrate with external A2A agent services

---

## Pattern Comparison Table

### Primary Orchestration Patterns

| Aspect | Swarm | Graph | Workflow |
|--------|-------|-------|----------|
| **Control Model** | Autonomous | Structured + LLM | Deterministic |
| **Execution** | Sequential handoffs | Conditional branching | Parallel DAG |
| **Cycles** | ✅ (with detection) | ✅ (with limits) | ❌ NO |
| **Parallel** | ❌ Sequential | ✅ Branches | ✅ Automatic |
| **Context** | Shared + history | Full transcript | Task summaries |
| **Path Decision** | Agents decide | LLM at nodes | Fixed by DAG |
| **Error Handling** | Agent handoff | Error edges | Halts downstream |
| **Package** | SDK + tools | SDK + tools | tools only |
| **Interface** | MultiAgentBase | MultiAgentBase | Tool |
| **Best For** | Exploration | Business logic | Pipelines |

### Coordination Patterns

| Aspect | A2A Protocol | Agents as Tools |
|--------|--------------|-----------------|
| **Mechanism** | HTTP/REST API | @tool decorator |
| **Scope** | Cross-system | Internal hierarchy |
| **Discovery** | AgentCard | Function signature |
| **Best For** | Integration | Specialization |

---

## Decision Guide

### Choose Swarm When:
- Problem requires diverse perspectives
- Path isn't predetermined
- Agents should self-organize
- Collaborative exploration is key
- Example: Multi-disciplinary incident response

### Choose Graph When:
- You need conditional branching
- Business process with decision points
- Iterative refinement (cycles)
- Clear dependency structure
- Example: Customer support routing with escalation paths

### Choose Workflow When:
- Process is repeatable and deterministic
- Independent tasks can run in parallel
- No cycles or iteration needed
- Want to encapsulate as a single tool
- Example: ETL pipeline or automated onboarding

### Choose Agents as Tools When:
- Clear domain specialists
- Hierarchical task delegation
- Orchestrator needs to route to specialists
- Want separation of concerns
- Example: Customer service with specialized departments

### Choose A2A When:
- Need cross-system communication
- Building agent marketplace
- Standardized protocol required
- External agent integration
- Example: Federated multi-vendor agent ecosystem

---

## Combining Patterns

Patterns can be combined for powerful architectures:

```python
# Example: Swarm with specialized agent tools
@tool
def legal_specialist(query: str) -> str:
    """Legal expertise."""
    return str(legal_agent(query))

@tool
def technical_specialist(query: str) -> str:
    """Technical expertise."""
    return str(tech_agent(query))

# Each swarm agent can have specialist tools
researcher = Agent(prompt="...", tools=[legal_specialist, technical_specialist])
analyst = Agent(prompt="...", tools=[legal_specialist, technical_specialist])

swarm = Swarm([researcher, analyst])
```

```python
# Example: Graph with Workflow as a node
workflow_tool = workflow  # From strands_tools

workflow_agent = Agent(tools=[workflow_tool])

builder = GraphBuilder()
builder.add_node(input_validator, "validate")
builder.add_node(workflow_agent, "process")  # Workflow as a graph node
builder.add_node(output_formatter, "format")
```

---

## Shared Features (Swarm & Graph)

Both orchestration patterns in the SDK share:

### Invocation State
```python
shared_state = {
    "user_id": "user123",
    "session_id": "sess456",
    "database": db_connection
}

# Works for both patterns
result = swarm(task, invocation_state=shared_state)
result = graph(task, invocation_state=shared_state)
```

### Streaming Events
```python
async for event in swarm.stream_async(task):
    # multi_agent_node_start
    # multi_agent_node_stream
    # multi_agent_handoff (swarm only)
    # multi_agent_node_stop
    # result
```

### Session Persistence
```python
from strands.session import FileSessionManager

session_manager = FileSessionManager(session_dir="./sessions")

swarm = Swarm(nodes=[...], session_manager=session_manager)
graph = builder.set_session_manager(session_manager).build()
```

### Hooks Integration
```python
from strands.hooks import HookProvider

class MyHooks(HookProvider):
    def before_node_call(self, event):
        # Cancel node if needed
        event.cancel_node = True

swarm = Swarm(nodes=[...], hooks=[MyHooks()])
```

### Interrupts
```python
# User can interrupt execution
# Resume from interrupt state
```

---

## Key Files Reference

### SDK Files
```
src/strands/
├── multiagent/
│   ├── base.py              # MultiAgentBase, NodeResult, Status
│   ├── swarm.py             # Swarm pattern
│   ├── graph.py             # Graph pattern, GraphBuilder
│   └── a2a/
│       ├── executor.py      # StrandsA2AExecutor
│       └── server.py        # A2AServer
├── tools/
│   └── decorator.py         # @tool for Agents as Tools
└── types/
    └── tools.py             # AgentTool base class
```

### External Packages
```
strands-agents-tools/
└── workflow.py              # Workflow pattern
```

---

## Resources

### Documentation
- Graph: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/graph/
- Swarm: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/swarm/
- Workflow: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/workflow/
- Agents as Tools: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agents-as-tools/
- A2A: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agent-to-agent/

### Repositories
- SDK Python: https://github.com/strands-agents/sdk-python
- Tools: https://github.com/strands-agents/tools
- Samples: https://github.com/strands-agents/samples
- Docs: https://github.com/strands-agents/docs

### Samples
- `swarm`: Basic swarm example
- `finance-swarm`: Financial analysis swarm
- `graph`: Basic graph example
- `data-warehouse-optimizer`: Graph with conditional logic
- `agent-as-tool`: Agents as tools pattern
- `personal-assistant`: Combined patterns
- `a2a-protocol`: A2A protocol example

---

**Note**: This reference is based on the Strands Agents SDK as of January 2026. Swarm, Graph, and A2A patterns are marked as Experimental. Agents as Tools is GA. Workflow is available in the strands-agents-tools package.
