"""
Project management tool for creative writing projects.

Handles creation and management of project folders with sanitized names.
"""

import re
from pathlib import Path

from agno.tools.toolkit import Toolkit


class ProjectTool(Toolkit):
    """Tool for managing writing projects and folders."""

    def __init__(self):
        """Initialize project management tool."""
        super().__init__(
            name="project_tool",
            instructions="Use this tool to create new project folders. Project names are automatically sanitized for filesystem compatibility. Projects are created in an 'output' directory. Only one project can be active at a time.",
        )
        self.register(self.create_project)
        self._active_project_folder: str | None = None

    def sanitize_folder_name(self, name: str) -> str:
        """
        Sanitizes a folder name for filesystem compatibility.

        Args:
            name: The proposed folder name

        Returns:
            Sanitized folder name
        """
        # Replace spaces with underscores
        name = name.strip().replace(" ", "_")
        # Remove any characters that aren't alphanumeric, underscore, or hyphen
        name = re.sub(r"[^\w\-]", "", name)
        # Remove leading/trailing hyphens or underscores
        name = name.strip("-_")
        # Ensure it's not empty
        if not name:
            name = "untitled_project"
        return name

    def get_active_project_folder(self) -> str | None:
        """
        Return the currently active project folder path.

        Returns:
            Path to active project folder or None if not set
        """
        return self._active_project_folder

    def set_active_project_folder(self, folder_path: str) -> None:
        """
        Set the active project folder.

        Args:
            folder_path: Path to the project folder
        """
        self._active_project_folder = folder_path

    def create_project(self, project_name: str) -> str:
        """
        Create a new project folder in the output directory.

        Args:
            project_name: The desired project name

        Returns:
            Success message with folder path or error message
        """
        try:
            # Sanitize the folder name
            sanitized_name = self.sanitize_folder_name(project_name)

            # Get the script's root directory
            script_dir = Path(__file__).parent.parent.parent
            root_dir = script_dir

            # Create output directory if it doesn't exist
            output_dir = root_dir / "output"
            if not output_dir.exists():
                output_dir.mkdir(exist_ok=True)

            # Create the full path inside output directory
            project_path = output_dir / sanitized_name

            # Check if folder already exists
            if project_path.exists():
                self.set_active_project_folder(str(project_path))
                return f"Project folder already exists at '{project_path}'. Set as active project folder."
            else:
                # Create the folder
                project_path.mkdir(exist_ok=True)
                self.set_active_project_folder(str(project_path))
                return (
                    f"Successfully created project folder at '{project_path}'. This is now the active project folder."
                )

        except Exception as e:
            return f"Error creating project folder: {e!s}"
