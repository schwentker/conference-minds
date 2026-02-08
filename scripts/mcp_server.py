"""
conference-minds MCP Server

Exposes conference-minds functionality as MCP tools for use with
Claude Code, Cursor, Windsurf, OpenClaw (via MakePorter), and any
MCP-compatible client.

Install:
    pip install mcp pydantic

Run:
    python -m conference_minds_mcp          # stdio transport (local)
    python -m conference_minds_mcp --http   # HTTP transport (remote)

Configure in claude_desktop_config.json or .mcp.json:
    {
      "mcpServers": {
        "conference-minds": {
          "command": "python",
          "args": ["-m", "conference_minds_mcp"]
        }
      }
    }
"""

import json
import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core import (
    ingest, ask, list_minds, load_mind, 
    get_minds_dir, slugify, detect_themes, detect_tensions
)

# ─── Server Init ───────────────────────────────────────────────

mcp = FastMCP("conference_minds_mcp")


# ─── Input Models ──────────────────────────────────────────────

class IngestInput(BaseModel):
    """Input for ingesting a conference transcript."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    transcript: str = Field(
        ..., 
        description="The full transcript text to ingest. Supports raw text, SRT, VTT, YouTube timestamp format, or labeled speaker format (e.g., 'Speaker Name: text').",
        min_length=50
    )
    name: str = Field(
        default="",
        description="Name for this conference/event (e.g., 'Cisco AI Summit 2026'). Auto-generated if not provided.",
        max_length=200
    )
    source: str = Field(
        default="",
        description="Source attribution (e.g., 'YC Interview', 'YouTube', 'live recording').",
        max_length=200
    )


class AskInput(BaseModel):
    """Input for asking a question of a conference mind."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    question: str = Field(
        ...,
        description="The question to ask. Will be routed to the most relevant speaker(s) with attributed responses.",
        min_length=3,
        max_length=1000
    )
    conference: str = Field(
        default="",
        description="Name of the conference to query. If empty, uses the most recently ingested conference."
    )
    speaker: Optional[str] = Field(
        default=None,
        description="Target a specific speaker by name (e.g., 'Peter Steinberger'). If empty, routes to best matching speaker(s)."
    )


class ConferenceInput(BaseModel):
    """Input for conference-specific queries."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    conference: str = Field(
        default="",
        description="Conference name. If empty, uses the most recently ingested."
    )


class DeleteInput(BaseModel):
    """Input for deleting a conference mind."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    name: str = Field(
        ...,
        description="Name of the conference to delete.",
        min_length=1
    )


# ─── Tools ─────────────────────────────────────────────────────

@mcp.tool(
    name="conference_minds_ingest",
    annotations={
        "title": "Ingest Conference Transcript",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def tool_ingest(params: IngestInput) -> str:
    """Ingest a conference transcript and create speaker-agents.
    
    Accepts transcripts in any format (raw text, SRT, VTT, YouTube, labeled speakers).
    Extracts speakers, generates soul profiles and skill maps, detects themes and tensions.
    Returns a summary of what was extracted.
    """
    try:
        mind = ingest(
            transcript=params.transcript,
            name=params.name,
            source_file=params.source
        )
        
        result = f"## Ingested: {mind.name}\n\n"
        result += f"**Speakers:** {len(mind.speakers)}\n\n"
        
        for s in mind.speakers:
            skills_str = ', '.join(sk['domain'] for sk in s.skills[:3]) if s.skills else 'general'
            result += f"- **{s.name}**: {len(s.passages)} passages | Expertise: {skills_str}\n"
        
        result += f"\n**Themes:** {len(mind.themes)}\n"
        for t in mind.themes[:5]:
            result += f"- {t['theme']} ({t['frequency']} mentions)\n"
        
        if mind.tensions:
            result += f"\n**Tensions:** {len(mind.tensions)}\n"
            for t in mind.tensions:
                result += f"- {' vs '.join(t['speakers'])}\n"
        
        result += f"\nSaved to: ~/.conference-minds/conferences/{slugify(mind.name)}/"
        return result
        
    except Exception as e:
        return f"Error ingesting transcript: {str(e)}"


@mcp.tool(
    name="conference_minds_ask",
    annotations={
        "title": "Ask a Conference Mind",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_ask(params: AskInput) -> str:
    """Ask a question and get attributed responses from conference speakers.
    
    Routes the question to the most relevant speaker(s) based on topical match,
    expertise depth, and passage content. Returns responses with full attribution
    to specific transcript passages.
    """
    conference = params.conference
    if not conference:
        minds = list_minds()
        if not minds:
            return "No conferences ingested yet. Use conference_minds_ingest first."
        conference = minds[-1]['name']
    
    response = ask(params.question, conference, params.speaker)
    return response


@mcp.tool(
    name="conference_minds_speakers",
    annotations={
        "title": "List Conference Speakers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_speakers(params: ConferenceInput) -> str:
    """List all speakers in a conference mind with their expertise areas and voice profiles."""
    conference = params.conference
    if not conference:
        minds = list_minds()
        if not minds:
            return "No conferences ingested yet."
        conference = minds[-1]['name']
    
    mind = load_mind(conference)
    if not mind:
        return f"Conference '{conference}' not found."
    
    result = f"## Speakers in: {mind.name}\n\n"
    for s in mind.speakers:
        result += f"### {s.name}\n"
        result += f"- Passages: {len(s.passages)}\n"
        if s.soul and isinstance(s.soul, dict) and 'voice' in s.soul:
            voice = s.soul['voice']
            result += f"- Voice: {voice.get('sentence_structure', 'unknown')}, {voice.get('vocabulary_register', 'unknown')}\n"
        if s.skills:
            for sk in s.skills[:5]:
                result += f"- {sk['domain']}: {sk['strength']}\n"
        result += "\n"
    
    return result


@mcp.tool(
    name="conference_minds_themes",
    annotations={
        "title": "Show Conference Themes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_themes(params: ConferenceInput) -> str:
    """Show the dominant themes extracted from a conference transcript."""
    conference = params.conference
    if not conference:
        minds = list_minds()
        if not minds:
            return "No conferences ingested yet."
        conference = minds[-1]['name']
    
    mind = load_mind(conference)
    if not mind:
        return f"Conference '{conference}' not found."
    
    result = f"## Themes in: {mind.name}\n\n"
    for t in mind.themes[:15]:
        bar = '█' * min(t['frequency'], 30)
        result += f"- **{t['theme']}** {bar} ({t['frequency']})\n"
    
    return result


@mcp.tool(
    name="conference_minds_tensions",
    annotations={
        "title": "Show Speaker Tensions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_tensions(params: ConferenceInput) -> str:
    """Show detected disagreements and tensions between speakers."""
    conference = params.conference
    if not conference:
        minds = list_minds()
        if not minds:
            return "No conferences ingested yet."
        conference = minds[-1]['name']
    
    mind = load_mind(conference)
    if not mind:
        return f"Conference '{conference}' not found."
    
    if not mind.tensions:
        return f"No strong tensions detected in {mind.name}."
    
    result = f"## Tensions in: {mind.name}\n\n"
    for t in mind.tensions:
        result += f"- **{' vs '.join(t['speakers'])}**: {t['note']}\n"
    
    return result


@mcp.tool(
    name="conference_minds_list",
    annotations={
        "title": "List All Conference Minds",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_list() -> str:
    """List all ingested conference minds with metadata."""
    minds = list_minds()
    if not minds:
        return "No conferences ingested yet. Use conference_minds_ingest to add one."
    
    result = "## Stored Conference Minds\n\n"
    for m in minds:
        result += f"- **{m['name']}**\n"
        result += f"  Speakers: {m.get('speaker_count', '?')} | Created: {m.get('created', 'unknown')[:10]}\n\n"
    
    return result


@mcp.tool(
    name="conference_minds_delete",
    annotations={
        "title": "Delete Conference Mind",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def tool_delete(params: DeleteInput) -> str:
    """Delete a conference mind and all its associated data."""
    import shutil
    slug = slugify(params.name)
    conf_dir = get_minds_dir() / slug
    
    if not conf_dir.exists():
        return f"Conference '{params.name}' not found."
    
    shutil.rmtree(conf_dir)
    return f"Deleted: {params.name}"


# ─── Entry Point ───────────────────────────────────────────────

if __name__ == "__main__":
    transport = "stdio"
    if "--http" in sys.argv:
        transport = "streamable-http"
    
    mcp.run(transport=transport)
