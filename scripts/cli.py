#!/usr/bin/env python3
"""
conference-minds CLI

Usage:
    conference-minds ingest [--name NAME] [--file PATH]
    conference-minds ask QUESTION [--conference NAME] [--speaker NAME]
    conference-minds speakers [--conference NAME] [--detail]
    conference-minds themes [--conference NAME]
    conference-minds tensions [--conference NAME]
    conference-minds list
    conference-minds export [--conference NAME] [--output PATH]
    conference-minds delete NAME
"""

import sys
import argparse
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core import ingest, ask, list_minds, load_mind, get_minds_dir, slugify


def cmd_ingest(args):
    """Ingest a transcript from file or stdin."""
    if args.file:
        transcript = Path(args.file).read_text()
        source = args.file
    else:
        print("Paste transcript below (Ctrl+D or Ctrl+Z when done):")
        transcript = sys.stdin.read()
        source = "stdin"
    
    if not transcript.strip():
        print("Error: Empty transcript")
        sys.exit(1)
    
    name = args.name or ""
    mind = ingest(transcript, name=name, source_file=source)
    
    print(f"\n✓ Ingested: {mind.name}")
    print(f"  Speakers: {len(mind.speakers)}")
    for s in mind.speakers:
        skills_str = ', '.join(sk['domain'] for sk in s.skills[:3]) if s.skills else 'analyzing...'
        print(f"    - {s.name}: {len(s.passages)} passages | {skills_str}")
    print(f"  Themes: {len(mind.themes)}")
    print(f"  Tensions: {len(mind.tensions)}")
    print(f"  Saved to: ~/.conference-minds/conferences/{slugify(mind.name)}/")


def cmd_ask(args):
    """Ask a question of a conference mind."""
    # If no conference specified, use most recent
    if not args.conference:
        minds = list_minds()
        if not minds:
            print("No conferences ingested yet. Use 'conference-minds ingest' first.")
            sys.exit(1)
        args.conference = minds[-1]['name']
    
    response = ask(args.question, args.conference, args.speaker)
    print(response)


def cmd_speakers(args):
    """List speakers in a conference mind."""
    if not args.conference:
        minds = list_minds()
        if not minds:
            print("No conferences ingested yet.")
            sys.exit(1)
        args.conference = minds[-1]['name']
    
    mind = load_mind(args.conference)
    if not mind:
        print(f"Conference '{args.conference}' not found.")
        sys.exit(1)
    
    print(f"\nSpeakers in: {mind.name}\n")
    for s in mind.speakers:
        print(f"  {s.name}")
        if args.detail:
            print(f"    Passages: {len(s.passages)}")
            if s.soul and 'voice' in s.soul:
                voice = s.soul['voice']
                print(f"    Voice: {voice.get('sentence_structure', 'unknown')}, {voice.get('vocabulary_register', 'unknown')}")
            if s.skills:
                for sk in s.skills[:5]:
                    print(f"    Skill: {sk['domain']} ({sk['strength']})")
            print()


def cmd_themes(args):
    """Show conference themes."""
    if not args.conference:
        minds = list_minds()
        if not minds:
            print("No conferences ingested yet.")
            sys.exit(1)
        args.conference = minds[-1]['name']
    
    mind = load_mind(args.conference)
    if not mind:
        print(f"Conference '{args.conference}' not found.")
        sys.exit(1)
    
    print(f"\nThemes in: {mind.name}\n")
    for t in mind.themes[:15]:
        bar = '█' * min(t['frequency'], 30)
        print(f"  {t['theme']:20s} {bar} ({t['frequency']})")


def cmd_tensions(args):
    """Show detected tensions."""
    if not args.conference:
        minds = list_minds()
        if not minds:
            print("No conferences ingested yet.")
            sys.exit(1)
        args.conference = minds[-1]['name']
    
    mind = load_mind(args.conference)
    if not mind:
        print(f"Conference '{args.conference}' not found.")
        sys.exit(1)
    
    print(f"\nTensions in: {mind.name}\n")
    if not mind.tensions:
        print("  No strong tensions detected.")
    for t in mind.tensions:
        print(f"  {' vs '.join(t['speakers'])}")
        print(f"    {t['note']}")
        print()


def cmd_list(args):
    """List all ingested conferences."""
    minds = list_minds()
    if not minds:
        print("No conferences ingested yet. Use 'conference-minds ingest' first.")
        return
    
    print(f"\nStored conference minds:\n")
    for m in minds:
        print(f"  {m['name']}")
        print(f"    Speakers: {m.get('speaker_count', '?')} | Created: {m.get('created', 'unknown')[:10]}")
        print()


def cmd_export(args):
    """Export a conference mind's files."""
    if not args.conference:
        minds = list_minds()
        if not minds:
            print("No conferences ingested yet.")
            sys.exit(1)
        args.conference = minds[-1]['name']
    
    slug = slugify(args.conference)
    source = get_minds_dir() / slug
    
    if not source.exists():
        print(f"Conference '{args.conference}' not found.")
        sys.exit(1)
    
    output = Path(args.output) if args.output else Path.cwd() / f"{slug}-export"
    
    import shutil
    shutil.copytree(source, output, dirs_exist_ok=True)
    print(f"Exported to: {output}")


def cmd_delete(args):
    """Delete a conference mind."""
    slug = slugify(args.name)
    conf_dir = get_minds_dir() / slug
    
    if not conf_dir.exists():
        print(f"Conference '{args.name}' not found.")
        sys.exit(1)
    
    import shutil
    shutil.rmtree(conf_dir)
    print(f"Deleted: {args.name}")


def main():
    parser = argparse.ArgumentParser(
        prog='conference-minds',
        description='Transform conference transcripts into conversational speaker-agents'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # ingest
    p_ingest = subparsers.add_parser('ingest', help='Ingest a transcript')
    p_ingest.add_argument('--name', '-n', help='Conference name')
    p_ingest.add_argument('--file', '-f', help='Path to transcript file')
    
    # ask
    p_ask = subparsers.add_parser('ask', help='Ask a question')
    p_ask.add_argument('question', help='Question to ask')
    p_ask.add_argument('--conference', '-c', help='Conference name')
    p_ask.add_argument('--speaker', '-s', help='Target specific speaker')
    
    # speakers
    p_speakers = subparsers.add_parser('speakers', help='List speakers')
    p_speakers.add_argument('--conference', '-c', help='Conference name')
    p_speakers.add_argument('--detail', '-d', action='store_true', help='Show detail')
    
    # themes
    p_themes = subparsers.add_parser('themes', help='Show themes')
    p_themes.add_argument('--conference', '-c', help='Conference name')
    
    # tensions
    p_tensions = subparsers.add_parser('tensions', help='Show tensions')
    p_tensions.add_argument('--conference', '-c', help='Conference name')
    
    # list
    subparsers.add_parser('list', help='List all conferences')
    
    # export
    p_export = subparsers.add_parser('export', help='Export conference files')
    p_export.add_argument('--conference', '-c', help='Conference name')
    p_export.add_argument('--output', '-o', help='Output path')
    
    # delete
    p_delete = subparsers.add_parser('delete', help='Delete a conference')
    p_delete.add_argument('name', help='Conference name to delete')
    
    args = parser.parse_args()
    
    commands = {
        'ingest': cmd_ingest,
        'ask': cmd_ask,
        'speakers': cmd_speakers,
        'themes': cmd_themes,
        'tensions': cmd_tensions,
        'list': cmd_list,
        'export': cmd_export,
        'delete': cmd_delete,
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
