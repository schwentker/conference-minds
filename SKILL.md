---
name: conference-minds
version: 1.0.0
description: Transform conference transcripts into persistent, conversational speaker-agents. Ingest any transcript (pasted, file, or URL), extract speaker identities and positions, generate soul+skill files per speaker, and route questions to the most relevant voice with full attribution. Use when the user wants to "create agents from a conference," "talk to a speaker," "ingest a transcript," "build a summit mind," "conference-minds," or wants persistent conversational access to conference content. Works with meetups, podcasts, panels, keynotes, interviews, and any multi-speaker content.
author: schwentker
license: MIT
---

# conference-minds

Transform ephemeral conference content into persistent, conversational intelligence.

## What It Does

conference-minds takes a transcript (any format: raw paste, .txt, .md, .srt, .vtt, JSON) and produces a queryable knowledge layer where each speaker becomes a distinct conversational agent. Ask a question, get an answer attributed to the specific speaker whose position best addresses it, with a direct citation to the transcript passage.

## When To Use This Skill

- User pastes or uploads a conference transcript
- User says "ingest this talk" or "create agents from this panel"
- User wants to "ask Jensen about inference costs" after watching a keynote
- User references "conference-minds" or "summit mind" by name
- User wants to query a past event's content conversationally
- User uploads multiple transcripts to build a composite conference mind

## Architecture

### Three-Layer Pipeline

```
INGEST          EXTRACT           SERVE
transcript  ->  speakers[]    ->  routed response
                  soul.md           + attribution
                  skills.md
                  passages[]
```

### Layer 1: Ingest

Accepts transcript in any common format. Detects speaker labels automatically (e.g., "SPEAKER:", "John:", timestamps with names). Cleans formatting artifacts, merges broken lines, normalizes timestamps.

**Supported inputs:**
- Raw pasted text
- .txt, .md files
- .srt, .vtt subtitle files
- YouTube transcript format (timestamp + text)
- JSON structured transcripts
- Multiple files for multi-session conferences

### Layer 2: Extract

For each detected speaker:

1. **Identity**: Name, role (if mentioned), affiliation
2. **Soul file** (`{speaker}_soul.md`): Communication style, rhetorical patterns, key phrases, intellectual posture (contrarian, consensus-builder, technical, visionary)
3. **Skills file** (`{speaker}_skills.md`): Domain expertise areas, specific claims made, frameworks referenced, technologies discussed
4. **Passages index**: Every statement attributed to this speaker with timestamp/position reference

For the conference as a whole:
5. **Summit mind** (`summit_mind.md`): Composite themes, points of agreement/disagreement across speakers, emergent questions nobody asked

### Layer 3: Serve

When the user asks a question:

1. **Intent classification**: What domain does this question touch?
2. **Speaker routing**: Which speaker(s) have relevant expertise? Use weighted selection based on:
   - Direct topical match (speaker discussed this specific subject)
   - Expertise proximity (speaker's domain is adjacent)
   - Rhetorical stance (if user asks "who disagrees with X")
3. **Response generation**: Synthesize an answer in the speaker's voice using their soul file for tone and their passages for content
4. **Attribution**: Every claim links back to a specific transcript passage with position marker
5. **Multi-voice option**: For broad questions, present multiple speakers' perspectives

## Commands

### Ingest

```
conference-minds ingest <transcript>
conference-minds ingest --file path/to/transcript.txt
conference-minds ingest --name "Cisco AI Summit 2026"
conference-minds ingest --multi path/to/session1.txt path/to/session2.txt
```

### Query

```
conference-minds ask "What did the panel think about agent security?"
conference-minds ask "Who disagreed with the cloud-first approach?"
conference-minds ask --speaker "Peter Steinberger" "What's your view on MCP?"
```

### Explore

```
conference-minds speakers              # List all extracted speakers
conference-minds speakers --detail     # Show expertise areas per speaker
conference-minds themes                # Show emergent conference themes
conference-minds tensions              # Show points of disagreement
conference-minds export                # Export all soul/skill files
```

### Manage

```
conference-minds list                  # List all ingested conferences
conference-minds delete <conference>   # Remove a conference mind
conference-minds merge <conf1> <conf2> # Combine conferences into one mind
```

## File Structure

After ingestion, conference-minds creates:

```
~/.conference-minds/
  conferences/
    cisco-ai-summit-2026/
      meta.json                    # Conference metadata
      transcript_raw.md            # Original transcript preserved
      transcript_clean.md          # Cleaned, normalized version
      summit_mind.md               # Composite conference intelligence
      speakers/
        jensen-huang/
          soul.md                  # Communication style, personality
          skills.md                # Domain expertise, specific claims
          passages.json            # Indexed statements with positions
        pat-gelsinger/
          soul.md
          skills.md
          passages.json
      themes.json                  # Extracted conference themes
      tensions.json                # Points of disagreement
```

## Dependencies

### Required
- Python 3.10+
- No external API keys required for basic operation

### Optional (enhanced features)
- **Ollama** (local inference): For privacy-preserving speaker agent responses without API costs
- **OpenAI/Anthropic API key**: For higher-quality extraction and response generation
- **whisper/transcription skills**: Chain with audio transcription for end-to-end pipeline

## How It Works Under the Hood

### Speaker Detection Algorithm

1. Scan for repeated name patterns at line starts (e.g., "John:", "SPEAKER 1:")
2. Detect timestamp + name patterns from subtitle formats
3. Fall back to paragraph-level attribution using linguistic cues
4. Handle moderator/interviewer vs panelist distinction
5. Merge speaker references (e.g., "Dr. Smith" and "Smith" are the same person)

### Soul File Generation

Each speaker's soul.md captures:

```markdown
# {Speaker Name} - Communication Soul

## Voice
- Sentence structure: {short/complex/mixed}
- Vocabulary register: {technical/accessible/mixed}
- Rhetorical devices: {analogy-heavy, data-driven, story-led}
- Signature phrases: ["...", "..."]

## Intellectual Posture
- {contrarian | consensus-builder | provocateur | synthesizer | pragmatist}
- Key tensions they hold: [...]
- What they push back on: [...]

## Values (inferred)
- [extracted from positions taken and language used]
```

### Transit-Weighted Speaker Selection

When routing a question to the right speaker:

```
relevance_score = (
    topical_match * 0.5 +      # Did they discuss this topic?
    expertise_depth * 0.3 +      # How deeply did they go?
    recency_weight * 0.1 +       # More recent statements weighted slightly
    uniqueness * 0.1             # Did they say something others didn't?
)
```

Multiple speakers returned when scores are close, enabling "panel" responses.

### Attribution Format

Every response includes:

```
[Speaker Name, timestamp/position] "Paraphrased or quoted passage"
```

User can request full original passage for verification.

## Privacy and Ethics

- All processing can run locally via Ollama (no data leaves the machine)
- Original transcripts stored locally in ~/.conference-minds/
- No data sent to external services unless user explicitly configures API keys
- Speaker agents are clearly labeled as AI reconstructions, not the actual people
- Attribution is mandatory in all responses to prevent misrepresentation

## Chaining with Other Skills

conference-minds is designed to chain with the OpenClaw ecosystem:

- **whisper / transcription skills** -> auto-transcribe audio before ingestion
- **moltbook-interact** -> speaker-agents can post to Moltbook
- **elite-longterm-memory** -> persist context across sessions
- **duckduckgo-search / web search** -> enrich speaker profiles with external context
- **docx / pdf skills** -> export conference mind as formatted report

## Examples

### Basic: Ingest and Query

```
> conference-minds ingest --name "YC Interview: Peter Steinberger"
  [paste transcript]

Ingested: 1 speaker detected (Peter Steinberger)
  - 47 passages indexed
  - Expertise: local-first AI, agent architecture, CLI philosophy, swarm intelligence
  - Soul: contrarian, story-led, technically precise with accessible framing

> conference-minds ask "Why does Peter prefer CLI over MCP?"

[Peter Steinberger, 34:12] The preference is architectural, not ideological.
MCP servers require restarts when configurations change. CLIs do not. More
importantly, MCP was designed for bots while CLIs were designed for humans.
Agents turn out to be excellent at Unix. Building for humans first means
sufficiently capable agents adapt naturally.

Source: passages 31-33 of transcript
```

### Advanced: Multi-Conference Merge

```
> conference-minds merge "Cisco AI Summit" "OpenClaw Meetup Feb 5"

Merged: 14 speakers across 2 events
New tensions detected:
  - Cloud-first (Cisco speakers) vs Local-first (OpenClaw community)
  - Enterprise governance vs Individual sovereignty
  - Agent orchestration vs Agent autonomy

> conference-minds ask "Where do enterprise and open-source agent visions diverge?"

[Panel response - 3 speakers]
...
```
