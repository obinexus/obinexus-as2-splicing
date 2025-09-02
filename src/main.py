# src/main.py
from dataclasses import dataclass
from typing import Set, Tuple, Optional, List
from itertools import groupby
from hashlib import sha256
import json

@dataclass
class AuxRule:
    pattern: str
    proto_tags: Set[str]
    actions: Set[str]
    priority: int
    penalty: float
    bounds: Optional[Tuple[int, int]]

def sequence_to_lattice(kmer: str) -> Tuple[float, float]:
    # Placeholder: Map k-mer to [-1, 1]
    return (hash(kmer) % 2 - 1, hash(kmer[::-1]) % 2 - 1)

def compose_intervals(genome: str, aux_table: List[AuxRule], k: int = 4) -> List[Tuple[int, int]]:
    annotations = []
    for i in range(len(genome) - k + 1):
        kmer = genome[i:i+k]
        for rule in aux_table:
            if kmer == rule.pattern and "exclude" not in rule.actions:
                annotations.append((i, i+k, rule))

    candidate_regions = []
    for _, group in groupby(sorted(annotations, key=lambda x: x[0]), key=lambda x: x[2].proto_tags):
        group = list(group)
        start, end = group[0][0], group[-1][1]
        rule = group[0][2]
        candidate_regions.append((start, end, rule.priority, rule.penalty, rule.proto_tags))

    selected_regions = []
    candidate_regions.sort(key=lambda x: (x[0], x[2]))
    last_end = -1
    for start, end, priority, penalty, tags in candidate_regions:
        if start >= last_end and "healthy" in tags:
            selected_regions.append((start, end))
            last_end = end

    return selected_regions

def score_clone(genome: str, clone_regions: List[Tuple[int, int]], aux_table: List[AuxRule], k: int) -> dict:
    phi_original = set().union(*(rule.proto_tags for rule in aux_table if rule.pattern in genome))
    phi_clone = set().union(*(rule.proto_tags for rule in aux_table if any(rule.pattern in genome[s:e] for s, e in clone_regions)))
    jaccard = len(phi_original & phi_clone) / len(phi_original | phi_clone) if phi_original | phi_clone else 1.0
    total_penalty = sum(rule.penalty for rule in aux_table if any(rule.pattern in genome[s:e] for s, e in clone_regions))
    health_score = sum(1 for s, e in clone_regions if any("healthy" in rule.proto_tags for rule in aux_table if rule.pattern in genome[s:e])) / len(clone_regions) if clone_regions else 0
    score = 0.6 * jaccard + 0.35 * health_score - 0.03 * total_penalty + 0.02 * len(clone_regions)
    
    recommendations = []
    error_detected = False
    for s, e in clone_regions:
        for rule in aux_table:
            if rule.pattern in genome[s:e] and "error" in rule.proto_tags:
                error_detected = True
                recommendations.append({"increase_penalty": [{"rule": rule.pattern, "delta": 2.0}]})
                recommendations.append({"deprioritize": [{"rule": rule.pattern, "new_priority": rule.priority + 1}]})

    certificate = {
        "aux_table_hash": sha256(str(aux_table).encode()).hexdigest(),
        "k": k,
        "selected_regions": clone_regions,
        "scores": [score],
        "cost": total_penalty,
        "phi_original": list(phi_original),
        "phi_clone": list(phi_clone),
        "health_score": health_score,
        "recommendations": recommendations,
        "timestamp": "2025-09-03T00:13:00"
    }
    
    # Save certificate as .cav
    with open("src/clonecertificate.cav", "w") as f:
        f.write(f"# OBINexus Directed Evolution Certificate\n")
        f.write(f"AUX_TABLE_HASH: {certificate['aux_table_hash']}\n")
        f.write(f"K: {certificate['k']}\n")
        f.write(f"SELECTED_REGIONS: {certificate['selected_regions']}\n")
        f.write(f"SCORES: {certificate['scores']}\n")
        f.write(f"COST: {certificate['cost']}\n")
        f.write(f"PHI_ORIGINAL: {certificate['phi_original']}\n")
        f.write(f"PHI_CLONE: {certificate['phi_clone']}\n")
        f.write(f"HEALTH_SCORE: {certificate['health_score']}\n")
        f.write(f"RECOMMENDATIONS: {certificate['recommendations']}\n")
        f.write(f"TIMESTAMP: {certificate['timestamp']}\n")
    
    # Also save as .json for compatibility
    with open("src/clonecertificate.json", "w") as f:
        json.dump(certificate, f, indent=2)
    
    return {"score": score, "certificate": certificate, "error_detected": error_detected}

def update_aux_table(aux_table: List[AuxRule], certificate: dict) -> List[AuxRule]:
    updated_table = aux_table.copy()
    for rec in certificate["recommendations"]:
        if "increase_penalty" in rec:
            for update in rec["increase_penalty"]:
                for rule in updated_table:
                    if rule.pattern == update["rule"]:
                        rule.penalty += update["delta"]
                        print(f"Updated penalty for {rule.pattern} to {rule.penalty}")
        if "deprioritize" in rec:
            for update in rec["deprioritize"]:
                for rule in updated_table:
                    if rule.pattern == update["rule"]:
                        rule.priority = update["new_priority"]
                        print(f"Updated priority for {rule.pattern} to {rule.priority}")
    return updated_table

def main():
    # Define auxiliary table (from §4)
    aux_table = [
        AuxRule("ATCG", {"short_hair", "healthy", "mammal_safe"}, {"splice", "validate"}, 1, 0.5, (-1, 1)),
        AuxRule("CGTA", {"long_hair", "healthy", "mammal_safe"}, {"splice", "check_drift"}, 2, 1.0, (-0.5, 0.5)),
        AuxRule("GCTA", {"long_hair", "risky"}, {"exclude", "log_error"}, 3, 2.0, None),
        AuxRule("TTTT", {"lesion", "error"}, {"exclude", "flag_mito"}, 4, 5.0, None),
    ]
    
    # Test genome with error pattern
    genome = "ATCGCGTATTTTATCG"  # Includes TTTT to trigger feedback
    k = 4
    
    # Compose intervals and score clone
    regions = compose_intervals(genome, aux_table, k)
    result = score_clone(genome, regions, aux_table, k)
    
    # Apply feedback loop
    if result["error_detected"]:
        print("Errors detected, updating auxiliary table...")
        aux_table = update_aux_table(aux_table, result["certificate"])
    
    # Print results
    print(f"Selected regions: {regions}")
    print(f"Score: {result['score']}")
    print(f"Certificate saved to src/clonecertificate.cav and src/clonecertificate.json")

if __name__ == "__main__":
    main()
