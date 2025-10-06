#!/usr/bin/env python3
"""
Simple demonstration of max_tokens=100 behavior.
Shows the exact flow from the test case.
"""

from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands.types.exceptions import MaxTokensReachedException

@tool
def story_tool(story: str) -> str:
    """Tool that writes a story that is minimum 50,000 lines long."""
    return story

# Recreate the exact test scenario
def simple_demo():
    print("Creating agent with max_tokens=100...")

    # Step 1: Create agent with low token limit
    model = BedrockModel(max_tokens=100)
    agent = Agent(model=model, tools=[story_tool])

    print(f"Agent created. Token limit: {model.config.get('max_tokens', 'default')}")
    print("Available tools:", list(agent.tool_registry.registry.keys()))

    try:
        print("\nCalling agent('Tell me a story!')...")
        print("This will trigger max_tokens because:")
        print("- Model tries to call story_tool")
        print("- Response gets truncated at 100 tokens")
        print("- Tool use becomes incomplete")

        # Step 2: This triggers MaxTokensReachedException
        agent("Tell me a story!")
        print("❌ Unexpected: No exception thrown")

    except MaxTokensReachedException as e:
        print(f"\n✅ MaxTokensReachedException caught: {e}")

        # Step 3: Show message recovery in action
        print("\n📋 Messages after recovery:")
        for i, msg in enumerate(agent.messages):
            print(f"  Message {i+1} ({msg['role']}):")
            for content in msg['content']:
                if 'text' in content:
                    print(f"    📄 Text: {content['text']}")
                elif 'toolUse' in content:
                    print(f"    🔧 Tool: {content['toolUse']}")

        # Step 4: Verify expected error message exists
        expected_text = "tool use was incomplete due to maximum token limits being reached"
        all_text = [
            content["text"]
            for message in agent.messages
            for content in message.get("content", [])
            if "text" in content
        ]

        has_error_message = any(expected_text in text for text in all_text)
        print(f"\n🔍 Contains recovery error message: {has_error_message}")

        # Step 5: Show agent can recover
        print("\n🔄 Testing recovery (removing tools)...")
        agent.tool_registry.registry = {}
        agent.tool_registry.tool_config = {}

        recovery_result = agent("What is 3+3")
        print(f"✅ Recovery successful: {recovery_result.stop_reason}")
        print(f"📄 Response: {recovery_result.message['content'][0]['text']}")

if __name__ == "__main__":
    simple_demo()