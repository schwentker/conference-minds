"""
conference_minds - Core library for transforming conference transcripts 
into persistent, conversational speaker-agents.

Architecture:
    Ingest (transcript in) -> Extract (speakers, souls, skills) -> Serve (routed query responses)
"""

import json
import re
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


# ─── Data Models ────────────────────────────────────────────────

@dataclass
class Passage:
    """A single attributed statement from a speaker."""
    speaker: str
    text: str
    position: int          # line or segment number in transcript
    timestamp: str = ""    # original timestamp if available
    topics: list = field(default_factory=list)

@dataclass 
class Speaker:
    """Extracted speaker with soul, skills, and passages."""
    name: str
    role: str = ""
    affiliation: str = ""
    passages: list = field(default_factory=list)     # list of Passage
    soul: dict = field(default_factory=dict)          # communication style
    skills: list = field(default_factory=list)        # expertise areas
    claims: list = field(default_factory=list)        # specific assertions made
    signature_phrases: list = field(default_factory=list)

@dataclass
class ConferenceMind:
    """A complete conference mind with all speakers and metadata."""
    name: str
    created: str = ""
    source_file: str = ""
    speakers: list = field(default_factory=list)      # list of Speaker
    themes: list = field(default_factory=list)
    tensions: list = field(default_factory=list)
    raw_transcript: str = ""
    clean_transcript: str = ""


# ─── Configuration ──────────────────────────────────────────────

MINDS_DIR = Path.home() / ".conference-minds" / "conferences"


def get_minds_dir() -> Path:
    """Get and ensure the conference minds storage directory exists."""
    MINDS_DIR.mkdir(parents=True, exist_ok=True)
    return MINDS_DIR


def slugify(text: str) -> str:
    """Convert text to filesystem-safe slug."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug.strip('-')


# ─── Layer 1: Ingest ───────────────────────────────────────────

def detect_format(text: str) -> str:
    """Detect transcript format: srt, vtt, youtube, labeled, raw."""
    lines = text.strip().split('\n')[:20]  # check first 20 lines
    
    # SRT: numbered lines followed by timestamp with -->
    if any(re.match(r'^\d+$', l.strip()) for l in lines[:5]):
        if any('-->' in l for l in lines[:10]):
            return 'srt'
    
    # VTT: starts with WEBVTT
    if lines and lines[0].strip().startswith('WEBVTT'):
        return 'vtt'
    
    # YouTube: timestamp format like 0:00 or 00:00
    if any(re.match(r'^\d{1,2}:\d{2}', l.strip()) for l in lines[:10]):
        return 'youtube'
    
    # Labeled: "Name:" pattern at start of lines
    label_pattern = re.compile(r'^[A-Z][a-zA-Z\s\.]+:')
    label_count = sum(1 for l in lines if label_pattern.match(l.strip()))
    if label_count >= 3:
        return 'labeled'
    
    return 'raw'


def clean_transcript(text: str, fmt: str) -> str:
    """Clean and normalize transcript based on detected format."""
    if fmt == 'srt':
        return _clean_srt(text)
    elif fmt == 'vtt':
        return _clean_vtt(text)
    elif fmt == 'youtube':
        return _clean_youtube(text)
    else:
        return _clean_raw(text)


def _clean_srt(text: str) -> str:
    """Clean SRT subtitle format."""
    lines = text.strip().split('\n')
    cleaned = []
    skip_next = False
    for line in lines:
        line = line.strip()
        if re.match(r'^\d+$', line):
            continue
        if '-->' in line:
            continue
        if line:
            cleaned.append(line)
    return '\n'.join(cleaned)


def _clean_vtt(text: str) -> str:
    """Clean WebVTT format."""
    lines = text.strip().split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if line.startswith('WEBVTT') or line.startswith('NOTE'):
            continue
        if '-->' in line:
            continue
        if re.match(r'^\d{2}:\d{2}', line):
            continue
        if line:
            cleaned.append(line)
    return '\n'.join(cleaned)


def _clean_youtube(text: str) -> str:
    """Clean YouTube transcript format (timestamp + text)."""
    lines = text.strip().split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        # Remove leading timestamp like "0:00" or "1:23:45"
        cleaned_line = re.sub(r'^\d{1,2}:\d{2}(:\d{2})?\s*', '', line)
        if cleaned_line:
            cleaned.append(cleaned_line)
    return '\n'.join(cleaned)


def _clean_raw(text: str) -> str:
    """Clean raw unformatted text."""
    lines = text.strip().split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned.append(line)
    return '\n'.join(cleaned)


# ─── Layer 2: Extract ──────────────────────────────────────────

def extract_speakers(clean_text: str) -> list:
    """Extract speaker names and their passages from cleaned transcript."""
    speakers_dict = {}
    current_speaker = "Unknown"
    current_text = []
    position = 0
    
    # Pattern: "Name:" or "SPEAKER NAME:" at start of line
    speaker_pattern = re.compile(r'^([A-Z][a-zA-Z\s\.\']+?):\s*(.*)')
    
    for line in clean_text.split('\n'):
        match = speaker_pattern.match(line.strip())
        if match:
            # Save previous speaker's passage
            if current_text:
                _add_passage(speakers_dict, current_speaker, 
                           ' '.join(current_text), position)
                position += 1
            
            current_speaker = match.group(1).strip()
            remaining = match.group(2).strip()
            current_text = [remaining] if remaining else []
        else:
            if line.strip():
                current_text.append(line.strip())
    
    # Don't forget the last passage
    if current_text:
        _add_passage(speakers_dict, current_speaker, 
                   ' '.join(current_text), position)
    
    # Convert to Speaker objects
    speakers = []
    for name, passages in speakers_dict.items():
        speaker = Speaker(
            name=name,
            passages=passages
        )
        speakers.append(speaker)
    
    return speakers


def _add_passage(speakers_dict: dict, name: str, text: str, position: int):
    """Add a passage to the speakers dictionary."""
    if name not in speakers_dict:
        speakers_dict[name] = []
    speakers_dict[name].append(Passage(
        speaker=name,
        text=text,
        position=position
    ))


def generate_soul(speaker: Speaker) -> dict:
    """Generate a soul profile from a speaker's passages.
    
    Returns a dict that can be written as soul.md.
    For basic operation this uses heuristics.
    When LLM is available, this gets enhanced significantly.
    """
    all_text = ' '.join(p.text for p in speaker.passages)
    words = all_text.split()
    word_count = len(words)
    
    # Sentence structure analysis
    sentences = re.split(r'[.!?]+', all_text)
    avg_sentence_len = sum(len(s.split()) for s in sentences if s.strip()) / max(len(sentences), 1)
    
    if avg_sentence_len < 12:
        structure = "concise, direct"
    elif avg_sentence_len < 20:
        structure = "balanced, measured"
    else:
        structure = "complex, expansive"
    
    # Question frequency (rhetorical engagement)
    question_count = all_text.count('?')
    question_ratio = question_count / max(len(sentences), 1)
    
    # Technical vocabulary detection
    tech_terms = ['algorithm', 'infrastructure', 'protocol', 'API', 'model', 
                  'architecture', 'deploy', 'inference', 'latency', 'compute',
                  'runtime', 'framework', 'pipeline', 'endpoint', 'cluster',
                  'GPU', 'token', 'vector', 'embedding', 'fine-tune']
    tech_count = sum(1 for word in words if word.lower().strip('.,;:') in 
                     [t.lower() for t in tech_terms])
    tech_density = tech_count / max(word_count, 1)
    
    if tech_density > 0.03:
        register = "highly technical"
    elif tech_density > 0.01:
        register = "technical-accessible blend"
    else:
        register = "accessible, general audience"
    
    # Extract potential signature phrases (repeated n-grams)
    bigrams = [' '.join(words[i:i+2]).lower() for i in range(len(words)-1)]
    from collections import Counter
    bigram_counts = Counter(bigrams)
    signature = [phrase for phrase, count in bigram_counts.most_common(10) 
                 if count >= 3 and len(phrase) > 5]
    
    soul = {
        'name': speaker.name,
        'voice': {
            'sentence_structure': structure,
            'vocabulary_register': register,
            'question_frequency': 'high' if question_ratio > 0.15 else 'moderate' if question_ratio > 0.05 else 'low',
            'avg_sentence_length': round(avg_sentence_len, 1),
        },
        'signature_phrases': signature[:5],
        'passage_count': len(speaker.passages),
        'word_count': word_count,
    }
    
    speaker.soul = soul
    return soul


def extract_skills(speaker: Speaker) -> list:
    """Extract expertise areas from speaker's passages.
    
    Basic keyword clustering. Enhanced significantly with LLM.
    """
    all_text = ' '.join(p.text for p in speaker.passages).lower()
    
    # Domain keyword clusters
    domains = {
        'AI/ML': ['ai', 'machine learning', 'neural', 'model', 'training', 'inference', 'llm', 'gpt', 'claude', 'agent'],
        'Infrastructure': ['cloud', 'server', 'deploy', 'kubernetes', 'docker', 'infrastructure', 'compute', 'gpu', 'cluster'],
        'Security': ['security', 'privacy', 'encryption', 'auth', 'vulnerability', 'trust', 'permission'],
        'Product': ['user', 'product', 'feature', 'experience', 'interface', 'design', 'customer'],
        'Business': ['revenue', 'market', 'strategy', 'growth', 'enterprise', 'startup', 'investment', 'valuation'],
        'Open Source': ['open source', 'github', 'community', 'contributor', 'fork', 'repository', 'license'],
        'Education': ['learn', 'teach', 'student', 'course', 'curriculum', 'training', 'workshop'],
        'Governance': ['policy', 'regulation', 'compliance', 'governance', 'ethics', 'responsible'],
    }
    
    skills = []
    for domain, keywords in domains.items():
        hits = sum(all_text.count(kw) for kw in keywords)
        if hits >= 3:
            skills.append({
                'domain': domain,
                'strength': 'strong' if hits >= 10 else 'moderate',
                'hit_count': hits
            })
    
    skills.sort(key=lambda x: x['hit_count'], reverse=True)
    speaker.skills = skills
    return skills


def detect_themes(speakers: list) -> list:
    """Detect cross-speaker themes from all passages."""
    all_text = ' '.join(
        p.text for s in speakers for p in s.passages
    ).lower()
    
    # Simple theme detection via keyword frequency
    words = re.findall(r'\b[a-z]{4,}\b', all_text)
    from collections import Counter
    word_freq = Counter(words)
    
    # Filter common stop words and return top themes
    stop_words = {'that', 'this', 'with', 'have', 'from', 'they', 'been',
                  'were', 'their', 'will', 'would', 'could', 'should',
                  'about', 'which', 'there', 'when', 'what', 'your',
                  'just', 'like', 'know', 'think', 'going', 'really',
                  'very', 'also', 'some', 'more', 'than', 'then',
                  'into', 'other', 'people', 'because', 'something'}
    
    themes = [
        {'theme': word, 'frequency': count}
        for word, count in word_freq.most_common(50)
        if word not in stop_words and count >= 5
    ][:15]
    
    return themes


def detect_tensions(speakers: list) -> list:
    """Detect potential disagreements between speakers.
    
    Basic: looks for contrasting language patterns.
    Enhanced significantly with LLM analysis.
    """
    tensions = []
    
    # Compare each pair of speakers
    for i, s1 in enumerate(speakers):
        for s2 in speakers[i+1:]:
            s1_text = ' '.join(p.text for p in s1.passages).lower()
            s2_text = ' '.join(p.text for p in s2.passages).lower()
            
            # Look for contrastive markers
            contrast_markers = ['however', 'disagree', 'but actually', 
                              'on the contrary', 'not necessarily',
                              'i would argue', 'the problem with']
            
            s1_contrasts = sum(s1_text.count(m) for m in contrast_markers)
            s2_contrasts = sum(s2_text.count(m) for m in contrast_markers)
            
            if s1_contrasts + s2_contrasts >= 3:
                tensions.append({
                    'speakers': [s1.name, s2.name],
                    'contrast_signals': s1_contrasts + s2_contrasts,
                    'note': 'Potential disagreement detected via linguistic markers'
                })
    
    return tensions


# ─── Layer 3: Serve ────────────────────────────────────────────

def route_question(question: str, mind: ConferenceMind, 
                   target_speaker: str = None) -> list:
    """Route a question to the most relevant speaker(s).
    
    Returns list of (speaker, relevance_score, relevant_passages) tuples.
    """
    question_lower = question.lower()
    question_words = set(re.findall(r'\b[a-z]{3,}\b', question_lower))
    
    results = []
    
    for speaker in mind.speakers:
        # Skip if user requested specific speaker and this isn't them
        if target_speaker and target_speaker.lower() not in speaker.name.lower():
            continue
        
        # Score each passage for relevance
        passage_scores = []
        for passage in speaker.passages:
            passage_words = set(re.findall(r'\b[a-z]{3,}\b', passage.text.lower()))
            overlap = len(question_words & passage_words)
            score = overlap / max(len(question_words), 1)
            if score > 0.1:
                passage_scores.append((passage, score))
        
        passage_scores.sort(key=lambda x: x[1], reverse=True)
        
        if passage_scores:
            top_score = passage_scores[0][1]
            top_passages = [p for p, s in passage_scores[:3]]
            
            # Weight by expertise match
            skill_bonus = 0
            for skill in speaker.skills:
                skill_words = set(skill['domain'].lower().split('/'))
                if skill_words & question_words:
                    skill_bonus += 0.2
            
            final_score = top_score * 0.7 + skill_bonus * 0.3
            results.append((speaker, final_score, top_passages))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:3]  # top 3 speakers


def format_response(results: list, question: str) -> str:
    """Format routed results into a readable attributed response."""
    if not results:
        return "No speakers found with relevant content for this question."
    
    parts = []
    for speaker, score, passages in results:
        parts.append(f"**{speaker.name}** (relevance: {score:.0%})")
        for p in passages[:2]:
            timestamp = f", {p.timestamp}" if p.timestamp else f", position {p.position}"
            parts.append(f'  [{speaker.name}{timestamp}] "{p.text[:300]}{"..." if len(p.text) > 300 else ""}"')
        parts.append("")
    
    return '\n'.join(parts)


# ─── Persistence ───────────────────────────────────────────────

def save_mind(mind: ConferenceMind) -> Path:
    """Save a ConferenceMind to disk."""
    slug = slugify(mind.name)
    conf_dir = get_minds_dir() / slug
    conf_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metadata
    meta = {
        'name': mind.name,
        'created': mind.created,
        'source_file': mind.source_file,
        'speaker_count': len(mind.speakers),
        'themes': mind.themes,
        'tensions': mind.tensions,
    }
    (conf_dir / 'meta.json').write_text(json.dumps(meta, indent=2))
    
    # Save transcripts
    (conf_dir / 'transcript_raw.md').write_text(mind.raw_transcript)
    (conf_dir / 'transcript_clean.md').write_text(mind.clean_transcript)
    
    # Save speakers
    speakers_dir = conf_dir / 'speakers'
    for speaker in mind.speakers:
        speaker_dir = speakers_dir / slugify(speaker.name)
        speaker_dir.mkdir(parents=True, exist_ok=True)
        
        # Soul file
        soul_md = f"# {speaker.name} - Communication Soul\n\n"
        if speaker.soul:
            soul_md += f"## Voice\n"
            for k, v in speaker.soul.get('voice', {}).items():
                soul_md += f"- {k}: {v}\n"
            soul_md += f"\n## Signature Phrases\n"
            for phrase in speaker.soul.get('signature_phrases', []):
                soul_md += f"- \"{phrase}\"\n"
        (speaker_dir / 'soul.md').write_text(soul_md)
        
        # Skills file
        skills_md = f"# {speaker.name} - Expertise\n\n"
        for skill in speaker.skills:
            skills_md += f"- **{skill['domain']}**: {skill['strength']} ({skill['hit_count']} references)\n"
        (speaker_dir / 'skills.md').write_text(skills_md)
        
        # Passages index
        passages_data = [asdict(p) for p in speaker.passages]
        (speaker_dir / 'passages.json').write_text(json.dumps(passages_data, indent=2))
    
    # Save themes and tensions
    (conf_dir / 'themes.json').write_text(json.dumps(mind.themes, indent=2))
    (conf_dir / 'tensions.json').write_text(json.dumps(mind.tensions, indent=2))
    
    # Summit mind composite
    summit_md = f"# {mind.name} - Summit Mind\n\n"
    summit_md += f"Created: {mind.created}\n"
    summit_md += f"Speakers: {len(mind.speakers)}\n\n"
    summit_md += "## Themes\n"
    for t in mind.themes[:10]:
        summit_md += f"- {t['theme']} ({t['frequency']} mentions)\n"
    summit_md += "\n## Tensions\n"
    for t in mind.tensions:
        summit_md += f"- {' vs '.join(t['speakers'])}: {t['note']}\n"
    summit_md += "\n## Speakers\n"
    for s in mind.speakers:
        summit_md += f"- **{s.name}**: {len(s.passages)} passages"
        if s.skills:
            summit_md += f" | {', '.join(sk['domain'] for sk in s.skills[:3])}"
        summit_md += "\n"
    (conf_dir / 'summit_mind.md').write_text(summit_md)
    
    return conf_dir


def load_mind(name: str) -> Optional[ConferenceMind]:
    """Load a ConferenceMind from disk by name or slug."""
    slug = slugify(name)
    conf_dir = get_minds_dir() / slug
    
    if not conf_dir.exists():
        return None
    
    meta = json.loads((conf_dir / 'meta.json').read_text())
    
    mind = ConferenceMind(
        name=meta['name'],
        created=meta.get('created', ''),
        source_file=meta.get('source_file', ''),
        themes=meta.get('themes', []),
        tensions=meta.get('tensions', []),
    )
    
    if (conf_dir / 'transcript_raw.md').exists():
        mind.raw_transcript = (conf_dir / 'transcript_raw.md').read_text()
    if (conf_dir / 'transcript_clean.md').exists():
        mind.clean_transcript = (conf_dir / 'transcript_clean.md').read_text()
    
    # Load speakers
    speakers_dir = conf_dir / 'speakers'
    if speakers_dir.exists():
        for speaker_dir in sorted(speakers_dir.iterdir()):
            if speaker_dir.is_dir():
                speaker = Speaker(name=speaker_dir.name.replace('-', ' ').title())
                
                if (speaker_dir / 'passages.json').exists():
                    passages_data = json.loads((speaker_dir / 'passages.json').read_text())
                    speaker.passages = [Passage(**p) for p in passages_data]
                
                if (speaker_dir / 'soul.md').exists():
                    # Parse soul back (simplified - just store raw)
                    speaker.soul = {'raw': (speaker_dir / 'soul.md').read_text()}
                
                mind.speakers.append(speaker)
    
    return mind


def list_minds() -> list:
    """List all stored conference minds."""
    minds_dir = get_minds_dir()
    results = []
    for conf_dir in sorted(minds_dir.iterdir()):
        if conf_dir.is_dir() and (conf_dir / 'meta.json').exists():
            meta = json.loads((conf_dir / 'meta.json').read_text())
            results.append(meta)
    return results


# ─── Main Pipeline ─────────────────────────────────────────────

def ingest(transcript: str, name: str = "", source_file: str = "") -> ConferenceMind:
    """Full ingest pipeline: detect format, clean, extract, analyze, save."""
    
    # Auto-name if not provided
    if not name:
        name = f"Conference {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Detect and clean
    fmt = detect_format(transcript)
    clean = clean_transcript(transcript, fmt)
    
    # Extract speakers
    speakers = extract_speakers(clean)
    
    # Generate soul and skills for each speaker
    for speaker in speakers:
        generate_soul(speaker)
        extract_skills(speaker)
    
    # Detect cross-speaker patterns
    themes = detect_themes(speakers)
    tensions = detect_tensions(speakers)
    
    # Build mind
    mind = ConferenceMind(
        name=name,
        created=datetime.now().isoformat(),
        source_file=source_file,
        speakers=speakers,
        themes=themes,
        tensions=tensions,
        raw_transcript=transcript,
        clean_transcript=clean,
    )
    
    # Save to disk
    save_mind(mind)
    
    return mind


def ask(question: str, conference_name: str, 
        speaker_name: str = None) -> str:
    """Ask a question of a conference mind."""
    mind = load_mind(conference_name)
    if not mind:
        return f"Conference '{conference_name}' not found. Use 'list' to see available minds."
    
    results = route_question(question, mind, speaker_name)
    return format_response(results, question)
