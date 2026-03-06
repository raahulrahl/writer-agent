"""
Context compression tool for managing conversation history during long writing projects.

Automatically compresses context when approaching token limits to maintain
conversation continuity while managing memory usage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from agno.tools.toolkit import Toolkit

from .project import ProjectTool


class CompressionTool(Toolkit):
    """Tool for managing conversation context and compressing long conversations."""

    def __init__(self, project_tool: ProjectTool):
        """Initialize compression tool with project tool reference."""
        super().__init__(
            name="compression_tool",
            instructions="Use this tool when conversation history becomes too long. Automatically triggered when approaching token limits. Saves compressed context summaries to project folder. Maintains conversation continuity while managing memory.",
        )
        self.project_tool = project_tool
        self.register(self.compress_context)

    def compress_context(self, messages: list[Any], keep_recent: int = 10) -> dict[str, Any]:
        """
        Compresses the conversation context by summarizing older messages.

        Args:
            messages: The full message history
            keep_recent: Number of recent messages to keep uncompressed

        Returns:
            Dictionary containing compression results and statistics
        """
        try:
            if len(messages) <= keep_recent + 1:  # +1 for system message
                return {
                    "compressed_messages": messages,
                    "summary_file": None,
                    "tokens_saved": 0,
                    "message": "Not enough messages to compress.",
                }

            # Separate system message, messages to compress, and recent messages
            system_message = messages[0] if messages and messages[0].get("role") == "system" else None

            if system_message:
                messages_to_compress = messages[1:-keep_recent]
                recent_messages = messages[-keep_recent:]
            else:
                messages_to_compress = messages[:-keep_recent]
                recent_messages = messages[-keep_recent:]

            # Create a detailed summary of the conversation
            summary = self._create_conversation_summary(messages_to_compress)

            # Save summary to file
            summary_file_path = self._save_summary_to_file(summary, len(messages_to_compress), keep_recent)

            # Build the compressed message list
            compressed_messages = []

            # Add system message if it exists
            if system_message:
                compressed_messages.append(system_message)

            # Add the summary as a user message
            compressed_messages.append({
                "role": "user",
                "content": f"[CONTEXT SUMMARY - Previous conversation compressed]\n\n{summary}\n\n[END CONTEXT SUMMARY - Continuing from here...]",
            })

            # Add recent messages
            compressed_messages.extend(recent_messages)

            # Calculate token savings (rough estimate)
            original_length = sum(len(str(m)) for m in messages_to_compress)
            compressed_length = len(summary)
            estimated_tokens_saved = (original_length - compressed_length) // 4  # Rough estimate

            return {
                "compressed_messages": compressed_messages,
                "summary_file": summary_file_path,
                "tokens_saved": estimated_tokens_saved,
                "messages_compressed": len(messages_to_compress),
                "messages_retained": keep_recent,
                "message": f"Successfully compressed {len(messages_to_compress)} messages. Summary saved to {summary_file_path}.",
            }

        except Exception as e:
            return {
                "compressed_messages": messages,
                "summary_file": None,
                "tokens_saved": 0,
                "message": f"Error during compression: {e!s}",
            }

    def _extract_message_info(self, messages: list[Any]) -> tuple[list[str], list[str], list[str]]:
        """Extract project info, files created, and writing progress from messages."""
        project_info = []
        files_created = []
        writing_progress = []

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                # Extract the original task/goal
                if "project" in content.lower() or "write" in content.lower() or "create" in content.lower():
                    project_info.append(f"Original Request: {content[:200]}...")

            elif role == "assistant":
                # Look for tool calls and their results
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc.function.name == "create_project":
                            args = json.loads(tc.function.arguments)
                            project_info.append(f"Project Created: {args.get('project_name', 'Unknown')}")
                        elif tc.function.name == "write_file":
                            args = json.loads(tc.function.arguments)
                            filename = args.get("filename", "unknown")
                            mode = args.get("mode", "unknown")
                            files_created.append(f"{filename} ({mode})")

                # Track writing progress
                if len(content) > 500:  # Substantial content
                    writing_progress.append(f"Generated content ({len(content)} characters)")

        return project_info, files_created, writing_progress

    def _create_conversation_summary(self, messages: list[Any]) -> str:
        """Create a comprehensive summary of the conversation history."""
        summary_parts = [
            "# Writing Project Context Summary",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Project Overview",
        ]

        # Extract key information from messages
        project_info, files_created, writing_progress = self._extract_message_info(messages)

        # Add extracted information to summary
        if project_info:
            summary_parts.extend(project_info)

        summary_parts.extend([
            "",
            "## Files Created",
        ])

        if files_created:
            summary_parts.extend([f"- {file}" for file in files_created])
        else:
            summary_parts.append("- No files created yet")

        summary_parts.extend([
            "",
            "## Writing Progress",
        ])

        if writing_progress:
            summary_parts.extend([f"- {progress}" for progress in writing_progress])
        else:
            summary_parts.append("- No substantial writing progress yet")

        summary_parts.extend([
            "",
            "## Current Status",
            "Project is ongoing. Continue from where we left off.",
            "",
            "---",
            f"**Note:** This summary was generated to manage context length. Original conversation had {len(messages)} messages.",
        ])

        return "\n".join(summary_parts)

    def _save_summary_to_file(self, summary: str, messages_compressed: int, messages_retained: int) -> str:
        """Save the summary to a file in the project folder."""
        try:
            project_folder = self.project_tool.get_active_project_folder()

            if project_folder:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                summary_file = Path(project_folder) / f".context_summary_{timestamp}.md"

                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write(summary)

                return str(summary_file)
            else:
                # If no project folder, return a placeholder
                return "No project folder - summary not saved"

        except Exception as e:
            return f"Error saving summary: {e!s}"
