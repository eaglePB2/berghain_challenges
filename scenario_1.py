import requests

# -----------------------------
# Constant Values
# -----------------------------

NEW_GAME_URL = "https://berghain.challenges.listenlabs.ai/new-game"
BASE_URL = "https://berghain.challenges.listenlabs.ai/decide-and-next"

PLAYER_ID = ""
SCENARIO = 1
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
def rule_auto_accept(counts, constraints, attrs, threshold):
    """If quotas are already satisfied, accept everyone."""
    if counts["young"] >= constraints["young"] * threshold and counts["well_dressed"] >= constraints["well_dressed"] * threshold:
        return True
    return None

def rule_balance(counts, constraints, attrs, threshold):
    """
    Balance between young and well_dressed:
      - Reject if neither
      - Accept both
      - If only one, prefer the one lagging behind
    """
    is_young = attrs.get("young", False)
    is_well_dressed = attrs.get("well_dressed", False)

    if not (is_young or is_well_dressed):
        return False
    if is_young and is_well_dressed:
        return True

    young_progress = counts["young"] / constraints["young"] if constraints["young"] > 0 else 1
    well_progress = counts["well_dressed"] / constraints["well_dressed"] if constraints["well_dressed"] > 0 else 1

    if is_young and young_progress > well_progress:
        return False
    if is_well_dressed and well_progress > young_progress:
        return False

    # If progress equal, default accept whichever tag present
    return True

# -----------------------------
# Decision Engine
# -----------------------------
def decide(counts, constraints, attrs, threshold):
    """Run rules in order until one makes a decision."""
    for rule in (rule_auto_accept, rule_balance):
        result = rule(counts, constraints, attrs, threshold)
        if result is not None:
            return result
    return False  # default reject

# -----------------------------
# Main Loop
# -----------------------------
def main():

    # threshold = int(input("Enter threshold percentage (e.g., 80 for 80%): ")) / 100.0
    threshold = 0.87

    # start new game and extract constraints
    game_info = start_game()
    game_id = game_info["gameId"]
    constraints = {c["attribute"]: c["minCount"] for c in game_info["constraints"]}

    print(f"Started game {game_id}")
    print("Constraints:", constraints)

    # state
    person_index = 0
    accept = False
    counts = {"young": 0, "well_dressed": 0}
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

        will_accept = decide(counts, constraints, attrs, threshold)

        if will_accept:
            venue_count += 1
            for a in counts.keys():
                if attrs.get(a, False):
                    counts[a] += 1

        accept = will_accept

        if venue_count % 50 == 0:
            print(f"Venue {venue_count}/{MAX_VENUE} | Counts: {counts}")

main()