# conference-minds

Transform ephemeral conference content into persistent, conversational intelligence.

conference-minds takes any transcript and produces a queryable knowledge layer where each speaker becomes a distinct conversational agent. Ask a question, get an answer attributed to the specific speaker whose position best addresses it.

## Install

```bash
# Core (no dependencies)
pip install conference-minds

# With MCP server support
pip install conference-minds[mcp]
```

## Quick Start

### CLI

```bash
# Ingest a transcript
conference-minds ingest --name "YC Interview" --file transcript.txt

# Ask a question
conference-minds ask "Why does Peter prefer CLI over MCP?"

# Explore
conference-minds speakers --detail
conference-minds themes
conference-minds tensions
conference-minds list
```

### As OpenClaw Skill (ClawHub)

```bash
npx clawhub@latest install schwentker/conference-minds
```

Then in conversation with your agent:
> "Ingest this conference transcript and create speaker agents"

### As MCP Server

Add to your MCP config (Claude Code, Cursor, etc.):

```json
{
  "mcpServers": {
    "conference-minds": {
      "command": "python",
      "args": ["-m", "scripts.mcp_server"],
      "cwd": "/path/to/conference-minds"
    }
  }
}
```

**Available MCP tools:**
- `conference_minds_ingest` - Ingest transcript, extract speakers
- `conference_minds_ask` - Ask questions with attributed responses
- `conference_minds_speakers` - List speakers with expertise profiles
- `conference_minds_themes` - Show dominant conference themes
- `conference_minds_tensions` - Show speaker disagreements
- `conference_minds_list` - List all stored conference minds
- `conference_minds_delete` - Remove a conference mind

## How It Works

### Three-Layer Pipeline

```
INGEST              EXTRACT              SERVE
transcript    ->    speakers[]     ->    routed response
(any format)        soul.md              + attribution
                    skills.md
                    passages[]
```

**Ingest**: Accepts raw text, .srt, .vtt, YouTube format, labeled speakers. Auto-detects format.

**Extract**: For each speaker, generates a soul file (communication style, rhetorical patterns), skills file (domain expertise), and indexed passages. Detects cross-speaker themes and tensions.

**Serve**: Routes questions to the most relevant speaker(s) using weighted scoring (topical match, expertise depth, uniqueness). Every response includes attribution to specific transcript passages.

## Supported Transcript Formats

- Raw pasted text
- Labeled speakers (`Speaker Name: text`)
- SRT subtitles
- WebVTT subtitles
- YouTube transcript (timestamp + text)
- Multiple files for multi-session conferences

## Privacy

- Zero dependencies for core operation (pure Python stdlib)
- All processing runs locally
- No data sent to external services
- Speaker agents clearly labeled as AI reconstructions
- Attribution mandatory in all responses

## Chaining

conference-minds chains with other tools:

- **Whisper/transcription** -> auto-transcribe before ingestion
- **Moltbook** -> speaker-agents post to agent social network
- **Longterm memory** -> persist context across sessions
- **docx/pdf** -> export as formatted reports

## License

MIT
