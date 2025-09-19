import requests

# -----------------------------
# Constant Values
# -----------------------------

NEW_GAME_URL = "https://berghain.challenges.listenlabs.ai/new-game"
BASE_URL = "https://berghain.challenges.listenlabs.ai/decide-and-next"

PLAYER_ID = ""
SCENARIO = 2
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
    # Focus traits (ignore well_connected)
    focus_traits = ["techno_lover", "creative", "berlin_local"]

    progress = {}
    for t in focus_traits:
        if constraints[t] > 0:
            progress[t] = counts[t] / constraints[t]
        else:
            progress[t] = 0.0

    lowest = min(progress, key=progress.get)
    highest = max(progress, key=progress.get)

    full_traits = sum(1 for t in constraints if counts[t] >= constraints[t])
    if full_traits >= len(constraints) - 1:
        return True

    if attrs.get("well_connected", False) and not any(attrs.get(t, False) for t in focus_traits):
        return False
    
    if attrs.get("well_connected", False):
        other_focus = [t for t in focus_traits if attrs.get(t, False)]
        if len(other_focus) == 1 and not attrs.get("creative", False):
            return False
    
    for t in focus_traits + ["well_connected"]:
        if constraints[t] > 0:
            if counts[t] / constraints[t] >= 0.85:
                # If this person only contributes to the nearly-full trait
                if attrs.get(t, False) and not any(attrs.get(o, False) for o in constraints if o != t):
                    return False
    
    # Case 1: If person has the lowest-progress trait → accept
    if attrs.get(lowest, False):
        return True

    return False

    # Case 2: If person has only the highest-progress trait → reject
    # if attrs.get(highest, False) and not any(attrs.get(t, False) for t in focus_traits if t != highest):
    #     return False

    # # Case 3: Otherwise → accept if they have any focus trait
    # return any(attrs.get(t, False) for t in focus_traits)

# -----------------------------
# Main Loop
# -----------------------------
def main():
    
    game_info = start_game()
    game_id = game_info["gameId"]
    constraints = {c["attribute"]: c["minCount"] for c in game_info["constraints"]}
    rejected_traits = {t: 0 for t in constraints if t != "well_connected"}


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

        if not will_accept:
            for a in rejected_traits:
                if attrs.get(a, False):
                    rejected_traits[a] += 1


        if venue_count % 50 == 0:
            print(f"Venue {venue_count}/{MAX_VENUE} | Counts: {counts} | Rejected Traits: {rejected_traits}")

main()
