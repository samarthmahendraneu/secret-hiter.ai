#!/usr/bin/env python3
"""
Secret Hitler - Complete Implementation
Supports 5-10 players with proper rule enforcement
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from openai import OpenAI

MOODEL = "gpt-5-mini"  # works well for conversational play
client = OpenAI(api_key=OPENAI_API_KEY)

# !/usr/bin/env python3
"""
Secret Hitler - Natural Discussion Edition
AI players speak organically throughout the game like real humans
"""

import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from openai import OpenAI
#
# # Initialize OpenAI client
# client = OpenAI()
# MODEL = "gpt-4o-mini"

# ================== GAME CONSTANTS ==================
BOARD_CONFIGS = {
    5: {
        "fascist_count": 1,
        "hitler_sees_fascists": False,
        "powers": {3: None, 4: "EXECUTION", 5: "EXECUTION"},
        "win_fascist": 6,
        "win_liberal": 5
    },
    6: {
        "fascist_count": 1,
        "hitler_sees_fascists": False,
        "powers": {3: None, 4: "EXECUTION", 5: "EXECUTION"},
        "win_fascist": 6,
        "win_liberal": 5
    },
    7: {
        "fascist_count": 2,
        "hitler_sees_fascists": False,
        "powers": {2: "INVESTIGATE_LOYALTY", 3: "SPECIAL_ELECTION", 4: "EXECUTION", 5: "EXECUTION"},
        "win_fascist": 6,
        "win_liberal": 5
    },
    8: {
        "fascist_count": 2,
        "hitler_sees_fascists": False,
        "powers": {2: "INVESTIGATE_LOYALTY", 3: "SPECIAL_ELECTION", 4: "EXECUTION", 5: "EXECUTION"},
        "win_fascist": 6,
        "win_liberal": 5
    },
    9: {
        "fascist_count": 3,
        "hitler_sees_fascists": False,
        "powers": {1: "INVESTIGATE_LOYALTY", 2: "INVESTIGATE_LOYALTY", 3: "SPECIAL_ELECTION", 4: "EXECUTION",
                   5: "EXECUTION"},
        "win_fascist": 6,
        "win_liberal": 5
    },
    10: {
        "fascist_count": 3,
        "hitler_sees_fascists": False,
        "powers": {1: "INVESTIGATE_LOYALTY", 2: "INVESTIGATE_LOYALTY", 3: "SPECIAL_ELECTION", 4: "EXECUTION",
                   5: "EXECUTION"},
        "win_fascist": 6,
        "win_liberal": 5
    }
}

VETO_THRESHOLD = 5


# ================== PERSONALITY SYSTEM ==================
class Personality:
    """Personality traits for AI players - no hardcoded dialogue"""

    PROFILES = [
        {"name": "Alex Chen", "occupation": "Data Scientist", "trait": "analytical"},
        {"name": "Sam Rodriguez", "occupation": "High School Teacher", "trait": "nurturing"},
        {"name": "Jordan Black", "occupation": "Startup Founder", "trait": "aggressive"},
        {"name": "Riley Thompson", "occupation": "Therapist", "trait": "perceptive"},
        {"name": "Morgan Kim", "occupation": "Lawyer", "trait": "argumentative"},
        {"name": "Casey Wright", "occupation": "Stand-up Comedian", "trait": "humorous"},
        {"name": "Drew Martinez", "occupation": "Professional Poker Player", "trait": "stoic"},
        {"name": "Avery Jones", "occupation": "Political Analyst", "trait": "strategic"},
        {"name": "Taylor Green", "occupation": "Theater Director", "trait": "dramatic"},
        {"name": "Jamie Park", "occupation": "Software Engineer", "trait": "logical"}
    ]


# ================== OUTPUT MODELS ==================
class AIDecision(BaseModel):
    action: str
    target: Optional[str] = None
    choice: Optional[str] = None
    text: Optional[str] = None
    discard_index: Optional[int] = None
    enact_index: Optional[int] = None
    veto: Optional[bool] = None


class AIComment(BaseModel):
    text: str = Field(..., description="Natural comment as if playing with friends")
    wants_to_speak: bool = Field(..., description="Whether the player wants to comment")
    emotional_state: Optional[str] = None


# ================== GAME MODELS ==================
@dataclass
class Player:
    name: str
    role: str  # "L", "F", or "H"
    personality: Dict
    memory: List[Tuple[str, int]] = field(default_factory=list)
    investigated_players: Dict[str, str] = field(default_factory=dict)
    suspicion_scores: Dict[str, float] = field(default_factory=dict)
    alive: bool = True
    term_limited: bool = False
    last_spoke: int = 0  # Track when they last spoke

    def remember(self, event: str, importance: int = 1):
        self.memory.append((event, importance))
        self.memory = sorted(self.memory, key=lambda x: -x[1])[:30]

    def update_suspicion(self, target: str, delta: float):
        if target not in self.suspicion_scores:
            self.suspicion_scores[target] = 5.0
        self.suspicion_scores[target] = max(0, min(10, self.suspicion_scores[target] + delta))

    def visible_teammates(self, all_players: Dict[str, 'Player'], player_count: int) -> List[str]:
        config = BOARD_CONFIGS[player_count]
        if self.role == "F":
            return [p.name for p in all_players.values()
                    if p.role in ("F", "H") and p.name != self.name]
        elif self.role == "H" and player_count >= 7:  # Hitler never sees fascists in official rules
            return []
        return []


@dataclass
class Table:
    players: Dict[str, Player]
    order: List[str]
    player_count: int
    config: Dict
    deck: List[str] = field(default_factory=list)
    discards: List[str] = field(default_factory=list)
    liberal_policies: int = 0
    fascist_policies: int = 0
    president_idx: int = 0
    special_election_next: Optional[str] = None
    last_government: Optional[Tuple[str, str]] = None
    failed_elections: int = 0
    round_num: int = 1
    governments_formed: List[Tuple[str, str]] = field(default_factory=list)
    policy_history: List[Dict] = field(default_factory=list)
    investigation_history: List[Tuple[str, str, str]] = field(default_factory=list)
    execution_history: List[str] = field(default_factory=list)
    chat_history: List[str] = field(default_factory=list)
    veto_enabled: bool = False
    interaction_count: int = 0  # Track total interactions for speaking frequency

    def __post_init__(self):
        self.deck = ["L"] * 6 + ["F"] * 11
        random.shuffle(self.deck)
        self.config = BOARD_CONFIGS[self.player_count]

    def check_veto_enabled(self):
        self.veto_enabled = self.fascist_policies >= VETO_THRESHOLD

    def draw(self, n: int) -> List[str]:
        if len(self.deck) < n:
            self.reshuffle()
        drawn = [self.deck.pop() for _ in range(n) if self.deck]
        return drawn

    def reshuffle(self):
        print(f"♻️ Reshuffling {len(self.discards)} cards...")
        self.deck.extend(self.discards)
        self.discards.clear()
        random.shuffle(self.deck)

    def can_be_chancellor(self, player_name: str, president_name: str) -> bool:
        player = self.players[player_name]
        if not player.alive or player_name == president_name:
            return False
        alive_count = sum(1 for p in self.players.values() if p.alive)
        if alive_count > 5 and self.last_government:
            if player_name in self.last_government:
                return False
        return True

    def update_term_limits(self):
        for p in self.players.values():
            p.term_limited = False
        alive_count = sum(1 for p in self.players.values() if p.alive)
        if alive_count > 5 and self.last_government:
            for name in self.last_government:
                if name in self.players:
                    self.players[name].term_limited = True

    def enact_policy(self, policy: str, president: str, chancellor: str):
        if policy == "L":
            self.liberal_policies += 1
            print(f"📘 LIBERAL policy enacted! ({self.liberal_policies}/5)")
        else:
            self.fascist_policies += 1
            print(f"📕 FASCIST policy enacted! ({self.fascist_policies}/6)")
            self.check_veto_enabled()

        self.policy_history.append({
            "round": self.round_num,
            "president": president,
            "chancellor": chancellor,
            "policy": policy
        })

    def check_win_conditions(self) -> Optional[str]:
        if self.liberal_policies >= self.config["win_liberal"]:
            return "LIBERAL_POLICY"
        if self.fascist_policies >= self.config["win_fascist"]:
            return "FASCIST_POLICY"
        if self.fascist_policies >= 3 and self.last_government:
            chancellor = self.last_government[1]
            if chancellor in self.players and self.players[chancellor].role == "H":
                return "HITLER_CHANCELLOR"
        for name in self.execution_history:
            if name in self.players and self.players[name].role == "H":
                return "HITLER_EXECUTED"
        return None

    def get_current_power(self) -> Optional[str]:
        return self.config.get("powers", {}).get(self.fascist_policies)

    def add_chat(self, speaker: str, message: str):
        entry = f"{speaker}: {message}"
        self.chat_history.append(entry)
        self.chat_history = self.chat_history[-100:]
        print(f"  {entry}")


# ================== NATURAL AI SYSTEM ==================

def get_ai_comment(player: Player, table: Table, context: str) -> Optional[str]:
    """Get natural AI commentary based on game situation"""

    # Build comprehensive context
    teammates = player.visible_teammates(table.players, table.player_count)
    hitler = next((p.name for p in table.players.values() if p.role == "H"), None) if player.role == "F" else None

    # Recent events context
    recent_chat = "\n".join(table.chat_history[-20:]) if table.chat_history else ""
    recent_policies = table.policy_history[-3:] if table.policy_history else []

    # Check if player should speak (based on personality and situation)
    rounds_since_spoke = table.interaction_count - player.last_spoke

    prompt = f"""You are {player.name}, a {player.personality['occupation']} playing Secret Hitler.
Your personality trait: {player.personality['trait']}
Your SECRET role: {'Liberal' if player.role == 'L' else 'Fascist' if player.role == 'F' else 'Hitler'}
{'Your fascist teammates: ' + ', '.join(teammates) if teammates else ''}
{'Hitler is: ' + hitler if hitler and player.role == 'F' else ''}

Current situation: {context}
Board state: L:{table.liberal_policies}/5 F:{table.fascist_policies}/6 Failed:{table.failed_elections}/3
You last spoke {rounds_since_spoke} interactions ago.

Recent conversation:
{recent_chat}

Decide if you want to comment on the current situation. If you do, speak naturally as if playing with friends.
Consider:
- Your role and goals
- Your personality trait
- What others have been saying
- Whether this is a good moment to influence the game
- Don't speak too often (you've spoken recently: {rounds_since_spoke < 3})

Respond as you would at a real game table. Be genuine, use natural language, show emotion when appropriate.
If you're lying or deflecting, do it naturally. Reference specific events or players when relevant."""

    try:
        response = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You're a human playing Secret Hitler with friends. Speak naturally."},
                {"role": "user", "content": prompt}
            ],
            response_format=AIComment
        )

        comment = response.choices[0].message.parsed

        if comment.wants_to_speak:
            player.last_spoke = table.interaction_count
            return comment.text
        return None

    except Exception as e:
        # Simple fallback
        if random.random() < 0.3:  # 30% chance to speak on error
            fallbacks = [
                "Hmm, interesting...",
                "I need to think about this.",
                "Not sure about that.",
                "Let's see how this plays out."
            ]
            return random.choice(fallbacks)
        return None


def ai_decide(player: Player, table: Table, action: str, context: str) -> AIDecision:
    """AI makes game decisions"""

    teammates = player.visible_teammates(table.players, table.player_count)
    hitler = next((p.name for p in table.players.values() if p.role == "H"), None) if player.role == "F" else None

    prompt = f"""You are {player.name} ({player.personality['occupation']}, {player.personality['trait']}).
SECRET ROLE: {'Liberal' if player.role == 'L' else 'Fascist' if player.role == 'F' else 'Hitler'}
{'Teammates: ' + ', '.join(teammates) if teammates else ''}
{'Hitler: ' + hitler if hitler and player.role == 'F' else ''}

Action needed: {action}
Context: {context}
Game state: L:{table.liberal_policies}/5 F:{table.fascist_policies}/6

Make the best strategic decision for your team. You may also make a brief comment if it helps your strategy."""

    try:
        response = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Make strategic game decisions based on your secret role."},
                {"role": "user", "content": prompt}
            ],
            response_format=AIDecision
        )
        return response.choices[0].message.parsed
    except Exception as e:
        # Return defaults
        return AIDecision(
            action=action,
            choice="Ja" if action == "vote" else None,
            text=None
        )


def open_discussion(table: Table, topic: str, min_speakers: int = 0, max_speakers: int = 4):
    """Allow natural discussion where any AI can speak"""

    print(f"\n💬 {topic}")
    print("-" * 40)

    table.interaction_count += 1
    alive_ai = [p for p in table.players.values() if p.alive and p.name != "YOU"]
    speakers_count = 0
    max_rounds = 3  # Allow up to 3 rounds of discussion

    for round_num in range(max_rounds):
        spoke_this_round = False

        # Shuffle order for natural flow
        random.shuffle(alive_ai)

        for player in alive_ai:
            # Check if this player wants to speak
            comment = get_ai_comment(player, table, topic)
            if comment:
                table.add_chat(player.name, comment)
                speakers_count += 1
                spoke_this_round = True

                # Small chance for immediate response from another player
                if random.random() < 0.3:
                    responders = [p for p in alive_ai if p != player]
                    if responders:
                        responder = random.choice(responders)
                        response = get_ai_comment(responder, table, f"Responding to {player.name}'s comment: {comment}")
                        if response:
                            time.sleep(0.5)  # Brief pause for realism
                            table.add_chat(responder.name, response)
                            speakers_count += 1

            if speakers_count >= max_speakers:
                break

        # If no one spoke this round or we've had enough, end discussion
        if not spoke_this_round or speakers_count >= max_speakers:
            break

        # Small pause between rounds
        if round_num < max_rounds - 1:
            time.sleep(0.3)

    # Always give human a chance to comment
    if table.players["YOU"].alive:
        human_comment = input("  You (press Enter to skip): ").strip()
        if human_comment:
            table.add_chat("YOU", human_comment)

            # AI might respond to human
            if random.random() < 0.5 and alive_ai:
                responder = random.choice(alive_ai)
                response = get_ai_comment(responder, table, f"Responding to human's comment: {human_comment}")
                if response:
                    time.sleep(0.5)
                    table.add_chat(responder.name, response)


# ================== GAME PHASES ==================

def nomination_phase(table: Table, president: Player) -> Optional[Player]:
    """Handle chancellor nomination with natural discussion"""

    eligible = [name for name, p in table.players.items()
                if table.can_be_chancellor(name, president.name)]

    if not eligible:
        return None

    print(f"\n{'=' * 60}")
    print(f"🎩 President {president.name} must nominate a Chancellor")
    print(f"Eligible: {', '.join(eligible)}")

    # Pre-nomination discussion
    open_discussion(table, f"{president.name} is considering chancellor options", max_speakers=2)

    if president.name == "YOU":
        while True:
            choice = input("\nNominate Chancellor: ").strip()
            if choice in eligible:
                break
            print(f"Invalid. Choose from: {', '.join(eligible)}")
    else:
        decision = ai_decide(president, table, "nominate", f"Choose from: {eligible}")
        choice = decision.target if decision.target in eligible else random.choice(eligible)

        # President might explain choice
        if decision.text:
            print(f"\n{president.name}: {decision.text}")
            table.add_chat(president.name, decision.text)

    chancellor = table.players[choice]
    print(f"\n➜ {president.name} nominates {chancellor.name} as Chancellor")

    # Immediate reactions to nomination
    open_discussion(table, f"Reaction to {chancellor.name}'s nomination", max_speakers=3)

    return chancellor


def voting_phase(table: Table, president: Player, chancellor: Player) -> bool:
    """Voting with natural pre-vote discussion"""

    print(f"\n{'=' * 60}")
    print(f"🗳️ VOTE on {president.name} (President) + {chancellor.name} (Chancellor)")


    # Collect votes
    print("\n[Voting]")
    votes = {}

    for p in table.players.values():
        if not p.alive:
            continue

        if p.name == "YOU":
            while True:
                vote = input(f"Your vote (ja/nein): ").strip().lower()
                if vote in ["ja", "nein", "j", "n"]:
                    votes[p.name] = vote.startswith("j")
                    break
        else:
            decision = ai_decide(p, table, "vote", f"Vote on {president.name} + {chancellor.name}")
            votes[p.name] = (decision.choice or "Ja").lower().startswith("j")
            p.remember(f"Voted {'Ja' if votes[p.name] else 'Nein'} for {president.name}+{chancellor.name}")

    # Show results
    print("\nResults:")
    for name, vote in votes.items():
        print(f"  {name}: {'Ja ✓' if vote else 'Nein ✗'}")

    ja_count = sum(votes.values())
    total = len(votes)
    passed = ja_count > total / 2

    print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}: {ja_count}/{total} Ja votes")

    if passed:
        table.failed_elections = 0
        table.last_government = (president.name, chancellor.name)
        table.governments_formed.append((president.name, chancellor.name))
        table.update_term_limits()
    else:
        table.failed_elections += 1

        # Post-vote reactions
        open_discussion(table, f"Reaction to failed vote", max_speakers=2)

        if table.failed_elections >= 3:
            print("\n⚠️ CHAOS! Three failed elections!")
            chaos_policy = table.draw(1)[0]
            table.enact_policy(chaos_policy, "CHAOS", "CHAOS")
            table.failed_elections = 0
            open_discussion(table, f"Chaos enacted {chaos_policy} policy!", max_speakers=3)

    return passed


def legislative_phase(table: Table, president: Player, chancellor: Player):
    """Policy enactment with natural discussion"""

    print(f"\n{'=' * 60}")
    print("📋 LEGISLATIVE SESSION")

    # Draw cards
    cards = table.draw(3)

    # President discards
    if president.name == "YOU":
        print(f"You drew: {cards}")
        while True:
            try:
                idx = int(input("Discard (0, 1, or 2): "))
                if 0 <= idx <= 2:
                    break
            except ValueError:
                pass
    else:
        decision = ai_decide(president, table, "discard", f"Drew {cards}, discard one")
        idx = decision.discard_index or random.randint(0, 2)

    discarded = cards.pop(idx)
    table.discards.append(discarded)

    print("President passes 2 cards to Chancellor...")

    # Chancellor enacts
    if table.veto_enabled:
        print("⚠️ Veto power ACTIVE")

    if chancellor.name == "YOU":
        print(f"You received: {cards}")

        if table.veto_enabled:
            if input("Propose veto? (y/n): ").strip().lower() == 'y':
                if president.name == "YOU":
                    veto_approved = input("Approve veto? (y/n): ").strip().lower() == 'y'
                else:
                    veto_decision = ai_decide(president, table, "veto", "Chancellor proposes veto")
                    veto_approved = veto_decision.veto or False

                if veto_approved:
                    print("✅ Veto approved!")
                    table.discards.extend(cards)
                    table.failed_elections += 1
                    return
                print("❌ Veto rejected")

        while True:
            try:
                idx = int(input("Enact (0 or 1): "))
                if 0 <= idx <= 1:
                    break
            except ValueError:
                pass
        enacted = cards[idx]
    else:
        decision = ai_decide(chancellor, table, "enact", f"Received {cards}")

        if table.veto_enabled and decision.veto:
            print(f"{chancellor.name} proposes VETO!")

            if president.name == "YOU":
                veto_approved = input("Approve veto? (y/n): ").strip().lower() == 'y'
            else:
                veto_decision = ai_decide(president, table, "veto_response", "Veto proposed")
                veto_approved = veto_decision.veto or False

            if veto_approved:
                print("✅ Veto approved!")
                table.discards.extend(cards)
                table.failed_elections += 1

                open_discussion(table, "Reaction to vetoed agenda", max_speakers=2)
                return
            print("❌ Veto rejected")

        idx = decision.enact_index or 0
        enacted = cards[idx if idx < len(cards) else 0]

    table.discards.append(cards[1 - idx if idx < len(cards) else 0])
    table.enact_policy(enacted, president.name, chancellor.name)

    # Policy discussion - claims and reactions
    print("\n[Policy Discussion]")

    # Natural claiming phase
    open_discussion(table,
                    f"{'Liberal' if enacted == 'L' else 'Fascist'} policy was enacted. {president.name} and {chancellor.name}, what happened?",
                    min_speakers=2, max_speakers=5)


def execute_power(table: Table, president: Player, power: str):
    """Execute presidential powers with discussion"""

    print(f"\n{'=' * 60}")
    print(f"⚡ PRESIDENTIAL POWER: {power}")

    alive_players = [p for p in table.players.values() if p.alive and p.name != president.name]

    if power == "INVESTIGATE_LOYALTY":
        # Pre-investigation discussion
        open_discussion(table, f"{president.name} must investigate someone. Who seems suspicious?", max_speakers=3)

        if president.name == "YOU":
            while True:
                target_name = input("Investigate: ").strip()
                if target_name in [p.name for p in alive_players]:
                    break
        else:
            decision = ai_decide(president, table, "investigate", "Choose target")
            target_name = decision.target or random.choice([p.name for p in alive_players])
            if decision.text:
                table.add_chat(president.name, decision.text)

        target = table.players[target_name]
        party = "Fascist" if target.role in ["F", "H"] else "Liberal"

        president.investigated_players[target_name] = party
        table.investigation_history.append((president.name, target_name, party))

        if president.name == "YOU":
            print(f"\n🔍 {target_name} is {party}")
        else:
            president.remember(f"Investigated {target_name}: {party}", importance=3)
            president.update_suspicion(target_name, 5 if party == "Fascist" else -3)

        # Post-investigation discussion
        open_discussion(table, f"{president.name} investigated {target_name}. What does this mean?", min_speakers=1,
                        max_speakers=4)

    elif power == "SPECIAL_ELECTION":
        open_discussion(table, f"{president.name} will choose the next President", max_speakers=2)

        if president.name == "YOU":
            while True:
                target_name = input("Choose next President: ").strip()
                if target_name in [p.name for p in alive_players]:
                    break
        else:
            decision = ai_decide(president, table, "special_election", "Choose next President")
            target_name = decision.target or random.choice([p.name for p in alive_players])
            if decision.text:
                table.add_chat(president.name, decision.text)

        table.special_election_next = target_name
        print(f"➜ {target_name} will be next President")

    elif power == "EXECUTION":
        # Critical discussion before execution
        open_discussion(table, f"{president.name} must execute someone. This is crucial!", min_speakers=2,
                        max_speakers=5)

        if president.name == "YOU":
            while True:
                target_name = input("Execute: ").strip()
                if target_name in [p.name for p in alive_players]:
                    break
        else:
            decision = ai_decide(president, table, "execute", "Choose who to execute")
            target_name = decision.target or random.choice([p.name for p in alive_players])
            if decision.text:
                table.add_chat(president.name, decision.text)

        target = table.players[target_name]
        target.alive = False
        table.execution_history.append(target_name)

        print(f"\n💀 {target_name} has been EXECUTED!")

        # Immediate reactions
        open_discussion(table, f"Reaction to {target_name}'s execution", min_speakers=1, max_speakers=3)

        if target.role == "H":
            return "HITLER_EXECUTED"

    return None


# ================== MAIN GAME ==================

def setup_game():
    """Initialize game"""
    print("=" * 60)
    print(" SECRET HITLER ")
    print("=" * 60)

    while True:
        try:
            total_players = int(input("Total players (5-10): "))
            if 5 <= total_players <= 10:
                break
        except ValueError:
            pass

    player_name = input("Your name: ").strip() or "Player"

    # Setup players
    personalities = random.sample(Personality.PROFILES, total_players - 1)
    config = BOARD_CONFIGS[total_players]
    fascist_count = config["fascist_count"]

    roles = ["H"] + ["F"] * fascist_count + ["L"] * (total_players - fascist_count - 1)
    random.shuffle(roles)

    players = {}

    # Human player
    players["YOU"] = Player(
        name="YOU",
        role=roles.pop(),
        personality={"name": player_name, "occupation": "Human Player", "trait": "adaptive"}
    )

    # AI players
    for personality in personalities:
        name = personality["name"].split()[0].upper()
        players[name] = Player(name=name, role=roles.pop(), personality=personality)

    # Setup table
    order = list(players.keys())
    random.shuffle(order)

    table = Table(players=players, order=order, player_count=total_players, config=config)

    # Initialize fascist knowledge
    for player in players.values():
        teammates = player.visible_teammates(players, total_players)
        if teammates:
            for teammate in teammates:
                player.remember(f"{teammate} is on my team", importance=5)

    return table


def reveal_roles(table: Table):
    """Show role to human player"""
    human = table.players["YOU"]

    print("\n" + "=" * 60)
    print("YOUR SECRET ROLE")
    print("=" * 60)

    if human.role == "L":
        print("🔵 You are a LIBERAL")
        print("Win: Enact 5 Liberal policies OR execute Hitler")
    elif human.role == "F":
        print("🔴 You are a FASCIST")
        print("Win: Enact 6 Fascist policies OR elect Hitler as Chancellor (after 3 Fascist)")
        teammates = human.visible_teammates(table.players, table.player_count)
        if teammates:
            print(f"Your team: {', '.join(teammates)}")
            hitler = next((p.name for p in table.players.values() if p.role == "H"), None)
            if hitler:
                print(f"Hitler is: {hitler} - Protect them!")
    else:
        print("💀 You are HITLER")
        print("Win: Get elected Chancellor after 3 Fascist policies")
        print("Act Liberal! The Fascists know who you are.")

    input("\nPress Enter to start...")
    print("\n" * 2)


def display_board(table: Table):
    """Show game state"""
    print("\n" + "=" * 60)
    print(f" ROUND {table.round_num} ")
    print("=" * 60)

    lib_track = "🔵" * table.liberal_policies + "⚪" * (5 - table.liberal_policies)
    fas_track = "🔴" * table.fascist_policies + "⚪" * (6 - table.fascist_policies)

    print(f"Liberal:  {lib_track} ({table.liberal_policies}/5)")
    print(f"Fascist:  {fas_track} ({table.fascist_policies}/6)")

    if table.veto_enabled:
        print("⚠️ VETO ACTIVE")

    print(f"Failed: {'🔸' * table.failed_elections}{'⚪' * (3 - table.failed_elections)}")
    print(f"Deck: {len(table.deck)} | Discard: {len(table.discards)}")

    print("\nPlayers:")
    for name in table.order:
        player = table.players[name]
        status = "💀" if not player.alive else "  "
        term = " [TERM]" if player.term_limited else ""
        print(f"{status} {name} ({player.personality['occupation']}){term}")


def run_game(table: Table):
    """Main game loop"""
    reveal_roles(table)

    # Opening discussion
    print("\n" + "=" * 60)
    print("The game begins! Let's see who we can trust...")
    open_discussion(table, "Opening thoughts", max_speakers=3)

    while True:
        display_board(table)

        # Determine president
        if table.special_election_next:
            president_name = table.special_election_next
            table.special_election_next = None
            print(f"\n[SPECIAL] {president_name} is President")
        else:
            while True:
                president_name = table.order[table.president_idx % len(table.order)]
                table.president_idx += 1
                if table.players[president_name].alive:
                    break

        president = table.players[president_name]

        # Nomination and voting
        chancellor = nomination_phase(table, president)
        if not chancellor:
            continue

        elected = voting_phase(table, president, chancellor)

        if elected:
            # Check Hitler win
            if table.fascist_policies >= 3 and chancellor.role == "H":
                win_condition = "HITLER_CHANCELLOR"
            else:
                legislative_phase(table, president, chancellor)
                win_condition = table.check_win_conditions()

                if not win_condition:
                    power = table.get_current_power()
                    if power:
                        result = execute_power(table, president, power)
                        if result:
                            win_condition = result
        else:
            win_condition = None

        if win_condition:
            display_endgame(table, win_condition)
            break

        table.round_num += 1
        input("\nPress Enter for next round...")


def display_endgame(table: Table, win_condition: str):
    """Show game results"""
    print("\n" + "=" * 60)
    print(" GAME OVER ")
    print("=" * 60)

    if win_condition == "LIBERAL_POLICY":
        print("🔵 LIBERALS WIN! - 5 Liberal policies")
    elif win_condition == "HITLER_EXECUTED":
        print("🔵 LIBERALS WIN! - Hitler executed")
    elif win_condition == "FASCIST_POLICY":
        print("🔴 FASCISTS WIN! - 6 Fascist policies")
    elif win_condition == "HITLER_CHANCELLOR":
        print("💀 FASCISTS WIN! - Hitler elected")

    print("\nROLES REVEALED:")
    for name in table.order:
        player = table.players[name]
        role_name = {"L": "Liberal", "F": "Fascist", "H": "HITLER"}[player.role]
        print(f"  {name}: {role_name}")


def main():
    """Entry point"""
    try:
        table = setup_game()
        run_game(table)

        if input("\nPlay again? (y/n): ").strip().lower() == 'y':
            main()
    except KeyboardInterrupt:
        print("\n\nGame ended.")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()