# Upstream Changelog: v1.27.0 - v1.29.0

**Date:** 2026-03-10
**Context:** Research - tracking upstream changes (167 commits)

## New Features

- **Plugins system** - `@hook` and `@tool` decorators, Plugin Protocol → ABC, `plugins` parameter on Agent (#1733, #1734, #1740, #1741)
- **Agent Skills** (#1755) - new skills capability
- **Steering** - graduated from experimental to production (#1853, #1738, #1429)
- **CancellationToken** - graceful agent execution cancellation (#1772)
- **OpenAI Responses API** model implementation (#975)
- **Automatic prompt caching** for Amazon Bedrock (#1438)
- **A2A (Agent-to-Agent)** - A2AAgent class, AgentBase Protocol (#1441, #1126, #1615)
- **MCP Tasks** - basic support for MCP Tasks (#1475)
- **MCP Resources** - resource operations in MCP Tools (#1117)
- **Retry strategy** - configurable retry for model calls, hook-based retry (#1424, #1556, #1405)
- **Interrupts in graph** - hook-based, agent-based, and multiagent node interrupts (#1478, #1533, #1606)
- **Hooks improvements** - `add_hook` convenience method, union types support, invocation state, resume flag, retry mechanism (#1706, #1719, #1550, #1767)
- **Session manager** - optimization, dirty flag for skipping unnecessary persistence (#1829, #1803)
- **Concurrent invocation mode** parameter (#1707)
- **BidiAgent** - Nova Sonic 2 support, Gemini Live & OpenAI Realtime models (#1476, #1383)
- **Guardrails** - `guardrail_latest_message` option (#1224)
- **Structured output** - configurable prompt message (#1627)
- **Web/search result citations** support (#1344)

## Bug Fixes

- Cache point placement fix (#1821)
- Concurrency protection against parallel invocations (#1453)
- MCP session closure hang prevention (#1396)
- Various model fixes: Gemini (tool_use_id, reasoning, streaming), OpenAI (tool calls, context overflow), Mistral (usage metrics), LiteLLM
- Telemetry double-counting fix (#1327)
- Tool result serialization as JSON (#1752)
- Tool result truncation strategy improvement (#1756)
- Nullable semantics preservation for `Union[T, None]` params (#1584)
- Guardrail `latest_message` wrapping preserved after tool execution (#1658)
- Summary manager fix for structured output (#1805)
- Langfuse telemetry: latest semantic conventions, base URL check (#1768, #1826)

## Infrastructure/CI

- Multiple CI bumps (checkout v6, upload/download-artifact, setup-python, etc.)
- API breaking change check in workflow (#1348)
- Conventional commit workflow (#1645)
- Python 3.14 test coverage (#1178)
- Ruff pyupgrade for modernized syntax (#1336)

## Graduations (Experimental → Production)

- Steering (#1853)
- ToolProvider (#1567)
- Multiagent hook events (#1498)

## Other

- `pyaudio` made optional dependency (#1731)
- Security.md added (#1454)
- S3 location support for Document, Image, and Video (#1572)
- Custom client support for OpenAI and Gemini models (#1366)
- Gemini tools field with validation (#1050)
- `per_turn` parameter for SlidingWindowConversationManager (#1374)

## References

- Tags: v1.27.0, v1.28.0, v1.29.0
- Commits: 167
