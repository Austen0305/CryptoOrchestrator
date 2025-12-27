# StackOverflow MCP

**Status:** ✅ Working  
**Server:** stackoverflow  
**Tools:** 6 tools

## Available Tools

1. `search_questions` - Search by keywords
2. `search_by_tags` - Search by programming tags
3. `get_question` - Get question details
4. `get_question_with_answers` - Get question with answers
5. `get_rate_limit_status` - Check rate limits
6. `get_authentication_status` - Check auth status
7. `get_queue_status` - Check queue status

## Usage Example

```json
{
  "serverName": "stackoverflow",
  "toolName": "search_questions",
  "toolArgs": {
    "query": "python",
    "limit": 1
  }
}
```

## Features

- Search by keywords or tags
- Get detailed question information
- Include answers in results
- HTML to Markdown conversion
- Rate limit monitoring

## Rate Limits

- **Quota:** 300 requests
- **Remaining:** 296/300
- **Status:** ✅ Healthy

## Notes

- Supports sorting (relevance, activity, votes, creation)
- Can filter by tags
- Returns comprehensive question metadata
