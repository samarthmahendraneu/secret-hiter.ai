import random
import string
from collections import defaultdict
from math import comb

# ===== Behavior Model Parameters =====

# --- President lying probabilities ---
P_F_PRES_LIES = 0.7   # Probability that a Fascist President lies about what they drew or passed
P_L_PRES_LIES = 0.0   # Probability that a Liberal President lies (almost never lies)

# --- Chancellor lying probabilities ---
P_F_CHAN_LIES = 0.6   # Probability that a Fascist Chancellor lies about what they received
P_L_CHAN_LIES = 0.0   # Probability that a Liberal Chancellor lies (assumed truthful)

# --- Policy enactment probabilities (how likely a Chancellor of a given role enacts a policy) ---
P_F_CHAN_ENACT_F = 0.7  # Probability that a Fascist Chancellor enacts a Fascist policy when possible
P_L_CHAN_ENACT_F = 0.3  # Probability that a Liberal Chancellor ends up enacting a Fascist policy (bad luck / forced)

P_F_CHAN_ENACT_L = 0.4  # Probability that a Fascist Chancellor enacts a Liberal policy (to maintain cover)
P_L_CHAN_ENACT_L = 0.7  # Probability that a Liberal Chancellor enacts a Liberal policy (normal liberal outcome)

# how strong social propagation should be
SOCIAL_INFLUENCE = 0.35  # tweak this


def deck_likelihood(draw_F, deck_F, deck_L):
    total_cards = deck_F + deck_L
    if total_cards < 3 or draw_F < 0 or draw_F > 3:
        return 1e-6
    return comb(deck_F, draw_F) * comb(deck_L, 3 - draw_F) / comb(total_cards, 3)


def likelihood_of_obs(obs, assignment, deck_F, deck_L, player_scores):
    pres_idx, chan_idx, pres_claim_draw, pres_claim_pass, chan_claim_got, enacted = obs
    pres_role = assignment[pres_idx]
    chan_role = assignment[chan_idx]

    draw_F = int(pres_claim_draw[0])
    pass_F_pres = int(pres_claim_pass[0])
    pass_F_chan = int(chan_claim_got[0])
    claim_mismatch = pass_F_pres != pass_F_chan

    # 1) how plausible the draw was
    deck_like = deck_likelihood(draw_F, deck_F, deck_L)

    # 2) lying likelihood
    if claim_mismatch:
        pres_lie_prob = P_F_PRES_LIES if pres_role == "F" else P_L_PRES_LIES
        chan_lie_prob = P_F_CHAN_LIES if chan_role == "F" else P_L_CHAN_LIES
        lie_like = 1 - (1 - pres_lie_prob) * (1 - chan_lie_prob)
    else:
        pres_lie_prob = P_F_PRES_LIES if pres_role == "F" else P_L_PRES_LIES
        chan_lie_prob = P_F_CHAN_LIES if chan_role == "F" else P_L_CHAN_LIES
        lie_like = (1 - pres_lie_prob) * (1 - chan_lie_prob)

    # 3) enactment likelihood
    if enacted.upper() == "F":
        enact_like = P_F_CHAN_ENACT_F if chan_role == "F" else P_L_CHAN_ENACT_F
    else:
        enact_like = P_F_CHAN_ENACT_L if chan_role == "F" else P_L_CHAN_ENACT_L

    # 4) reputation multiplier
    pres_score = 1 + player_scores[pres_idx]["sus"] * 0.5
    chan_score = 1 + player_scores[chan_idx]["sus"] * 0.5

    return deck_like * lie_like * enact_like * pres_score * chan_score


def resample_by_weights(particles, weights):
    total = sum(weights)
    if total == 0:
        return [random.choice(particles) for _ in range(len(particles))]
    probs = [w / total for w in weights]
    return random.choices(particles, weights=probs, k=len(particles))


def estimate_marginals(particles):
    n = len(particles[0])
    counts = [0.0] * n
    for a in particles:
        for i in range(n):
            if a[i] == "F":
                counts[i] += 1
    total = len(particles)
    return [c / total for c in counts]


def main():
    print("=== Secret Hitler Inference Assistant (Support-Aware) ===")
    n = int(input("Enter number of players (5–10): "))
    f = int(input("Enter number of fascists: "))
    players = [string.ascii_uppercase[i] for i in range(n)]
    print(f"Players: {', '.join(players)}")

    deck_F = int(input("Enter current number of Fascist cards in deck (default 11): ") or 11)
    deck_L = int(input("Enter current number of Liberal cards in deck (default 6): ") or 6)
    print(f"Initial deck: {deck_F}F / {deck_L}L")

    num_particles = 10000

    # initial particles
    particles = []
    for _ in range(num_particles):
        fascists = set(random.sample(range(n), f))
        particles.append(tuple("F" if i in fascists else "L" for i in range(n)))

    # suspicion tracker
    player_scores = defaultdict(lambda: {"sus": 0.0})

    # support graph: supporter -> {supported: count}
    support_graph = defaultdict(lambda: defaultdict(int))

    round_num = 1
    while True:
        print(f"\n--- Round {round_num} ---")
        print(f"Deck before round: {deck_F}F / {deck_L}L remaining.")
        pres = input(f"President? ({'/'.join(players)}): ").strip().upper()
        chan = input(f"Chancellor? ({'/'.join(players)}): ").strip().upper()
        if pres not in players or chan not in players:
            print("Invalid player name.")
            continue

        pres_draw = input("What did President SAY they drew? (e.g., 2F1L): ").strip().upper()
        pres_pass = input("What did President SAY they passed? (e.g., 1F1L): ").strip().upper()
        chan_got = input("What did Chancellor SAY they got? (e.g., 1F1L): ").strip().upper()
        enacted = input("What policy was ENACTED? (F/L): ").strip().upper()

        pres_idx = players.index(pres)
        chan_idx = players.index(chan)

        obs = (pres_idx, chan_idx, pres_draw, pres_pass, chan_got, enacted)

        # 1) weight update
        weights = [likelihood_of_obs(obs, a, deck_F, deck_L, player_scores) for a in particles]
        particles = resample_by_weights(particles, weights)
        marginals = estimate_marginals(particles)

        # 2) base suspicion update from round
        mismatch = int(pres_pass[0]) != int(chan_got[0])
        if mismatch:
            player_scores[pres_idx]["sus"] += 1.0
            player_scores[chan_idx]["sus"] += 1.0
        if enacted == "F":
            # chancellor involved in F tends to be a bit more sus
            player_scores[chan_idx]["sus"] += 0.5

        # 3) ask for social support info
        # format: "A:E,B:D" means "A supported E", "B supported D"
        sup_line = input(
            "Who supported whom in discussion? (format A:E,B:D) leave blank if none: "
        ).strip()
        if sup_line:
            pairs = [p.strip() for p in sup_line.split(",") if p.strip()]
            for pair in pairs:
                if ":" in pair:
                    src, dst = pair.split(":", 1)
                    src = src.strip().upper()
                    dst = dst.strip().upper()
                    if src in players and dst in players:
                        support_graph[src][dst] += 1

        # 4) propagate suspicion via support graph
        # if a suspicious player keeps defending someone, that someone becomes more suspicious
        for src in players:
            src_idx = players.index(src)
            src_sus = player_scores[src_idx]["sus"]
            if src_sus <= 0:
                continue
            for dst, count in support_graph[src].items():
                dst_idx = players.index(dst)
                # support weight: more repeats → stronger
                player_scores[dst_idx]["sus"] += SOCIAL_INFLUENCE * src_sus * (count / (round_num))

        # 5) print probs
        print("\nEstimated probability each player is a fascist:")
        for i, p in enumerate(marginals):
            print(f"  {players[i]}: {p * 100:.1f}%  (sus={player_scores[i]['sus']:.2f})")

        if enacted == "F":
            deck_F -= 1
        else:
            deck_L -= 1

            # reshuffle if deck too low
        if deck_F + deck_L < 3:
            print("Deck low → reshuffle to 11F + 6L")
            deck_F, deck_L = 11, 6

        print(f"Deck after round: {deck_F}F / {deck_L}L")

        cont = input("Continue? (y/n): ").strip().lower()
        if cont != "y":
            break
        round_num += 1


if __name__ == "__main__":
    main()
