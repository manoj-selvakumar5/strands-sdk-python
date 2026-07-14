# Strands Agents SDK

## About This Repository
- Official Strands Agents monorepo: Python SDK, TypeScript SDK, and docs site
- Model-agnostic agent framework with pluggable providers
- Apache 2.0 licensed

## My Role
I'm leading Strands Agents GTM (Go-To-Market). My work involves:
- Reviewing PRs to understand new features and changes
- Answering questions on the dedicated Strands Slack channel
- Analyzing SDK features in depth to understand them thoroughly
- Creating documentation and learning materials for myself and others

## Monorepo Structure
- `strands-py/` - Python SDK
  - `src/strands/` - Core SDK source code
  - `tests/` - Unit tests
  - `tests_integ/` - Integration tests
  - `docs/` - Python SDK documentation
- `strands-ts/` - TypeScript SDK (`src/`, `test/`, `examples/`, `docs/`)
- `site/` - Documentation site (Astro)
- `strandly/` - `@strands-agents/strandly` CLI
- `team/` - Team guidelines, tenets, and design decisions
- `test-infra/` - CDK-based test infrastructure

## Key SDK Components
Paths relative to `strands-py/src/strands/`:
- `agent/` - Main Agent class and conversation management
- `models/` - Model providers (Bedrock, Anthropic, OpenAI, etc.)
- `tools/` - Tool system with @tool decorator and MCP support
- `multiagent/` - Multi-agent orchestration (Swarm, Graph)
- `hooks/` - Hook system for lifecycle events
- `session/` - Session and state persistence
- `interrupt.py` - Interrupt mechanism
- `experimental/bidi/` - Bidirectional streaming (audio/real-time)

## Personal Documentation
The `personal/` directory contains my learning materials:
- `guides/` - Integration guides and BIDI deep-dives
- `notebooks/` - Jupyter notebooks and examples
- `feature-notes/` - Feature analyses and comparisons
- `presentations/` - Presentation materials
- `reviews/` - PR analysis work
- `Slack/` - Q&A documentation

## Preferences
- Use "Amazon Bedrock" not "AWS Bedrock"
- Keep SDK source unchanged when working on personal docs
