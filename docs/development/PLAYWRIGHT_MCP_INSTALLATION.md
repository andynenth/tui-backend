Basic Command:
bashclaude mcp add playwright npx @playwright/mcp@latest
With Additional Options (if needed):
bash# Add with headless mode
claude mcp add playwright -- npx @playwright/mcp@latest --headless

# Add with specific scope (project-wide)

claude mcp add playwright -s project -- npx @playwright/mcp@latest

# Add with environment variables

claude mcp add playwright -e API_KEY=your-key -- npx @playwright/mcp@latest --headless
Verify Installation:
bash# List all MCP servers
claude mcp list

# Check specific server details

claude mcp get playwright

# Check MCP status within Claude Code

/mcp
Common Options:

-s local (default): Available only to you in current project
-s project: Shared with team via .mcp.json file
-s user: Available across all your projects
--headless: Run browser in headless mode
--isolated: Keep browser profile in memory only

The basic command should work for most use cases. Use the additional options based on your specific needs.
