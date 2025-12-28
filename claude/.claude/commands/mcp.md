---
description: Create a complete Model Context Protocol (MCP) server with the specialized mcp-creator agent
allowed-tools: [Task]
argument-hint: <description of MCP server to create>
model: sonnet
---

# Create MCP Server

You are tasked with creating a Model Context Protocol (MCP) server using the specialized **mcp-creator** agent.

**User Request:** $ARGUMENTS

## Instructions

Use the Task tool to launch the **mcp-creator** agent with the following prompt:

```
Create a complete MCP server for: $ARGUMENTS

Follow the full 6-phase process:
1. DISCOVERY - Ask clarifying questions
2. ANALYSIS & ARCHITECTURE - Design the structure
3. SCAFFOLDING - Create file structure
4. IMPLEMENTATION - Write complete code
5. INTEGRATION & TESTING - Configure and test
6. OPTIMIZATION - Finalize and document

Ensure all code is production-ready, fully typed, with error handling, logging, and complete documentation.
```

Launch the agent now with this prompt.
