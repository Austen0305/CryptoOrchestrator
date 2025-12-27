#!/usr/bin/env python3
"""
API Client Generator
Generates TypeScript API client from OpenAPI schema
"""
import json
import requests
from pathlib import Path
from typing import Dict, Any


def fetch_openapi_schema(url: str = "http://localhost:8000/openapi.json") -> Dict[str, Any]:
    """Fetch OpenAPI schema from API"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching OpenAPI schema: {e}")
        # Try local file
        local_path = Path("docs/openapi.json")
        if local_path.exists():
            with open(local_path) as f:
                return json.load(f)
        raise


def generate_typescript_client(schema: Dict[str, Any], output_path: str = "client/src/lib/api-client.ts"):
    """Generate TypeScript API client from OpenAPI schema"""
    
    paths = schema.get("paths", {})
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    
    code = """/**
 * Auto-generated API Client
 * Generated from OpenAPI schema
 * DO NOT EDIT MANUALLY - This file is auto-generated
 */

export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    method: string,
    endpoint: string,
    options: {
      body?: any;
      headers?: Record<string, string>;
    } = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const token = localStorage.getItem('token');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new ApiError(response.status, data.message || response.statusText, data);
      }

      return {
        data: data as T,
        status: response.status,
      };
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(500, error instanceof Error ? error.message : 'Unknown error');
    }
  }

"""
    
    # Generate methods for each endpoint
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                continue
            
            operation_id = details.get('operationId', f"{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}")
            summary = details.get('summary', '')
            tags = details.get('tags', [])
            
            # Get parameters
            parameters = details.get('parameters', [])
            path_params = [p for p in parameters if p.get('in') == 'path']
            query_params = [p for p in parameters if p.get('in') == 'query']
            
            # Get request body
            request_body = details.get('requestBody', {})
            has_body = bool(request_body)
            
            # Generate method signature
            method_name = operation_id.replace('-', '_')
            params = []
            
            # Path parameters
            for param in path_params:
                param_name = param['name']
                param_type = 'string'  # Default, could be enhanced
                params.append(f"{param_name}: {param_type}")
            
            # Query parameters
            if query_params:
                query_type = '{ ' + ', '.join([f"{p['name']}?: {get_typescript_type(p.get('schema', {}))}" for p in query_params]) + ' }'
                params.append(f"query?: {query_type}")
            
            # Request body
            if has_body:
                body_schema = request_body.get('content', {}).get('application/json', {}).get('schema', {})
                body_type = get_typescript_type(body_schema)
                params.append(f"body?: {body_type}")
            
            # Response type
            responses = details.get('responses', {})
            response_200 = responses.get('200', {})
            response_type = 'any'
            if response_200:
                content = response_200.get('content', {})
                json_content = content.get('application/json', {})
                if json_content:
                    response_type = get_typescript_type(json_content.get('schema', {}))
            
            # Generate method
            method_code = f"""
  /**
   * {summary}
   * {f'Tags: {", ".join(tags)}' if tags else ''}
   */
  async {method_name}({', '.join(params) if params else ''}): Promise<ApiResponse<{response_type}>> {{
"""
            
            # Build endpoint with path params
            endpoint = path
            for param in path_params:
                endpoint = endpoint.replace(f"{{{param['name']}}}", f"${{{param['name']}}}")
            
            # Build query string
            if query_params:
                query_parts = [f"{p['name']}=${{query?.{p['name']}}}" for p in query_params]
                endpoint += "?" + "&".join(query_parts)
            
            method_code += f'    return this.request<{response_type}>(\n'
            method_code += f"      '{method.upper()}',\n"
            method_code += f"      `{endpoint}`,\n"
            if has_body:
                method_code += "      { body }\n"
            else:
                method_code += "      {}\n"
            method_code += "    );\n"
            method_code += "  }\n"
            
            code += method_code
    
    code += """
}

export const apiClient = new ApiClient();
"""
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(code)
    
    print(f"✅ Generated API client at {output_path}")


def get_typescript_type(schema: Dict[str, Any]) -> str:
    """Convert JSON Schema to TypeScript type"""
    if not schema:
        return 'any'
    
    schema_type = schema.get('type')
    ref = schema.get('$ref')
    
    if ref:
        # Extract type name from $ref
        type_name = ref.split('/')[-1]
        return type_name
    
    if schema_type == 'string':
        return 'string'
    elif schema_type == 'number' or schema_type == 'integer':
        return 'number'
    elif schema_type == 'boolean':
        return 'boolean'
    elif schema_type == 'array':
        items = schema.get('items', {})
        item_type = get_typescript_type(items)
        return f'{item_type}[]'
    elif schema_type == 'object':
        properties = schema.get('properties', {})
        if properties:
            props = []
            for prop_name, prop_schema in properties.items():
                prop_type = get_typescript_type(prop_schema)
                required = schema.get('required', [])
                optional = '?' if prop_name not in required else ''
                props.append(f"{prop_name}{optional}: {prop_type}")
            return '{ ' + '; '.join(props) + ' }'
        return 'Record<string, any>'
    
    return 'any'


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate TypeScript API client")
    parser.add_argument("--url", default="http://localhost:8000/openapi.json", help="OpenAPI schema URL")
    parser.add_argument("--output", default="client/src/lib/api-client.ts", help="Output file path")
    
    args = parser.parse_args()
    
    print("📡 Fetching OpenAPI schema...")
    schema = fetch_openapi_schema(args.url)
    
    print("🔨 Generating TypeScript client...")
    generate_typescript_client(schema, args.output)
    
    print("✅ Done!")


if __name__ == "__main__":
    main()

