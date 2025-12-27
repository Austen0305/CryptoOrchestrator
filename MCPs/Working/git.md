# Git MCP

**Status:** ✅ Working  
**Server:** git  
**Tools:** 27 tools

## Available Tools

### Basic Operations
- `git_add` - Stage files
- `git_commit` - Create commits
- `git_status` - Show working tree status
- `git_diff` - View differences
- `git_log` - View commit history

### Branch Management
- `git_branch` - List/create/delete branches
- `git_checkout` - Switch branches
- `git_merge` - Merge branches
- `git_rebase` - Rebase commits
- `git_cherry_pick` - Cherry-pick commits

### Remote Operations
- `git_clone` - Clone repositories
- `git_fetch` - Fetch updates
- `git_pull` - Pull changes
- `git_push` - Push changes
- `git_remote` - Manage remotes

### Advanced
- `git_stash` - Manage stashes
- `git_reset` - Reset HEAD
- `git_tag` - Manage tags
- `git_worktree` - Manage worktrees
- `git_blame` - Show line authorship
- `git_show` - Show object details
- `git_reflog` - View reference logs
- `git_clean` - Remove untracked files

## Usage Example

```json
{
  "serverName": "git",
  "toolName": "git_status",
  "toolArgs": {
    "path": "C:\\Users\\William Walker\\OneDrive\\Desktop\\CryptoOrchestrator\\Crypto-Orchestrator"
  }
}
```

## Repository Path

- `C:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\Crypto-Orchestrator`

## Notes

- Supports multi-line commit messages (JSON format)
- Can set working directory for session
- Full Git functionality available
