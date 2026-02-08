#!/usr/bin/env python3
"""Quick test of conference-minds core pipeline."""

import sys
sys.path.insert(0, '.')
from src.core import ingest, ask, list_minds

# Sample transcript (abbreviated Peter Steinberger YC interview style)
SAMPLE = """
Raphael Schaad: So Peter, tell us about how OpenClaw started. What was the original insight?

Peter Steinberger: It started in November in my kitchen. I wanted to check if my computer had finished a task. That's it. I'd been coding something, one of maybe 40 projects on my GitHub, and I just wanted to know: is it done yet? So I built this thin layer between WhatsApp and Claude Code. One hour prototype. Slow, but it worked.

Raphael Schaad: And that prototype became OpenClaw?

Peter Steinberger: Not immediately. The real moment was Marrakesh. I was there for a birthday party, internet was terrible, but WhatsApp works everywhere because it just moves text. So I started using the prototype for everyday things. Translate this menu. What does this sign say. Then I sent a voice message and something amazing happened. The agent figured out on its own how to handle it. Used ffmpeg to convert the audio, found an OpenAI API key in my environment, sent it for transcription via curl. Nine seconds. Nobody programmed any of those steps.

Raphael Schaad: That's the moment you realized this was bigger than a personal tool?

Peter Steinberger: Exactly. The coding models had become so good at creative problem-solving that the boundary between a software feature and an improvised solution just dissolved. That's when I knew 80 percent of apps would become unnecessary. Think about a fitness tracker. If the agent knows your habits, knows you're at a burger joint, it can infer the meal, log it, adjust your gym session. No app needed.

Raphael Schaad: What about MCP? Everyone in the community uses it, but OpenClaw doesn't.

Peter Steinberger: We got 160,000 stars with zero native MCP support. I built a skill that converts MCPs into CLIs through MakePorter. The reasoning is simple. MCP servers require restarts when configurations change. CLIs don't. MCP was designed for bots. CLIs were designed for humans. And it turns out agents are excellent at Unix. Build for humans first, and capable agents adapt.

Raphael Schaad: How do you think about the future? One big AI model doing everything, or something else?

Peter Steinberger: Not one god-AI. A constellation. Think about what one human can do alone. Not build an iPhone. Not reach orbit. We specialize, and through specialization within social structures, we accomplish the extraordinary. Same with agents. A private-life agent, a work agent, maybe a relationship agent. Bot-to-bot negotiation where possible. Bot-to-human delegation where necessary. And memory lives as markdown files on the user's machine. Not in corporate silos.
"""

print("=" * 60)
print("CONFERENCE-MINDS TEST")
print("=" * 60)

# Test ingest
print("\n1. Ingesting sample transcript...")
mind = ingest(SAMPLE, name="YC Interview Test: Peter Steinberger")

print(f"   Conference: {mind.name}")
print(f"   Speakers: {len(mind.speakers)}")
for s in mind.speakers:
    print(f"     - {s.name}: {len(s.passages)} passages")
    if s.soul and 'voice' in s.soul:
        print(f"       Voice: {s.soul['voice']}")
    if s.skills:
        print(f"       Skills: {[sk['domain'] for sk in s.skills]}")

print(f"   Themes: {[t['theme'] for t in mind.themes[:5]]}")
print(f"   Tensions: {len(mind.tensions)}")

# Test ask
print("\n2. Testing questions...")

q1 = "Why doesn't OpenClaw use MCP?"
print(f"\n   Q: {q1}")
print(f"   A: {ask(q1, 'YC Interview Test: Peter Steinberger')}")

q2 = "What happened in Marrakesh?"
print(f"\n   Q: {q2}")
print(f"   A: {ask(q2, 'YC Interview Test: Peter Steinberger')}")

q3 = "What's the vision for multiple agents?"
print(f"\n   Q: {q3}")
print(f"   A: {ask(q3, 'YC Interview Test: Peter Steinberger')}")

# Test list
print("\n3. Listing stored minds...")
for m in list_minds():
    print(f"   - {m['name']} ({m.get('speaker_count', '?')} speakers)")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
