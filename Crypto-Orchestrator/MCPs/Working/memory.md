# Memory MCP

**Status:** ✅ Working  
**Server:** memory  
**Tools:** 9 tools

## Available Tools

1. `create_entities` - Create knowledge graph entities
2. `create_relations` - Create relations between entities
3. `add_observations` - Add observations to entities
4. `delete_entities` - Delete entities
5. `delete_observations` - Delete observations
6. `delete_relations` - Delete relations
7. `read_graph` - Read entire knowledge graph
8. `search_nodes` - Search nodes by query
9. `open_nodes` - Open specific nodes

## Usage Example

```json
{
  "serverName": "memory",
  "toolName": "read_graph",
  "toolArgs": {}
}
```

## Features

- Knowledge graph storage
- Entity-relationship modeling
- Searchable knowledge base
- Observation tracking
- Graph traversal

## Notes

- Relations should be in active voice
- Supports complex knowledge structures
- Can search and filter nodes
- Persistent knowledge storage
