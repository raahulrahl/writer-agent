# |---------------------------------------------------------|
# |                                                         |
# |                 Give Feedback / Get Help                |
# | https://github.com/getbindu/Bindu/issues/new/choose    |
# |                                                         |
# |---------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""Writer Agent - AI creative writing assistant using Agno framework.

Autonomous agent for creating novels, books, and short story collections.
Inspired by kimi-writer but built on the Agno framework.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional


from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.openrouter import OpenRouter
from agno.tools.mem0 import Mem0Tools

from bindu.penguin.bindufy import bindufy
from dotenv import load_dotenv

# Import custom writing tools
from .tools import ProjectTool, WriterTool, CompressionTool


# Load environment variables from .env file
load_dotenv()

# Global tool instances and agent
project_tool: ProjectTool | None = None
writer_tool: WriterTool | None = None
compression_tool: CompressionTool | None = None
agent: Agent | None = None
model_name: str | None = None
moonshot_api_key: str | None = None
openrouter_api_key: str | None = None
mem0_api_key: str | None = None
_initialized = False
_init_lock = asyncio.Lock()


def initialize_writing_tools() -> None:
    """Initialize the custom writing tools."""
    global project_tool, writer_tool, compression_tool
    
    # Initialize tools in dependency order
    project_tool = ProjectTool()
    writer_tool = WriterTool(project_tool)
    compression_tool = CompressionTool(project_tool)
    
    print("✅ Writing tools initialized")


def load_config() -> dict:
    """Load agent configuration from project root."""
    # Get path to agent_config.json in project root
    config_path = Path(__file__).parent / "agent_config.json"

    with open(config_path, "r") as f:
        return json.load(f)


# Create the agent instance
async def initialize_agent() -> None:
    """Initialize the creative writing agent."""
    global agent, model_name, project_tool, writer_tool, compression_tool

    if not model_name:
        msg = "model_name must be set before initializing agent"
        raise ValueError(msg)

    # Model selection logic (supports Moonshot, OpenAI, and OpenRouter)
    if moonshot_api_key and "kimi" in model_name.lower():
        model = OpenAIChat(
            id=model_name,
            api_key=moonshot_api_key,
            base_url="https://api.moonshot.ai/v1"
        )
        print(f"✅ Using Moonshot model: {model_name}")
    elif openrouter_api_key:
        model = OpenRouter(
            id=model_name,
            api_key=openrouter_api_key,
            cache_response=True,
            supports_native_structured_outputs=True,
        )
        print(f"✅ Using OpenRouter model: {model_name}")
    else:
        raise ValueError("No valid API key provided for model selection")

    # Prepare tools list
    tools = [tool for tool in [project_tool, writer_tool, compression_tool] if tool is not None]
    
    # Add memory tools if API key is provided
    if mem0_api_key:
        tools.append(Mem0Tools(api_key=mem0_api_key))
        print("🧠 Mem0 memory enabled")

    # Create the creative writing agent
    agent = Agent(
        name="Creative Writing Assistant",
        model=model,
        tools=tools,
        description=dedent("""\
            You are Kimi, an expert creative writing assistant developed by Moonshot AI. 
            Your specialty is creating novels, books, and collections of short stories based on user requests.

            Your capabilities:
            1. You can create project folders to organize writing projects
            2. You can write markdown files with three modes: create new files, append to existing files, or overwrite files
            3. Context compression happens automatically when needed - you don't need to worry about it

            CRITICAL WRITING GUIDELINES:
            - Write SUBSTANTIAL, COMPLETE content - don't hold back on length
            - Short stories should be 3,000-10,000 words (10-30 pages) - write as much as the story needs!
            - Chapters should be 2,000-5,000 words minimum - fully developed and satisfying
            - NEVER write abbreviated or skeleton content - every piece should be a complete, polished work
            - Don't summarize or skip scenes - write them out fully with dialogue, description, and detail
            - Quality AND quantity matter - give readers a complete, immersive experience
            - If a story needs 8,000 words to be good, write all 8,000 words in one file
            - Use 'create' mode with full content rather than creating stubs you'll append to later

            Best practices:
            - Always start by creating a project folder using create_project
            - Break large works into multiple files (chapters, stories, etc.)
            - Use descriptive filenames (e.g., "chapter_01.md", "story_the_last_star.md")
            - For collections, consider creating a table of contents file
            - Write each file as a COMPLETE, SUBSTANTIAL piece - not a summary or outline

            Your workflow:
            1. Understand the user's request
            2. Create an appropriately named project folder
            3. Plan the structure of the work (chapters, stories, etc.)
            4. Write COMPLETE, FULL-LENGTH content for each file
            5. Create supporting files like README or table of contents if helpful

            REMEMBER: You have access to large token limits - use them! Write rich, detailed, complete stories. 
            Don't artificially limit yourself. A good short story is 5,000-10,000 words. A good chapter is 3,000-5,000 words. 
            Write what the narrative needs to be excellent.\
        """),
        instructions=dedent("""\
            Follow this workflow for every writing project:

            1. Project Setup 📁
               - Always start by creating a project folder with create_project()
               - Use a descriptive, sanitized project name
               - This organizes all your writing files

            2. Content Planning 📋
               - Understand the user's requirements thoroughly
               - Plan the structure (chapters, stories, sections)
               - Think about pacing, character development, plot arcs

            3. Writing Execution ✍️
               - Write SUBSTANTIAL, COMPLETE content in each file
               - Target 2,000-5,000+ words per chapter/story
               - Include rich dialogue, description, and detail
               - Never write summaries or outlines - write full scenes

            4. File Management 📄
               - Use descriptive filenames (chapter_01.md, story_title.md)
               - Use 'create' mode for new files, 'append' for additions
               - Organize files logically within the project

            5. Quality Assurance ✨
               - Ensure each piece is complete and satisfying
               - Check for consistency and continuity
               - Add depth and detail to immersive experience

            Always prioritize quality AND quantity. Your readers deserve complete, polished works.\
        """),
        add_datetime_to_context=True,
        markdown=True,
    )
    print("✅ Creative Writing Agent initialized")


async def cleanup_tools() -> None:
    """Clean up any tool resources."""
    global project_tool, writer_tool, compression_tool
    
    # Reset tool instances
    project_tool = None
    writer_tool = None
    compression_tool = None
    
    print("🧹 Writing tools cleaned up")


async def run_agent(messages: list[dict[str, str]]) -> Any:
    """Run the agent with the given messages.

    Args:
        messages: List of message dicts with 'role' and 'content' keys

    Returns:
        Agent response
    """
    global agent

    # Run the agent and get response
    response = await agent.arun(messages)
    return response




async def handler(messages: list[dict[str, str]]) -> Any:
    """Handle incoming agent messages with lazy initialization.

    Args:
        messages: List of message dicts with 'role' and 'content' keys

    Returns:
        Agent response
    """
    global _initialized

    # Lazy initialization on first call (in bindufy's event loop)
    async with _init_lock:
        if not _initialized:
            print("🔧 Initializing writing tools and agent...")
            await initialize_all()
            _initialized = True

    # Run the async agent
    result = await run_agent(messages)
    return result
    


async def initialize_all():
    """Initialize writing tools and agent."""
    initialize_writing_tools()
    await initialize_agent()


def main():
    """Run the Creative Writing Agent."""
    global model_name, moonshot_api_key, openrouter_api_key, mem0_api_key

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Creative Writing Agent - AI-powered novel and story generator")
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("MODEL_NAME", "kimi-k2-thinking"),
        help="Model ID to use (default: kimi-k2-thinking, env: MODEL_NAME)",
    )
    parser.add_argument(
        "--moonshot-api-key",
        type=str,
        default=os.getenv("MOONSHOT_API_KEY"),
        help="Moonshot API key for kimi models (env: MOONSHOT_API_KEY)",
    )
    parser.add_argument(
        "--openrouter-api-key",
        type=str,
        default=os.getenv("OPENROUTER_API_KEY"),
        help="OpenRouter API key for alternative models (env: OPENROUTER_API_KEY)",
    )
    parser.add_argument(
        "--mem0-api-key",
        type=str,
        default=os.getenv("MEM0_API_KEY"),
        help="Mem0 API key for memory operations (env: MEM0_API_KEY)",
    )
    args = parser.parse_args()

    # Set global model name and API keys
    model_name = args.model
    moonshot_api_key = args.moonshot_api_key
    openrouter_api_key = args.openrouter_api_key
    mem0_api_key = args.mem0_api_key

    # Validate API keys based on model choice
    if "kimi" in model_name.lower() and not moonshot_api_key:
        # If kimi model requested but no Moonshot key, fall back to OpenRouter
        if openrouter_api_key:
            model_name = "openai/gpt-4o"
            print(f"⚠️  Moonshot API key not found, falling back to OpenRouter with {model_name}")
        else:
            raise ValueError("MOONSHOT_API_KEY required for Kimi models. Get your key from: https://platform.moonshot.cn/")
    elif not moonshot_api_key and not openrouter_api_key:
        raise ValueError("Either MOONSHOT_API_KEY or OPENROUTER_API_KEY required")

    print(f"🤖 Creative Writing Agent - AI-powered storytelling")
    print(f"📝 Capabilities: Novels, books, short story collections")
    print(f"🧠 Model: {model_name}")

    # Load configuration
    config = load_config()

    try:
        # Bindufy and start the agent server
        print("🚀 Starting Creative Writing Agent server...")
        print(f"🌐 Server will run on: {config.get('deployment', {}).get('url', 'http://127.0.0.1:3773')}")
        bindufy(config, handler)
    except KeyboardInterrupt:
        print("\n🛑 Creative Writing Agent stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        # Cleanup on exit
        print("\n🧹 Cleaning up...")
        asyncio.run(cleanup_tools())


# Bindufy and start the agent server
if __name__ == "__main__":
    main()
