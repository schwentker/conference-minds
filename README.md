# conference-minds

**Transform ephemeral conference content into persistent, conversational intelligence.**

conference-minds takes any transcript and produces a queryable knowledge layer where each speaker becomes a distinct conversational agent. Ask a question, get an answer attributed to the specific speaker whose position best addresses it.

Conferences generate enormous signal that evaporates within days. Recordings exist but nobody rewatches them. Summaries flatten the disagreements that made the conversation valuable. conference-minds preserves the texture: who said what, where they disagreed, what positions they actually held, and what questions they left unresolved.

## Status

**Core pipeline exists.** Speaker extraction, theme detection, tension detection, and question routing are implemented as heuristic/keyword-based processing in pure Python. No external API calls required for basic operation. CLI and MCP server code are written but not yet tested end-to-end.

This is pre-launch infrastructure. The architecture is sound, the data flow is defined, the code compiles. What's missing is the wiring: end-to-end testing, tutorial documentation, LLM-enhanced extraction, and integration with the broader summit-composer pipeline.

## What's Built

**Core library** (`src/core.py`):
- Transcript format auto-detection (raw text, labeled speakers, SRT, VTT, YouTube)
- Speaker extraction and segmentation
- Soul generation (communication style, rhetorical patterns) via heuristic analysis
- Skills extraction (domain expertise mapping) via keyword frequency
- Theme detection across speakers
- Tension detection between speakers
- Question routing with weighted scoring (topical match, expertise depth, uniqueness)
- Response formatting with passage attribution
- Local file persistence (`~/.conference-minds/conferences/`)

**CLI** (`scripts/cli.py`):
- `ingest`, `ask`, `speakers`, `themes`, `tensions`, `list`, `export`, `delete` commands
- Written, not yet tested end-to-end with real transcripts

**MCP server** (`scripts/mcp_server.py`):
- Seven tools defined via FastMCP with proper annotations and input schemas
- `conference_minds_ingest`, `conference_minds_ask`, `conference_minds_speakers`, `conference_minds_themes`, `conference_minds_tensions`, `conference_minds_list`, `conference_minds_delete`
- Code exists, untested with any MCP client

**OpenClaw skill** (`SKILL.md`, `package.json`):
- ClawHub skill definition written
- Not yet published

**All processing runs locally. Zero external dependencies for core operation (pure Python stdlib). No data sent to external services.**

## What's Not Built Yet

Everything below is planned architecture, not working code.

**LLM-enhanced extraction**: Current pipeline is heuristic-only. Voice profiles, compositional feed generation, and in-character agent responses all require LLM calls. The system prompts and data contracts are defined (in summit-composer), but not wired into conference-minds.

**MCP server integration**: The seven tools exist as code but have not been tested with Claude Desktop, Cursor, or any MCP client. The `conference_minds_compose` tool (generates voice profiles, curated feed, topic tags) is specified but not implemented.

**End-to-end testing**: No tutorial exists. No verified workflow from raw transcript to attributed response. This is the most immediate gap.

**Vector store**: Speaker passages are currently stored as flat JSON files. No embedding, no semantic search, no cross-conference retrieval.

## Architecture

```
INGEST              EXTRACT              SERVE
transcript    →    speakers[]     →    routed response
(any format)        soul.md              + attribution
                    skills.md
                    passages[]
```

**Ingest** accepts raw text, .srt, .vtt, YouTube format, or labeled speaker transcripts. Auto-detects format. Cleans filler, merges consecutive segments from same speaker.

**Extract** generates three artifacts per speaker: a soul file (communication style, rhetorical patterns, tone), a skills file (domain expertise, key positions), and indexed passages. Across speakers, the system detects shared themes and points of tension. Currently heuristic. LLM-enhanced extraction on roadmap.

**Serve** routes questions to the most relevant speaker(s) using weighted scoring. Every response includes attribution to specific transcript passages. If two speakers disagree on the topic, both positions surface.

## Supported Transcript Formats

- Raw pasted text
- Labeled speakers (`Speaker Name: text`)
- SRT subtitles
- WebVTT subtitles
- YouTube transcript (timestamp + text)
- Multiple files for multi-session conferences

## Planned Usage

*These interfaces are written but not yet verified. Included here to show intended interaction patterns.*

### CLI

```bash
# Ingest a transcript
conference-minds ingest --name "AI Summit 2026" --file transcript.txt

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
"Ingest this conference transcript and create speaker agents"

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

## Part of a Larger System

conference-minds is the intelligence layer in a four-part stack:

```
┌──────────────────────────────────────────────────────────────┐
│  Transcription Module                                        │
│  Audio/video → text (Whisper)                                │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  conference-minds                  ◄── YOU ARE HERE          │
│  Transcript → speakers, themes, tensions, attributed Q&A     │
│  CLI + MCP server + OpenClaw skill                           │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  summit-composer                                             │
│  Orchestration: sequence tools, write to Supabase            │
│  Multi-provider LLM routing, cost tracking                   │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  moltbot-summit                                              │
│  Social feed UI: interactive summit experience               │
│  Agent profiles, curated feed, voice output (ElevenLabs)     │
└──────────────────────────────────────────────────────────────┘
```

## Roadmap

### Immediate (hackathon sprint)

- **End-to-end verification and tutorial**: Test full CLI pipeline with real transcripts. Document the complete workflow from raw transcript to attributed response. Make first-run experience seamless.
- **LLM-enhanced extraction**: Wire multi-provider LLM client (Gemini Flash for parsing, Gemini Pro for voice profiles). Replace heuristic soul/skills generation with compositional analysis that captures actual speaker voice.
- **MCP server testing**: Verify all seven tools with Claude Desktop. Fix whatever breaks.
- **summit-composer integration**: Connect ingest/compose output to Supabase writes. Transcript in, living summit out, one API call.
- **Voice manifestation**: ElevenLabs integration so speaker agents respond with synthesized voice matching their tone and register.
- **Mock Delphic archetypes**: Demo summit using public transcripts of AI leaders. A queryable panel that shows what conference-minds does at full capability.

### Near-term

- **Vector store per conference**: Embed speaker passages using pgvector (Supabase) or Pinecone for semantic retrieval. Each conference gets its own vector index, enabling "find everything this speaker said about governance" queries that go beyond keyword matching. Embedding model: likely `text-embedding-3-small` for cost efficiency, upgradeable.
- **Global vector index**: Unified embedding space across all ingested conferences. This unlocks three capabilities that flat storage cannot deliver. First, thematic search across events: "everyone who has discussed AI governance" returns attributed passages from different speakers at different conferences, ranked by relevance. Second, speaker trajectory tracking: the same person's positions across multiple appearances, showing how their thinking evolved. Third, cross-event tension mapping: where the same fundamental disagreement surfaces independently at different conferences, revealing structural fault lines in a field rather than individual opinions.
- **Cross-summit persistence**: Same speaker at multiple conferences builds a longitudinal profile. Positions evolve. New tensions emerge. The knowledge layer deepens rather than resetting per event.
- **Feed regeneration**: Re-compose a summit with different editorial approaches. A/B test which narrative arc produces the most engagement.
- **ClawHub publishing**: Speaker skills and souls as portable agent packages.

### Far Horizon: Absorption Intelligence

conference-minds began as a transcript tool, but the trajectory points somewhere more fundamental.

The original version of this idea was attempted at Buildspace in 2023: a system that could watch hackathon demo videos and produce structured intelligence. Not summaries. Absorption. The system would parse voice, video, slides, and live coding simultaneously, then reason about what it observed. What is this team actually building vs. what they claim? Where does this approach break under scale? Which technical decisions reveal deeper architectural assumptions? What would a senior mentor say after watching this demo?

The timing was wrong in 2023. Multi-modal models could not handle simultaneous video, audio, and code parsing with the coherence required for genuine reasoning. Context windows were too small for full demo sessions. The cost of running inference across modalities made it impractical outside research budgets.

The timing is converging now. Gemini and Claude handle multi-modal input natively. Context windows accommodate full presentations. Cost per token has dropped by orders of magnitude. But the missing piece was never the models themselves. It was the compositional layer: the system that knows how to decompose a demo into speaker intent, technical claims, architectural decisions, and unstated assumptions, then synthesize across all of them into actionable intelligence.

That compositional layer is what conference-minds is building. Today it processes text transcripts. The architecture (speaker extraction, expertise profiling, tension detection, attributed routing) is modality-agnostic by design. When the input expands from transcript to video+audio+slides+code, the extraction layer changes but the compositional intelligence stays the same.

The far-horizon version: point conference-minds at a hackathon demo stream. It watches. It absorbs. It identifies what each team is actually building, which often differs from what they present. It detects technical risks the team has not surfaced. It maps where this approach has been tried before and what happened. It generates the mentorship that most teams never get access to: specific, informed, grounded in what was actually demonstrated rather than what was pitched. Absorption, reasoning, reflection, prediction, and recommendation applied to live creative output. The conference-minds pipeline is the foundation.

## Privacy

- Zero external dependencies for core operation (pure Python stdlib)
- All processing runs locally by default
- No data sent to external services unless LLM routing is explicitly configured
- Speaker agents clearly labeled as AI reconstructions
- Attribution mandatory in all responses
- Transcript data stays under operator control

## Chaining

conference-minds chains with other tools:

- **Whisper/transcription**: auto-transcribe audio/video before ingestion
- **summit-composer**: orchestrate into living summit experience
- **moltbot-summit**: speaker agents post to interactive social feed
- **ElevenLabs**: voice manifestation for speaker agents
- **ClawHub**: publish speaker skills/souls as portable agent packages
- **docx/pdf**: export as formatted reports

## License

MIT