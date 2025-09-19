import requests

# -----------------------------
# Constant Values
# -----------------------------

NEW_GAME_URL = "https://berghain.challenges.listenlabs.ai/new-game"
BASE_URL = "https://berghain.challenges.listenlabs.ai/decide-and-next"

PLAYER_ID = ""
SCENARIO = 3
MAX_VENUE = 1000

# -----------------------------
# API Helpers
# -----------------------------

def start_game():
    params = {
        "scenario": SCENARIO,
        "playerId": PLAYER_ID
    }
    r = requests.get(NEW_GAME_URL, params=params)
    r.raise_for_status()
    return r.json()

def decide_person(game_id, person_index, accept):
    params = {
        "gameId": game_id,
        "personIndex": person_index,
        "accept": str(accept).lower()
    }
    r = requests.get(BASE_URL, params=params)
    r.raise_for_status()
    return r.json()

# -----------------------------
# Strategy Rules
# -----------------------------

def choose_by_ratio(counts, constraints, attrs):

    focus_traits = ["international", "german_speaker", "queer_friendly", "vinyl_collector"]

    # Compute progress ratio
    progress = {
        t: counts[t] / constraints[t] if constraints[t] > 0 else 0.0
        for t in focus_traits
    }

    lowest = min(progress, key=progress.get)

    # If everyone is full except maybe one → accept blindly
    full_traits = sum(1 for t in constraints if counts[t] >= constraints[t])
    if full_traits >= len(constraints) - 1:
        return True

    # Reject if person has no attributes at all
    if not any(attrs.values()):
        return False
    
    if sum(1 for t in focus_traits if attrs.get(t, False)) == 1:
        return False
    
    for t in focus_traits:
        if constraints[t] > 0:
            if counts[t] / constraints[t] >= 0.95:
                # If this person only contributes to the nearly-full trait
                if attrs.get(t, False) and not any(attrs.get(o, False) for o in constraints if o != t):
                    return False

    # Prioritize lowest-progress trait
    if attrs.get(lowest, False):
        return True

    # Otherwise: accept if they help any focus trait
    return False


# -----------------------------
# Main Loop
# -----------------------------
def main():
    game_info = start_game()
    game_id = game_info["gameId"]
    constraints = {c["attribute"]: c["minCount"] for c in game_info["constraints"]}

    print(f"Started game {game_id}")
    print("Constraints:", constraints)

    person_index = 0
    accept = False
    counts = {attr: 0 for attr in constraints.keys()}
    venue_count = 0

    while True:
        data = decide_person(game_id, person_index, accept)
        if data["status"] != "running":
            print("Game finished")
            print("Final counts:", counts, "Venue:", venue_count)
            break

        next_person = data["nextPerson"]
        person_index = next_person["personIndex"]
        attrs = next_person["attributes"]

        will_accept = choose_by_ratio(counts, constraints, attrs)

        if will_accept:
            venue_count += 1
            for a in constraints:
                if attrs.get(a, False):
                    counts[a] += 1

        accept = will_accept

        if venue_count % 50 == 0:
            print(f"Venue {venue_count}/{MAX_VENUE} | Counts: {counts}")

main()
