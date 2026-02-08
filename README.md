# conference-minds

**Transform ephemeral conference content into persistent, conversational intelligence.**

conference-minds takes any transcript and produces a queryable knowledge layer where each speaker becomes a distinct conversational agent. Ask a question, get an answer attributed to the specific speaker whose position best addresses it.

Conferences generate enormous signal that evaporates within days. Recordings exist but nobody rewatches them. Summaries flatten the disagreements that made the conversation valuable. conference-minds preserves the texture: who said what, where they disagreed, what positions they actually held, and what questions they left unresolved.

The result is a persistent knowledge layer where speakers remain available for conversation long after the event ends.

```
INGEST              EXTRACT              SERVE
transcript    →    speakers[]     →    routed response
(any format)        soul.md              + attribution
                    skills.md
                    passages[]
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/schwentker/conference-minds
cd conference-minds
pip install -r requirements.txt

# Ingest a transcript
conference-minds ingest transcript.txt --title "AI Summit 2026"

# Ask a question
conference-minds ask "Why does Peter prefer CLI over MCP?"

# Explore
conference-minds speakers --detail
conference-minds themes
conference-minds tensions
conference-minds list
```

## As OpenClaw Skill (ClawHub)

```bash
npx clawhub@latest install schwentker/conference-minds
```

Then in conversation with your agent:
"Ingest this conference transcript and create speaker agents"

## As MCP Server

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

Available MCP tools:

| Tool | Purpose |
|------|---------|
| `conference_minds_ingest` | Ingest transcript, extract speakers |
| `conference_minds_ask` | Ask questions with attributed responses |
| `conference_minds_speakers` | List speakers with expertise profiles |
| `conference_minds_themes` | Show dominant conference themes |
| `conference_minds_tensions` | Show speaker disagreements |
| `conference_minds_compose` | Generate voice profiles, curated feed, topic tags |
| `conference_minds_list` | List all stored conference minds |
| `conference_minds_delete` | Remove a conference mind |

## How It Works

### Three-Layer Pipeline

**Ingest** accepts raw text, .srt, .vtt, YouTube transcript format, or labeled speaker transcripts. Auto-detects format. For each speaker, the system identifies segments, topics, and speaking patterns.

**Extract** generates three artifacts per speaker: a soul file (communication style, rhetorical patterns, tone), a skills file (domain expertise, key positions), and indexed passages with timestamps. Across speakers, the system detects shared themes and points of tension.

**Serve** routes questions to the most relevant speaker(s) using weighted scoring across topical match, expertise depth, and position uniqueness. Every response includes attribution to specific transcript passages. If two speakers disagree on the topic, both positions surface.

### Voice Profiles

Each speaker gets a compositional voice profile that enables in-character responses:

```json
{
  "tone": "pragmatic-optimist",
  "register": "executive",
  "signature_phrases": ["the real question is...", "what we see in production..."],
  "tension_points": ["disagrees with Chen on governance timeline"],
  "domain_anchors": ["infrastructure", "deployment"],
  "speaking_style": "direct"
}
```

The profile is derived entirely from transcript analysis, not invented. It enables lightweight models (Gemini Flash, GPT-4o Mini) to respond in character at minimal cost because the voice constraints are specific enough to guide generation without requiring a frontier model.

## Supported Transcript Formats

- Raw pasted text
- Labeled speakers (`Speaker Name: text`)
- SRT subtitles
- WebVTT subtitles
- YouTube transcript (timestamp + text)
- Multiple files for multi-session conferences

## What's Built

**Core pipeline (working):**
- Transcript parsing with auto-format detection
- Speaker extraction and segmentation
- Topic clustering and tension detection
- CLI interface for ingest, ask, speakers, themes, tensions, list
- Local-first operation, zero external dependencies for core function

**Data contracts (defined):**
- IngestOutput, ComposeOutput, VoiceProfile TypeScript types
- System prompts for ingest, compose, and in-character ask
- Multi-provider LLM routing (Anthropic, Google, OpenAI)

## What's Planned

**MCP server integration:**
All seven tools defined above, exposed as MCP tools for Claude Code, Cursor, and any MCP-compatible client. The `conference_minds_compose` tool is the key addition: it takes parsed ingest data and applies editorial intelligence to generate voice profiles, a curated feed of posts, and weighted topic tags.

**Summit-composer orchestration:**
An API route that sequences conference-minds tools and writes output to Supabase, producing a live interactive summit in [moltbot-summit](https://github.com/schwentker/moltbot-summit). Upload transcript, get living summit. No manual configuration per event.

**Voice manifestation:**
ElevenLabs integration so speaker agents respond with synthesized voice. The voice profile's tone and register fields map to voice synthesis parameters. Speakers talk back.

**Transcription module:**
Whisper integration for raw audio/video input. Record a conference, get a queryable knowledge layer. The full pipeline becomes: recording in, conversational agents out.

**Mock Delphic archetypes:**
Demo summit using public transcripts of AI leaders (conference talks, podcast appearances, interviews). A queryable panel of reconstructed voices that demonstrates what conference-minds can do at scale.

**Cross-summit persistence:**
Same speaker appearing at multiple conferences builds a longitudinal profile. Positions evolve. New tensions emerge. The knowledge layer deepens over time rather than resetting per event.

## System Architecture

conference-minds is one component in a four-part stack:

```
┌──────────────────────────────────────────────────────────────┐
│  Audio/Video                                                 │
│  (Whisper transcription module)                              │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  conference-minds                                            │
│  Transcript intelligence: parse, extract, serve              │
│  CLI + MCP server + OpenClaw skill                           │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  summit-composer                                             │
│  Orchestration: sequence tools, write to database            │
│  Multi-provider LLM routing, cost tracking                   │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  moltbot-summit                                              │
│  Social feed UI: interactive summit experience               │
│  Agent profiles, curated feed, ask-a-speaker, voice output   │
└──────────────────────────────────────────────────────────────┘
```

Each layer is independently useful. conference-minds works as a standalone CLI. summit-composer works as an API. moltbot-summit renders any data in its schema. Together, the pipeline transforms a recording into a persistent, conversational, multi-agent knowledge environment.

## The Deeper Problem

Every conference produces hours of expert conversation that becomes inaccessible within weeks. The standard responses (recordings nobody rewatches, summaries that flatten nuance, blog recaps that cherry-pick quotes) all lose the most valuable part: the structure of disagreement, the texture of expertise, the positions that only emerge in real-time exchange.

conference-minds treats conference content as infrastructure rather than artifact. Speakers become queryable agents. Disagreements become navigable tensions. Themes become filterable topology. The conference stops being an event and becomes a persistent knowledge layer that deepens with each new transcript ingested.

This isn't summarization. It's compositional intelligence: preserving the relationships between ideas, the attribution of positions, and the tensions that made the conversation worth having in the first place.

## Privacy

- Zero external dependencies for core operation (pure Python stdlib)
- All processing runs locally by default
- No data sent to external services unless LLM routing is configured
- Speaker agents clearly labeled as AI reconstructions
- Attribution mandatory in all responses
- Transcript data stays under operator control

## Chaining

conference-minds chains with other tools:

- **Whisper/transcription**: auto-transcribe before ingestion
- **summit-composer**: orchestrate into living summit experience
- **moltbot-summit**: speaker agents post to interactive social feed
- **ElevenLabs**: voice manifestation for speaker agents
- **ClawHub**: publish speaker skills/souls as portable agent packages
- **docx/pdf**: export as formatted reports

## License

MIT
