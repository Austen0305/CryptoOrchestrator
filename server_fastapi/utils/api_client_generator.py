"""
API Client Generator
Generates type-safe API clients from OpenAPI schema
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class APIClientGenerator:
    """
    Generates API clients from OpenAPI schema

    Supports:
    - TypeScript/JavaScript
    - Python
    - Custom templates
    """

    def __init__(self, schema: dict[str, Any]):
        self.schema = schema
        self.paths = schema.get("paths", {})
        self.components = schema.get("components", {})

    def generate_typescript(self, output_path: str = "client/src/lib/api-client.ts"):
        """Generate TypeScript API client"""
        lines = [
            "// Auto-generated API client",
            "// Do not edit manually - regenerate from OpenAPI schema",
            "",
            "export interface ApiResponse<T> {",
            "  success: boolean;",
            "  data?: T;",
            "  error?: {",
            "    code: string;",
            "    message: string;",
            "  };",
            "}",
            "",
            "export class ApiClient {",
            "  private baseUrl: string;",
            "  private token?: string;",
            "",
            "  constructor(baseUrl: string = 'http://localhost:8000') {",
            "    this.baseUrl = baseUrl;",
            "  }",
            "",
            "  setToken(token: string) {",
            "    this.token = token;",
            "  }",
            "",
            "  private async request<T>(",
            "    method: string,",
            "    path: string,",
            "    body?: any",
            "  ): Promise<ApiResponse<T>> {",
            "    const headers: Record<string, string> = {",
            "      'Content-Type': 'application/json',",
            "    };",
            "",
            "    if (this.token) {",
            "      headers['Authorization'] = `Bearer ${this.token}`;",
            "    }",
            "",
            "    const response = await fetch(`${this.baseUrl}${path}`, {",
            "      method,",
            "      headers,",
            "      body: body ? JSON.stringify(body) : undefined,",
            "    });",
            "",
            "    const data = await response.json();",
            "",
            "    if (!response.ok) {",
            "      return {",
            "        success: false,",
            "        error: {",
            "          code: response.status.toString(),",
            "          message: data.detail || 'Request failed',",
            "        },",
            "      };",
            "    }",
            "",
            "    return {",
            "      success: true,",
            "      data,",
            "    };",
            "  }",
            "",
        ]

        # Generate methods for each endpoint
        for path, methods in self.paths.items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                    continue

                operation_id = details.get(
                    "operationId", self._generate_operation_id(path, method)
                )
                summary = details.get("summary", "")
                parameters = details.get("parameters", [])
                request_body = details.get("requestBody", {})

                # Generate method signature
                method_name = self._camel_case(operation_id)
                method_lines = [
                    "  /**",
                    f"   * {summary}",
                    "   */",
                    f"  async {method_name}(",
                ]

                # Add parameters
                param_lines = []
                path_params = [p for p in parameters if p.get("in") == "path"]
                query_params = [p for p in parameters if p.get("in") == "query"]

                if path_params:
                    for param in path_params:
                        param_name = param["name"]
                        param_type = self._typescript_type(param.get("schema", {}))
                        param_lines.append(f"    {param_name}: {param_type},")

                if query_params:
                    param_lines.append("    query?: {")
                    for param in query_params:
                        param_name = param["name"]
                        param_type = self._typescript_type(param.get("schema", {}))
                        required = param.get("required", False)
                        optional = "" if required else "?"
                        param_lines.append(
                            f"      {param_name}{optional}: {param_type};"
                        )
                    param_lines.append("    },")

                if request_body:
                    param_lines.append("    body?: any,")

                method_lines.extend(param_lines)
                method_lines.append("  ): Promise<ApiResponse<any>> {")

                # Generate method body
                method_path = self._replace_path_params(path, path_params)
                method_lines.append(f"    const path = `{method_path}`;")

                if query_params:
                    method_lines.append(
                        "    const queryString = query ? '?' + new URLSearchParams(query as any).toString() : '';"
                    )
                    method_lines.append(
                        "    return this.request('GET', path + queryString);"
                    )
                elif method.lower() == "get":
                    method_lines.append(
                        f"    return this.request<any>('{method.upper()}', path);"
                    )
                else:
                    method_lines.append(
                        f"    return this.request<any>('{method.upper()}', path, body);"
                    )

                method_lines.append("  }")
                method_lines.append("")

                lines.extend(method_lines)

        lines.append("}")

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("\n".join(lines), encoding="utf-8")

        logger.info(f"TypeScript API client generated: {output_path}")

    def _generate_operation_id(self, path: str, method: str) -> str:
        """Generate operation ID from path and method"""
        parts = path.strip("/").split("/")
        operation = "_".join(parts)
        return f"{method.lower()}_{operation}"

    def _camel_case(self, name: str) -> str:
        """Convert to camelCase"""
        parts = name.split("_")
        return parts[0] + "".join(word.capitalize() for word in parts[1:])

    def _typescript_type(self, schema: dict[str, Any]) -> str:
        """Convert JSON schema to TypeScript type"""
        schema_type = schema.get("type", "any")

        if schema_type == "string":
            return "string"
        elif schema_type == "number" or schema_type == "integer":
            return "number"
        elif schema_type == "boolean":
            return "boolean"
        elif schema_type == "array":
            items = schema.get("items", {})
            item_type = self._typescript_type(items)
            return f"{item_type}[]"
        elif schema_type == "object":
            return "Record<string, any>"
        else:
            return "any"

    def _replace_path_params(self, path: str, params: list[dict[str, Any]]) -> str:
        """Replace path parameters with template literals"""
        result = path
        for param in params:
            param_name = param["name"]
            result = result.replace(f"{{{param_name}}}", f"${{{param_name}}}")
        return result

    def generate_python(self, output_path: str = "api_client.py"):
        """Generate Python API client"""
        lines = [
            "# Auto-generated API client",
            "# Do not edit manually - regenerate from OpenAPI schema",
            "",
            "import httpx",
            "from typing import Optional, Dict, Any, List",
            "",
            "class ApiClient:",
            "    def __init__(self, base_url: str = 'http://localhost:8000'):",
            "        self.base_url = base_url",
            "        self.token: Optional[str] = None",
            "",
            "    def set_token(self, token: str):",
            "        self.token = token",
            "",
            "    def _request(",
            "        self,",
            "        method: str,",
            "        path: str,",
            "        json: Optional[Dict[str, Any]] = None,",
            "    ) -> Dict[str, Any]:",
            "        headers = {'Content-Type': 'application/json'}",
            "        if self.token:",
            "            headers['Authorization'] = f'Bearer {self.token}'",
            "",
            "        with httpx.Client() as client:",
            "            response = client.request(",
            "                method=method,",
            "                url=f'{self.base_url}{path}',",
            "                headers=headers,",
            "                json=json,",
            "            )",
            "            response.raise_for_status()",
            "            return response.json()",
            "",
        ]

        # Generate methods (similar to TypeScript)
        for path, methods in self.paths.items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                    continue

                operation_id = details.get(
                    "operationId", self._generate_operation_id(path, method)
                )
                method_name = self._snake_case(operation_id)
                summary = details.get("summary", "")

                lines.append(
                    f"    def {method_name}(self, **kwargs) -> Dict[str, Any]:"
                )
                lines.append(f'        """{summary}"""')
                lines.append(
                    f"        return self._request('{method.upper()}', '{path}', json=kwargs)"
                )
                lines.append("")

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("\n".join(lines), encoding="utf-8")

        logger.info(f"Python API client generated: {output_path}")

    def _snake_case(self, name: str) -> str:
        """Convert to snake_case"""
        return name.replace("-", "_").replace(" ", "_").lower()


def generate_api_clients(schema_path: str = "docs/openapi.json"):
    """Generate API clients from OpenAPI schema"""
    schema_file = Path(schema_path)
    if not schema_file.exists():
        logger.error(f"OpenAPI schema not found: {schema_path}")
        return

    with open(schema_file) as f:
        schema = json.load(f)

    generator = APIClientGenerator(schema)
    generator.generate_typescript()
    generator.generate_python()
