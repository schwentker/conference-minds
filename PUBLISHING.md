# Publishing conference-minds

## 1. ClawHub (OpenClaw Skill)

### Prerequisites
```bash
npm install -g clawhub@latest
# or: npx clawhub@latest
```

### Publish
```bash
# From the conference-minds directory:
npx clawhub@latest publish

# This publishes based on SKILL.md metadata:
#   name: conference-minds
#   version: 1.0.0
#   author: schwentker
```

### After Publishing
Users install with:
```bash
npx clawhub@latest install schwentker/conference-minds
```

The skill becomes available to any OpenClaw agent. When a user says
"ingest this conference transcript" or "create speaker agents," the
agent reads SKILL.md and follows the instructions.

---

## 2. MCP Server

### Local (stdio transport)

Add to `~/.openclaw/openclaw.json` or Claude Desktop config:

```json
{
  "mcpServers": {
    "conference-minds": {
      "command": "python",
      "args": ["scripts/mcp_server.py"],
      "cwd": "/path/to/conference-minds"
    }
  }
}
```

### For Claude Code / Cursor / Windsurf

Add to project `.mcp.json`:

```json
{
  "mcpServers": {
    "conference-minds": {
      "command": "python",
      "args": ["scripts/mcp_server.py"],
      "cwd": "/path/to/conference-minds"
    }
  }
}
```

### Remote (HTTP transport)

```bash
python scripts/mcp_server.py --http
# Serves on default port, configure reverse proxy as needed
```

### MCP Tools Available

| Tool | Description | Read-Only |
|------|-------------|-----------|
| `conference_minds_ingest` | Ingest transcript, create speaker agents | No |
| `conference_minds_ask` | Ask questions with attributed responses | Yes |
| `conference_minds_speakers` | List speakers with profiles | Yes |
| `conference_minds_themes` | Show conference themes | Yes |
| `conference_minds_tensions` | Show speaker disagreements | Yes |
| `conference_minds_list` | List all stored minds | Yes |
| `conference_minds_delete` | Remove a conference mind | No |

---

## 3. PyPI (pip installable)

```bash
# Build
python -m build

# Upload to PyPI
python -m twine upload dist/*

# Users install with:
pip install conference-minds
pip install conference-minds[mcp]  # with MCP support
```

---

## 4. GitHub

```bash
git init
git add .
git commit -m "v1.0.0: conference-minds - transcript to speaker-agents"
git remote add origin https://github.com/schwentker/conference-minds.git
git push -u origin main

# Tag release
git tag v1.0.0
git push --tags
```

---

## 5. OpenClaw MakePorter Bridge (CLI -> MCP)

For OpenClaw users who prefer the CLI-over-MCP philosophy:

```bash
# The CLI is already the primary interface.
# OpenClaw agents use it directly via shell:

conference-minds ingest --name "My Conference" --file transcript.txt
conference-minds ask "What was the key insight?"
conference-minds speakers --detail

# MakePorter can wrap the CLI as MCP if needed:
# See: https://github.com/openclaw/openclaw/tree/main/skills/mcp-adapter
```

---

## Directory Structure (what gets published)

```
conference-minds/
  SKILL.md              # ClawHub skill definition (required for ClawHub)
  README.md             # GitHub/PyPI readme
  package.json          # ClawHub metadata
  pyproject.toml        # Python package config
  src/
    __init__.py
    core.py             # Core library (ingest, extract, serve)
  scripts/
    __init__.py
    cli.py              # CLI interface
    mcp_server.py       # MCP server (FastMCP)
  tests/
    test_basic.py       # Basic pipeline test
  reference/
    (future: enhanced prompts for LLM-powered extraction)
```

---

## Version Roadmap

### v1.0.0 (current)
- Core pipeline: ingest, extract, serve
- CLI interface
- MCP server
- ClawHub skill
- Heuristic-based speaker analysis (no LLM required)

### v1.1.0 (planned)
- LLM-enhanced soul generation (Ollama + API support)
- Multi-conference merge
- Improved speaker detection for unlabeled transcripts
- SRT/VTT timestamp preservation in passages

### v1.2.0 (planned)  
- Hugging Face Spaces demo
- Audio file input (chain with whisper)
- Export to formatted reports (docx/pdf)
- Moltbook integration (speaker-agents post autonomously)

### v2.0.0 (planned)
- Real-time conference ingestion (live transcript feed)
- Speaker voice synthesis (ElevenLabs integration)
- Agent-to-agent knowledge marketplace integration
- Multi-language transcript support
