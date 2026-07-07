#!/usr/bin/env python3
"""
Example demonstrating max_tokens=100 behavior in Strands SDK.
This shows the step-by-step flow when token limits are reached.
"""

import logging
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands.types.exceptions import MaxTokensReachedException

# Enable logging to see the recovery process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
def write_story(theme: str, length: str = "long") -> str:
    """
    Write a creative story based on the given theme.

    Args:
        theme: The main theme or topic for the story
        length: How long the story should be (short, medium, long)
    """
    return f"Once upon a time, there was a magical {theme}..."

@tool
def get_weather(city: str) -> str:
    """Get weather information for a city."""
    return f"The weather in {city} is sunny and 75°F."

def demonstrate_max_tokens_behavior():
    """Demonstrate what happens when max_tokens=100 is reached."""

    print("=" * 60)
    print("STRANDS SDK: max_tokens=100 Example")
    print("=" * 60)

    # Create agent with very low token limit
    model = BedrockModel(max_tokens=100)  # Very low limit to trigger truncation
    agent = Agent(model=model, tools=[write_story, get_weather])

    print(f"✅ Agent created with max_tokens={model.max_tokens}")
    print(f"✅ Tools available: {[tool.name for tool in agent.tool_registry.registry.values()]}")
    print()

    try:
        print("🚀 Calling agent with: 'Write me a very long adventure story about dragons and wizards'")
        print("   (This will likely exceed 100 tokens and trigger max_tokens)")
        print()

        # This should trigger max_tokens due to the complex request
        result = agent("Write me a very long adventure story about dragons and wizards")

        # This line should not be reached due to MaxTokensReachedException
        print(f"✅ Unexpected success: {result.stop_reason}")

    except MaxTokensReachedException as e:
        print("❌ MaxTokensReachedException caught!")
        print(f"   Error message: {str(e)}")
        print()

        # Show the conversation state after the exception
        print("📝 Conversation history after max_tokens:")
        for i, msg in enumerate(agent.messages):
            print(f"   Message {i+1} ({msg['role']}):")
            for content in msg.get('content', []):
                if 'text' in content:
                    text = content['text'][:100] + "..." if len(content['text']) > 100 else content['text']
                    print(f"     Text: {text}")
                elif 'toolUse' in content:
                    print(f"     Tool: {content['toolUse']}")
        print()

        # Demonstrate that the agent can still work after the exception
        print("🔄 Testing agent recovery with a simple question...")
        try:
            # Remove tools to avoid tool use truncation
            agent.tool_registry.registry = {}
            agent.tool_registry.tool_config = {}

            recovery_result = agent("What is 2 + 2?")
            print(f"✅ Recovery successful!")
            print(f"   Stop reason: {recovery_result.stop_reason}")
            print(f"   Response: {recovery_result.message['content'][0]['text']}")

        except Exception as recovery_error:
            print(f"❌ Recovery failed: {recovery_error}")

if __name__ == "__main__":
    demonstrate_max_tokens_behavior()