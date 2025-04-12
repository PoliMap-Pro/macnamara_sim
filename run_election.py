from votekit.ballot import Ballot
from votekit.pref_profile import PreferenceProfile
from votekit.elections import IRV
import votekit.utils
import math

def generate_ballots(primary_party, primary_pct, total_votes, pref_flows, candidates):
    """Generates ballots for a given primary party based on preference flows."""
    ballots = []
    primary_votes = total_votes * primary_pct / 100.0
    accumulated_weight = 0

    # Define rankings based on primary party and flows
    # OTH is always ranked last by ALP, LIB, GRN voters
    if primary_party == "ALP":
        # ALP -> GRN -> LIB -> OTH
        weight1 = primary_votes * pref_flows["ALP_to_GRN"] / 100.0
        ranking1 = [{"ALP"}, {"GRN"}, {"LIB"}, {"OTH"}]
        ballots.append(Ballot(ranking=ranking1, weight=weight1))
        accumulated_weight += weight1
        # ALP -> LIB -> GRN -> OTH
        weight2 = primary_votes * (100 - pref_flows["ALP_to_GRN"]) / 100.0
        ranking2 = [{"ALP"}, {"LIB"}, {"GRN"}, {"OTH"}]
        ballots.append(Ballot(ranking=ranking2, weight=weight2))
        accumulated_weight += weight2

    elif primary_party == "LIB":
        # LIB -> GRN -> ALP -> OTH
        weight1 = primary_votes * pref_flows["LIB_to_GRN"] / 100.0
        ranking1 = [{"LIB"}, {"GRN"}, {"ALP"}, {"OTH"}]
        ballots.append(Ballot(ranking=ranking1, weight=weight1))
        accumulated_weight += weight1
        # LIB -> ALP -> GRN -> OTH
        weight2 = primary_votes * (100 - pref_flows["LIB_to_GRN"]) / 100.0
        ranking2 = [{"LIB"}, {"ALP"}, {"GRN"}, {"OTH"}]
        ballots.append(Ballot(ranking=ranking2, weight=weight2))
        accumulated_weight += weight2

    elif primary_party == "GRN":
        # GRN -> ALP -> LIB -> OTH
        weight1 = primary_votes * pref_flows["GRN_to_ALP"] / 100.0
        ranking1 = [{"GRN"}, {"ALP"}, {"LIB"}, {"OTH"}]
        ballots.append(Ballot(ranking=ranking1, weight=weight1))
        accumulated_weight += weight1
        # GRN -> LIB -> ALP -> OTH
        weight2 = primary_votes * (100 - pref_flows["GRN_to_ALP"]) / 100.0
        ranking2 = [{"GRN"}, {"LIB"}, {"ALP"}, {"OTH"}]
        ballots.append(Ballot(ranking=ranking2, weight=weight2))
        accumulated_weight += weight2

    elif primary_party == "OTH":
        # Use the exact OTH preference flows provided
        oth_to_grn_pct = pref_flows["OTH_to_GRN"]
        oth_to_alp_pct = pref_flows["OTH_to_ALP"]
        oth_to_lib_pct = pref_flows["OTH_to_LIB"]
        
        # Validate that preferences sum to approximately 100%
        pref_sum = oth_to_grn_pct + oth_to_alp_pct + oth_to_lib_pct
        if not (99.0 <= pref_sum <= 101.0):
            print(f"Warning: OTH preferences sum to {pref_sum}%, not 100%. Normalizing.")
            # Normalize to ensure they sum to 100%
            factor = 100.0 / pref_sum
            oth_to_grn_pct *= factor
            oth_to_alp_pct *= factor
            oth_to_lib_pct *= factor

        # Determine 3rd/4th preferences based on 2nd preference flow
        # OTH -> GRN -> (GRN flow) -> (GRN flow)
        grn_pref_order = [{"GRN"}, {"ALP"}, {"LIB"}] if pref_flows["GRN_to_ALP"] >= 50 else [{"GRN"}, {"LIB"}, {"ALP"}]
        ranking1 = [{"OTH"}] + grn_pref_order
        weight1 = primary_votes * oth_to_grn_pct / 100.0
        ballots.append(Ballot(ranking=ranking1, weight=weight1))
        accumulated_weight += weight1

        # OTH -> ALP -> (ALP flow) -> (ALP flow)
        alp_pref_order = [{"ALP"}, {"GRN"}, {"LIB"}] if pref_flows["ALP_to_GRN"] >= 50 else [{"ALP"}, {"LIB"}, {"GRN"}]
        ranking2 = [{"OTH"}] + alp_pref_order
        weight2 = primary_votes * oth_to_alp_pct / 100.0
        ballots.append(Ballot(ranking=ranking2, weight=weight2))
        accumulated_weight += weight2

        # OTH -> LIB -> (LIB flow) -> (LIB flow)
        lib_pref_order = [{"LIB"}, {"GRN"}, {"ALP"}] if pref_flows["LIB_to_GRN"] >= 50 else [{"LIB"}, {"ALP"}, {"GRN"}]
        ranking3 = [{"OTH"}] + lib_pref_order
        weight3 = primary_votes * oth_to_lib_pct / 100.0
        ballots.append(Ballot(ranking=ranking3, weight=weight3))
        accumulated_weight += weight3

    # Adjust weights to integers and ensure total matches primary_votes
    int_weights = [math.floor(b.weight) for b in ballots]
    remainder = int(round(primary_votes)) - sum(int_weights)

    # Distribute remainder (usually 0 or 1, sometimes more with floats)
    # Prioritize ballots with larger fractional parts for fairness
    frac_weights = sorted([(b.weight - math.floor(b.weight), i) for i, b in enumerate(ballots)], reverse=True)
    for i in range(remainder):
        idx_to_increment = frac_weights[i % len(frac_weights)][1]
        int_weights[idx_to_increment] += 1

    final_ballots = []
    for i, b in enumerate(ballots):
        if int_weights[i] > 0:
            # Ensure ranking covers all candidates if not already
            current_ranking_flat = {c for rank_set in b.ranking for c in rank_set}
            missing_candidates = [c for c in candidates if c not in current_ranking_flat]
            final_ranking = b.ranking + tuple([{c} for c in missing_candidates]) # Add missing ones at the end
            final_ballots.append(Ballot(ranking=final_ranking, weight=int_weights[i]))

    return final_ballots


def run_election(alp_primary, lib_primary, grn_primary, pref_flows):
    """
    Simulates a 4-candidate (ALP, LIB, GRN, OTH) preferential election using IRV.

    Args:
        alp_primary (float): ALP primary vote percentage.
        lib_primary (float): LIB primary vote percentage.
        grn_primary (float): GRN primary vote percentage.
        pref_flows (dict): Dictionary of preference flow percentages, e.g.,
                           {"ALP_to_GRN": 70, "LIB_to_GRN": 15,
                            "GRN_to_ALP": 80, "OTH_to_GRN": 30}
                           Assumes complementary flows (e.g., ALP_to_LIB = 100 - ALP_to_GRN).
                           Assumes OTH remainder splits equally to ALP/LIB for 2nd pref.
                           Subsequent OTH preferences follow the 2nd pref party's flow.

    Returns:
        dict: Dictionary with the final two candidates and their percentages
              after the full IRV count. Returns None if input is invalid.
    """
    oth_primary = 100.0 - alp_primary - lib_primary - grn_primary
    if not (-0.01 < oth_primary < 100.01): # Allow for small float inaccuracies
         print(f"Error: Total primary votes ({alp_primary+lib_primary+grn_primary:.2f}) invalid.")
         return None

    primaries = {
        "ALP": alp_primary,
        "LIB": lib_primary,
        "GRN": grn_primary,
        "OTH": max(0, oth_primary), # Ensure non-negative
    }
    # Filter out candidates with zero primary votes initially
    candidates = [c for c, p in primaries.items() if p > 0]
    if len(candidates) < 2:
        print("Error: Need at least two candidates with non-zero votes.")
        return None

    total_votes = 100000  # Simulate with 100k votes for precision

    all_ballots = []
    calculated_total_weight = 0
    for party, primary_pct in primaries.items():
        if primary_pct > 0:
            party_ballots = generate_ballots(party, primary_pct, total_votes, pref_flows, candidates)
            all_ballots.extend(party_ballots)
            calculated_total_weight += sum(b.weight for b in party_ballots)

    # Final weight check and adjustment
    if calculated_total_weight != total_votes:
        print(f"Warning: Total ballot weight ({calculated_total_weight}) doesn't match target ({total_votes}). Adjusting.")
        diff = total_votes - calculated_total_weight
        if all_ballots:
            # Add difference to the first ballot for simplicity
            first_ballot = all_ballots[0]
            new_weight = first_ballot.weight + diff
            if new_weight > 0:
                 all_ballots[0] = Ballot(ranking=first_ballot.ranking, weight=new_weight)
                 print(f"Adjusted first ballot weight to {new_weight}.")
            else:
                 print(f"Warning: Cannot adjust weight, results may be slightly off. Diff: {diff}")
        else:
             print("Warning: No ballots generated, cannot adjust weight.")


    if not all_ballots:
        print("Error: No ballots were generated.")
        return None

    try:
        profile = PreferenceProfile(ballots=all_ballots, candidates=candidates)

        # Run the full IRV election
        # Use 'random' tiebreaking for simplicity, could be configured
        election = IRV(profile=profile)
        
        # The IRV object itself contains the election results
        # Identify the final round and the candidates remaining
        final_round_num = election.length - 1 # Last round index
        final_round_profile = election.get_profile(final_round_num)

        # Get scores in the final round (should be only two candidates left)
        final_scores = votekit.utils.first_place_votes(final_round_profile)

        # Verify exactly two candidates remain
        if len(final_scores) != 2:
             print(f"Warning: Expected 2 candidates in final round, found {len(final_scores)}.")
             print("Final round scores:", final_scores)
             # Fallback: find the top two from the last round with votes
             sorted_scores = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)
             if len(sorted_scores) >= 2:
                 final_two_scores = dict(sorted_scores[:2])
                 print("Using top two candidates:", final_two_scores)
                 final_scores = final_two_scores
             else:
                 print("Error: Could not determine final two candidates.")
                 return None # Or return the raw final_scores

        total_final_votes = sum(final_scores.values())

        if total_final_votes == 0:
            print("Warning: Zero total votes in the final round calculation.")
            # Return 0% for the candidates identified, if any
            return {cand: 0.0 for cand in final_scores}

        # Calculate percentages for the final two
        final_percentages = {
            cand: 100.0 * float(votes) / total_final_votes
            for cand, votes in final_scores.items()
        }
        return final_percentages

    except Exception as e:
        print(f"Error during IRV election or result processing: {e}")
        import traceback
        traceback.print_exc()
        return None


# Example Usage (can be removed or commented out)
if __name__ == "__main__":
    # Scenario 1: Standard ALP vs LIB TPP expected
    print("--- Scenario 1: ALP vs LIB ---")
    alp_primary_1 = 35.0
    lib_primary_1 = 40.0
    grn_primary_1 = 15.0
    pref_flows_1 = {
        "ALP_to_GRN": 75.0, "LIB_to_GRN": 20.0, "GRN_to_ALP": 85.0,
        "OTH_to_GRN": 40.0, "OTH_to_ALP": 30.0, "OTH_to_LIB": 30.0
    }
    result_1 = run_election(alp_primary_1, lib_primary_1, grn_primary_1, pref_flows_1)
    if result_1:
        print("\n--- Final Two Candidates ---")
        for cand, perc in result_1.items():
            print(f"{cand}: {perc:.2f}%")

    # Scenario 2: High Green vote, potentially GRN vs ALP/LIB TPP
    print("\n--- Scenario 2: High Green ---")
    alp_primary_2 = 25.0
    lib_primary_2 = 30.0
    grn_primary_2 = 35.0 # Higher Green vote
    pref_flows_2 = { # Same flows for consistency
        "ALP_to_GRN": 75.0, "LIB_to_GRN": 20.0, "GRN_to_ALP": 85.0,
        "OTH_to_GRN": 40.0, "OTH_to_ALP": 30.0, "OTH_to_LIB": 30.0
    }
    
    # Scenario 4: MacNamara with default app.py values
    print("\n--- Scenario 4: MacNamara Default Values ---")
    alp_primary_4 = 31.8
    lib_primary_4 = 29.0
    grn_primary_4 = 29.7
    # oth_primary = 9.5 (calculated)
    pref_flows_4 = {
        "ALP_to_GRN": 83.0, "LIB_to_GRN": 29.0, "GRN_to_ALP": 88.0,
        "OTH_to_GRN": 33.0, "OTH_to_ALP": 18.0, "OTH_to_LIB": 49.0
    }
    result_4 = run_election(alp_primary_4, lib_primary_4, grn_primary_4, pref_flows_4)
    if result_4:
        print("\n--- Final Two Candidates ---")
        for cand, perc in result_4.items():
            print(f"{cand}: {perc:.2f}%")
    result_2 = run_election(alp_primary_2, lib_primary_2, grn_primary_2, pref_flows_2)
    if result_2:
        print("\n--- Final Two Candidates ---")
        for cand, perc in result_2.items():
            print(f"{cand}: {perc:.2f}%")

    # Scenario 3: Close 3-way, OTH preferences might decide final two
    print("\n--- Scenario 3: Close 3-Way ---")
    alp_primary_3 = 31.0
    lib_primary_3 = 32.0
    grn_primary_3 = 28.0 # Close race
    pref_flows_3 = { # Different flows to test sensitivity
        "ALP_to_GRN": 60.0, "LIB_to_GRN": 30.0, "GRN_to_ALP": 70.0,
        "OTH_to_GRN": 60.0, "OTH_to_ALP": 20.0, "OTH_to_LIB": 20.0 # Stronger OTH->GRN
    }
    result_3 = run_election(alp_primary_3, lib_primary_3, grn_primary_3, pref_flows_3)
    if result_3:
        print("\n--- Final Two Candidates ---")
        for cand, perc in result_3.items():
            print(f"{cand}: {perc:.2f}%")