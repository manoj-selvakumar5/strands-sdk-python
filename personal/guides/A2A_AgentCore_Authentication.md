# A2A Protocol + Amazon Bedrock AgentCore: Authentication Guide

## The Challenge

When using `A2AClientToolProvider` from `strands-agents-tools` with Amazon Bedrock AgentCore, you'll encounter 403 Forbidden errors because:

- **A2AClientToolProvider** makes standard HTTP requests (no auth)
- **AgentCore** requires AWS SigV4 authentication on all endpoints

```
A2AClientToolProvider                    AgentCore Gateway
        |                                        |
        |  GET /.well-known/agent-card.json      |
        |--------------------------------------->|
        |                                        |
        |  403 Forbidden (no SigV4 signature)    |
        |<---------------------------------------|
```

This affects both:
1. **Discovery** - GET requests to fetch agent cards
2. **Messaging** - POST requests to send A2A messages

---

## The Solution: SigV4 Auth via httpx_client_args

`A2AClientToolProvider` accepts `httpx_client_args` which can include a custom auth handler. We create an `httpx.Auth` subclass that signs requests with AWS SigV4.

### SigV4HTTPXAuth Class

```python
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


class SigV4HTTPXAuth(httpx.Auth):
    """
    httpx Auth handler that signs requests with AWS SigV4.

    This enables A2AClientToolProvider to authenticate with
    Amazon Bedrock AgentCore endpoints.
    """

    def __init__(self, credentials, service: str, region: str):
        """
        Args:
            credentials: botocore Credentials object from session.get_credentials()
            service: AWS service name (use "bedrock-agentcore")
            region: AWS region (e.g., "us-east-1")
        """
        self.signer = SigV4Auth(credentials, service, region)

    def auth_flow(self, request: httpx.Request):
        # IMPORTANT: Remove 'connection' header before signing
        # This header causes SignatureDoesNotMatch errors on the server
        headers = dict(request.headers)
        headers.pop("connection", None)

        # Create AWS request object for signing
        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=headers
        )

        # Add SigV4 signature headers
        self.signer.add_auth(aws_request)

        # Update original request with signed headers
        request.headers.update(aws_request.headers)
        yield request
```

### Using with A2AClientToolProvider

```python
import boto3
from strands import Agent
from strands.models import BedrockModel
from strands_tools.a2a_client import A2AClientToolProvider


def create_coordinator(market_research_url: str) -> Agent:
    """
    Create an agent that can call other agents via A2A on AgentCore.

    Args:
        market_research_url: AgentCore invoke URL, e.g.:
            https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{encoded_arn}/invocations
    """
    # Get credentials from boto3 session
    session = boto3.Session()
    credentials = session.get_credentials()
    region = session.region_name or "us-east-1"

    # Create A2AClientToolProvider with SigV4 authentication
    a2a_provider = A2AClientToolProvider(
        known_agent_urls=[market_research_url],
        httpx_client_args={
            "auth": SigV4HTTPXAuth(credentials, "bedrock-agentcore", region)
        }
    )

    return Agent(
        name="Investment_Coordinator",
        system_prompt="You are an investment research coordinator...",
        model=BedrockModel(model_id="us.amazon.nova-lite-v1:0"),
        tools=a2a_provider.tools,
    )
```

---

## URL Format

AgentCore URLs follow this pattern:

```
https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{url_encoded_arn}/invocations
```

Where `{url_encoded_arn}` has colons and slashes percent-encoded:
- `:` becomes `%3A`
- `/` becomes `%2F`

Example:
```
arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent
                    ↓ URL encoded
arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A123456789012%3Aruntime%2Fmy-agent
```

---

## Common Errors

### SignatureDoesNotMatch

```
SignatureDoesNotMatch: The request signature we calculated does not match
the signature you provided. Check your AWS Secret Access Key and signing method.
```

**Cause**: The `connection` header is included in signing but stripped by proxies.

**Fix**: Remove `connection` header before signing (shown in SigV4HTTPXAuth above).

### 403 Forbidden

**Cause**: No SigV4 signature on request.

**Fix**: Use SigV4HTTPXAuth with httpx_client_args.

---

## Alternative: boto3 Direct Invoke

If you don't need dynamic tool discovery, you can skip A2AClientToolProvider entirely and use boto3 directly:

```python
import json
import boto3
from strands import tool


@tool
def call_market_research(query: str) -> str:
    """Call the Market Research agent to analyze stocks."""
    client = boto3.client("bedrock-agentcore", region_name="us-east-1")

    a2a_message = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": query}]
            }
        },
        "id": "1"
    }

    response = client.invoke_agent_runtime(
        agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:...:runtime/...",
        body=json.dumps(a2a_message),
        contentType="application/json"
    )

    result = json.loads(response["body"].read())
    return result["result"]["message"]["parts"][0]["text"]
```

**Pros**: Simpler, no httpx auth setup
**Cons**: No dynamic discovery, manual tool definition

---

## References

- [AWS AgentCore MCP + SigV4 Sample](https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/01-AgentCore-runtime/02-hosting-MCP-server/hosting_mcp_server_iam_auth.ipynb)
- [streamable_http_sigv4.py utility](https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/01-AgentCore-runtime/02-hosting-MCP-server/streamable_http_sigv4.py)
- [A2A Protocol Documentation](https://google.github.io/A2A/)

---

## Summary

| Approach | Discovery | Messaging | Complexity |
|----------|-----------|-----------|------------|
| A2AClientToolProvider (no auth) | 403 | 403 | - |
| A2AClientToolProvider + SigV4HTTPXAuth | Works | Works | Medium |
| boto3 invoke_agent_runtime | Manual | Works | Low |

For full A2A protocol support with AgentCore, use `SigV4HTTPXAuth` with `httpx_client_args`. For simpler use cases with known agents, boto3 direct invoke works well.
