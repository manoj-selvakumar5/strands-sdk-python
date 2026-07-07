# Hooks & Sessions - Blog Research

**Date:** 2026-02-04
**Status:** Research complete, ready to write

## Title Ideas

**Hooks:**
- "Human-in-the-Loop Agents with Hooks"
- "Building Production Agents: Hooks Deep Dive"
- "Observe, Modify, Control: The Strands Hooks System"

**Sessions:**
- "Production Agent Persistence: From Files to S3"
- "Stateful Agents: Session Management Deep Dive"

## Why This Blog?

- `docs/HOOKS.md` is only 25 lines
- Session persistence completely undocumented
- Critical for production deployments
- Enables compliance, cost control, reliability

---

## HOOKS SYSTEM

### Key Code Locations

```
src/strands/hooks/
├── hook_provider.py       # HookProvider protocol
├── registry.py            # Callback registration
└── events/
    ├── agent_events.py    # 9 agent-level events
    └── multi_agent_events.py  # 5 multi-agent events
```

### Available Events (14 total)

**Agent Lifecycle:**
1. `AgentInitializedEvent` - post-construction (sync only)
2. `BeforeInvocationEvent` - pre-request (writable: messages)
3. `AfterInvocationEvent` - post-request
4. `MessageAddedEvent` - message added
5. `BeforeModelCallEvent` - pre-inference
6. `AfterModelCallEvent` - post-inference (writable: retry)
7. `BeforeToolCallEvent` - pre-execution (writable: selected_tool, cancel_tool, interruptible)
8. `AfterToolCallEvent` - post-execution (writable: result, retry)

**Multi-Agent:**
9. `MultiAgentInitializedEvent`
10. `BeforeMultiAgentInvocationEvent`
11. `AfterMultiAgentInvocationEvent`
12. `BeforeNodeCallEvent` (interruptible)
13. `AfterNodeCallEvent`

### Blog Outline (Hooks)

#### 1. Event System Overview
- HookProvider protocol
- Callback registration
- Event lifecycle timing

#### 2. Human-in-the-Loop: Approval Gates

```python
def approval_hook(event: BeforeToolCallEvent):
    if event.tool.name == "execute_trade":
        # Pause for human approval
        event.interrupt(
            name="trade_approval",
            reason="Trade requires manual approval"
        )

agent = Agent(hooks=[approval_hook])
```

- `interrupt()` raises `InterruptException`
- Unique interrupt ID for resumption
- Real use case: financial decisions

#### 3. Intelligent Retries

```python
def quality_gate(event: AfterModelCallEvent):
    if len(event.response.text) < 100:
        event.retry = True  # Retry with same inputs

def tool_retry(event: AfterToolCallEvent):
    if "rate_limit" in str(event.result):
        event.retry = True
```

- Quality gates (response validation)
- Tool error recovery
- **Caveat:** Streaming events from discarded attempts already emitted

#### 4. Tool Swapping at Runtime

```python
def cost_optimizer(event: BeforeToolCallEvent):
    if event.selected_tool.name == "expensive_api":
        event.selected_tool = cheaper_fallback_tool
```

- Dynamic routing based on context
- Fallback mechanisms
- Cost optimization patterns

#### 5. Reverse Callback Ordering
- `After*` events invoke callbacks in reverse order
- Enables proper teardown (like stack unwinding)
- Example: save session, then cleanup logger, then release locks

---

## SESSION PERSISTENCE

### Key Code Locations

```
src/strands/session/
├── session_manager.py     # SessionManager abstract
├── repository_session_manager.py  # Orchestration
├── file_session_manager.py        # Filesystem backend
└── s3_session_manager.py          # S3 backend
```

### Data Model

```
Session
├── session_id
├── session_type
└── created_at, updated_at

Agent (per session)
├── agent_id
├── state (user dict)
├── conversation_manager_state
├── _internal_state (interrupts)
└── messages/
    ├── message_0.json
    ├── message_1.json
    └── ...
```

### Blog Outline (Sessions)

#### 1. SessionManager Architecture
- Abstract `HookProvider` design
- Hooks fire at: init, message add, after invocation
- Automatic sync after state changes

#### 2. FileSessionManager Setup

```python
from strands.session import FileSessionManager

session = FileSessionManager(
    session_id="user-123-session",
    agent_id="assistant"
)
agent = Agent(session_manager=session)
```

- Default: `~/.tmp/strands/sessions/`
- Atomic writes (temp file + os.replace)
- Crash-safe persistence

#### 3. S3SessionManager Setup

```python
from strands.session import S3SessionManager

session = S3SessionManager(
    session_id="user-123-session",
    agent_id="assistant",
    bucket="my-sessions-bucket",
    prefix="strands/"
)
```

- Concurrent message loading (ThreadPoolExecutor)
- Pagination for large histories
- IAM permissions required

#### 4. Message History Repair
- Orphaned toolUse (no result) detection
- Orphaned toolResult (no use) detection
- Auto-generates missing tool result blocks
- Preserves conversation structure

#### 5. Multi-Agent Sessions
- Separate `create_multi_agent()` / `sync_multi_agent()`
- `MultiAgentBase.serialize_state()` / `deserialize_state()`
- Graph/Swarm state persistence

#### 6. Conversation Manager Integration
- Sessions aware of message pruning
- `conversation_manager.removed_message_count` tracks offset
- `prepend_messages` from summarization

#### 7. Message Redaction

```python
# Compliance-friendly editing
message.redact_message = "[REDACTED: contains PII]"
```

- `SessionMessage.redact_message` field
- Returns redacted content on restore

---

## Unique Angles

**Hooks:**
- Cost control via tool interception
- Compliance via input validation
- Observability without modifying SDK

**Sessions:**
- Production reliability patterns
- Multi-agent state coordination
- Crash recovery with atomic writes

## Code Examples Needed

- [ ] Approval gate with interrupt
- [ ] Quality gate retry logic
- [ ] Tool swapping for cost
- [ ] FileSessionManager basic setup
- [ ] S3SessionManager with concurrent loading
- [ ] Multi-agent session coordination

## References

- `docs/HOOKS.md` - minimal existing docs
- `personal/feature-notes/2026-02-01-hooks-system-reference.md` - detailed notes
- `personal/feature-notes/2026-02-04-hooks-vs-callback-handler-use-cases.md` - comparison
