"""
File writing tool for creating and managing markdown files.

Supports three modes: create, append, and overwrite for markdown files
in the active project folder.
"""

import os
from pathlib import Path
from typing import Literal
from agno.tools.toolkit import Toolkit
from .project import ProjectTool


class WriterTool(Toolkit):
    """Tool for writing markdown files in projects."""
    
    def __init__(self, project_tool: ProjectTool):
        super().__init__(
            name="writer_tool",
            instructions=[
                "Use this tool to write content to markdown files",
                "Supports three modes: create, append, overwrite",
                "Files are automatically saved with .md extension",
                "Requires an active project folder to be set first"
            ]
        )
        self.project_tool = project_tool
        self.register(self.write_file)
    
    def write_file(self, filename: str, content: str, mode: Literal["create", "append", "overwrite"]) -> str:
        """
        Writes content to a markdown file in the active project folder.
        
        Args:
            filename: The name of the file to write
            content: The content to write
            mode: The write mode - 'create', 'append', or 'overwrite'
            
        Returns:
            Success message or error message
        """
        try:
            # Check if project folder is initialized
            project_folder = self.project_tool.get_active_project_folder()
            if not project_folder:
                return "Error: No active project folder. Please create a project first using create_project."
            
            # Ensure filename ends with .md
            if not filename.endswith('.md'):
                filename = filename + '.md'
            
            # Create full file path
            file_path = Path(project_folder) / filename
            
            if mode == "create":
                # Create mode: fail if file exists
                if file_path.exists():
                    return f"Error: File '{filename}' already exists. Use 'append' or 'overwrite' mode to modify it."
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully created file '{filename}' with {len(content)} characters."
            
            elif mode == "append":
                # Append mode: add to end of file
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully appended {len(content)} characters to '{filename}'."
            
            elif mode == "overwrite":
                # Overwrite mode: replace entire file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully overwrote '{filename}' with {len(content)} characters."
            
            else:
                return f"Error: Invalid mode '{mode}'. Use 'create', 'append', or 'overwrite'."
            
        except Exception as e:
            return f"Error writing file '{filename}': {str(e)}"
