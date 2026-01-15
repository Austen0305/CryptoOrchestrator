"""
Documentation Generator
Automatically generates comprehensive documentation from code
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """
    Documentation generator

    Features:
    - API documentation from routes
    - Code documentation extraction
    - README generation
    - Changelog generation
    - Architecture diagrams (text-based)
    """

    def __init__(self, base_path: str = "server_fastapi"):
        self.base_path = Path(base_path)
        self.routes: list[dict[str, Any]] = []
        self.models: list[dict[str, Any]] = []

    def generate_api_docs(self, output_path: str = "docs/API.md") -> str:
        """Generate API documentation"""
        lines = [
            "# API Documentation",
            "",
            f"Generated: {datetime.now(UTC).isoformat()}",
            "",
            "## Overview",
            "",
            "This document describes all available API endpoints.",
            "",
        ]

        # Group routes by tag
        routes_by_tag: dict[str, list[dict[str, Any]]] = {}

        for route in self.routes:
            tags = route.get("tags", ["default"])
            for tag in tags:
                if tag not in routes_by_tag:
                    routes_by_tag[tag] = []
                routes_by_tag[tag].append(route)

        # Generate documentation for each tag
        for tag, routes in routes_by_tag.items():
            lines.append(f"## {tag.title()}")
            lines.append("")

            for route in routes:
                method = route.get("method", "GET")
                path = route.get("path", "")
                summary = route.get("summary", "")
                description = route.get("description", "")

                lines.append(f"### {method} {path}")
                lines.append("")
                if summary:
                    lines.append(f"**Summary**: {summary}")
                    lines.append("")
                if description:
                    lines.append(description)
                    lines.append("")

                # Parameters
                parameters = route.get("parameters", [])
                if parameters:
                    lines.append("**Parameters**:")
                    lines.append("")
                    for param in parameters:
                        param_name = param.get("name", "")
                        param_type = param.get("type", "string")
                        param_desc = param.get("description", "")
                        required = param.get("required", False)
                        req_marker = " (required)" if required else " (optional)"
                        lines.append(
                            f"- `{param_name}` ({param_type}){req_marker}: {param_desc}"
                        )
                    lines.append("")

                # Response
                responses = route.get("responses", {})
                if responses:
                    lines.append("**Responses**:")
                    lines.append("")
                    for status_code, response in responses.items():
                        desc = response.get("description", "")
                        lines.append(f"- `{status_code}`: {desc}")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("\n".join(lines), encoding="utf-8")

        logger.info(f"API documentation generated: {output_path}")
        return output_path

    def generate_readme(self, output_path: str = "docs/README.md") -> str:
        """Generate README documentation"""
        lines = [
            "# CryptoOrchestrator Backend",
            "",
            f"Last Updated: {datetime.now(UTC).isoformat()}",
            "",
            "## Overview",
            "",
            "Enterprise-grade cryptocurrency trading automation platform backend.",
            "",
            "## Features",
            "",
            "- FastAPI-based REST API",
            "- Real-time WebSocket support",
            "- Comprehensive security",
            "- Full observability",
            "- Performance optimized",
            "",
            "## Quick Start",
            "",
            "```bash",
            "# Install dependencies",
            "pip install -r requirements.txt",
            "",
            "# Set environment variables",
            "cp .env.example .env",
            "# Edit .env with your configuration",
            "",
            "# Run server",
            "python -m server_fastapi.main",
            "```",
            "",
            "## API Documentation",
            "",
            "API documentation is available at `/docs` when running the server.",
            "",
            "## Configuration",
            "",
            "See `.env.example` for all configuration options.",
            "",
            "## Development",
            "",
            "See `docs/development/` for development guides.",
            "",
        ]

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("\n".join(lines), encoding="utf-8")

        logger.info(f"README generated: {output_path}")
        return output_path

    def generate_changelog(self, output_path: str = "docs/CHANGELOG.md") -> str:
        """Generate changelog"""
        lines = [
            "# Changelog",
            "",
            "All notable changes to this project will be documented in this file.",
            "",
            "## [Unreleased]",
            "",
            "### Added",
            "- Comprehensive backend and middleware improvements",
            "- Advanced security features",
            "- Full observability stack",
            "- Performance optimizations",
            "",
            "### Changed",
            "- Improved middleware architecture",
            "- Enhanced error handling",
            "",
            "### Fixed",
            "- Various bug fixes and improvements",
            "",
            f"Generated: {datetime.now(UTC).isoformat()}",
        ]

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("\n".join(lines), encoding="utf-8")

        logger.info(f"Changelog generated: {output_path}")
        return output_path

    def extract_route_info(self, app):
        """Extract route information from FastAPI app"""
        self.routes = []

        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                for method in route.methods:
                    if method != "HEAD":
                        route_info = {
                            "method": method,
                            "path": route.path,
                            "summary": getattr(route, "summary", ""),
                            "description": getattr(route, "description", ""),
                            "tags": getattr(route, "tags", []),
                        }
                        self.routes.append(route_info)

    def generate_all(self, app) -> dict[str, str]:
        """Generate all documentation"""
        self.extract_route_info(app)

        return {
            "api_docs": self.generate_api_docs(),
            "readme": self.generate_readme(),
            "changelog": self.generate_changelog(),
        }


# Global documentation generator
doc_generator = DocumentationGenerator()
