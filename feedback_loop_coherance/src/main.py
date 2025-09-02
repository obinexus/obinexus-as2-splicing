# src/main.py (updated implementation)
from dataclasses import dataclass
from typing import Set, Tuple, Optional, List, Dict, Any
from itertools import groupby
from hashlib import sha256
import json
import re

@dataclass
class AuxRule:
    pattern: str
    proto_tags: Set[str]
    actions: Set[str]
    priority: int
    penalty: float
    bounds: Optional[Tuple[int, int]]
    
    def __post_init__(self):
        """Validate and compile the pattern"""
        try:
            self.compiled_pattern = re.compile(self.pattern)
        except re.error as e:
            raise ValueError(f"Invalid pattern '{self.pattern}': {e}")

class MitochondrialFeedbackEngine:
    """Engine for mitochondrial feedback loop implementation"""
    
    def __init__(self, k: int = 4):
        self.k = k
        self.aux_table: List[AuxRule] = []
        self.prototype_map: Dict[str, Set[str]] = {}
        self.certificate_history: List[Dict] = []
    
    def add_rule(self, rule: AuxRule) -> None:
        """Add a rule to the auxiliary table"""
        self.aux_table.append(rule)
        self.aux_table.sort(key=lambda x: x.priority, reverse=True)
    
    def register_prototype(self, name: str, sequences: Set[str]) -> None:
        """Register a prototype with associated sequences"""
        self.prototype_map[name] = sequences
    
    def sequence_to_lattice(self, kmer: str) -> Tuple[float, float]:
        """Map k-mer to geometric coordinates in [-1, 1] space"""
        # Improved lattice mapping using hash distribution
        hash1 = int(sha256(kmer.encode()).hexdigest()[:8], 16) / 2**32
        hash2 = int(sha256(kmer[::-1].encode()).hexdigest()[:8], 16) / 2**32
        return (hash1 * 2 - 1, hash2 * 2 - 1)
    
    def compose_intervals(self, genome: str) -> List[Tuple[int, int]]:
        """Compose optimal intervals for cloning based on auxiliary rules"""
        annotations = []
        
        # Annotate each k-mer with matching rules
        for i in range(len(genome) - self.k + 1):
            kmer = genome[i:i+self.k]
            for rule in self.aux_table:
                if rule.compiled_pattern.search(kmer) and "exclude" not in rule.actions:
                    annotations.append((i, i+self.k, rule))
        
        # Group annotations by prototype tags
        candidate_regions = []
        annotations.sort(key=lambda x: x[0])  # Sort by start position
        
        for key, group in groupby(annotations, key=lambda x: x[2].proto_tags):
            group_list = list(group)
            start = group_list[0][0]
            end = group_list[-1][1]
            rule = group_list[0][2]
            candidate_regions.append((start, end, rule.priority, rule.penalty, rule.proto_tags))
        
        # Select optimal regions (non-overlapping, high priority, healthy)
        selected_regions = []
        candidate_regions.sort(key=lambda x: (x[0], x[2]))  # Sort by start then priority
        last_end = -1
        
        for start, end, priority, penalty, tags in candidate_regions:
            if start >= last_end and "healthy" in tags:
                selected_regions.append((start, end))
                last_end = end
        
        return selected_regions
    
    def score_clone(self, genome: str, clone_regions: List[Tuple[int, int]]) -> Dict[str, Any]:
        """Score a clone and generate certificate"""
        # Calculate phi sets
        phi_original = set()
        for rule in self.aux_table:
            if rule.compiled_pattern.search(genome):
                phi_original.update(rule.proto_tags)
        
        phi_clone = set()
        for rule in self.aux_table:
            for start, end in clone_regions:
                region_seq = genome[start:end]
                if rule.compiled_pattern.search(region_seq):
                    phi_clone.update(rule.proto_tags)
        
        # Calculate scores
        union_size = len(phi_original | phi_clone)
        jaccard = len(phi_original & phi_clone) / union_size if union_size > 0 else 1.0
        
        # Calculate penalties only for distinct rules in clone
        rules_in_clone = set()
        for start, end in clone_regions:
            region_seq = genome[start:end]
            for rule in self.aux_table:
                if rule.compiled_pattern.search(region_seq):
                    rules_in_clone.add(rule)
        
        total_penalty = sum(rule.penalty for rule in rules_in_clone)
        
        # Health score (percentage of healthy regions)
        healthy_regions = sum(1 for start, end in clone_regions 
                            if any("healthy" in rule.proto_tags 
                                for rule in self.aux_table 
                                if rule.compiled_pattern.search(genome[start:end])))
        health_score = healthy_regions / len(clone_regions) if clone_regions else 0
        
        # Final score with weighted components
        score = (0.6 * jaccard + 0.35 * health_score - 
                0.03 * total_penalty + 0.02 * len(clone_regions))
        
        # Generate recommendations
        recommendations = []
        error_detected = False
        
        # Check for errors in original but not in clone
        for rule in self.aux_table:
            if "error" in rule.proto_tags and rule.compiled_pattern.search(genome):
                in_clone = any(rule.compiled_pattern.search(genome[start:end]) 
                            for start, end in clone_regions)
                if not in_clone:
                    error_detected = True
                    recommendations.append({
                        "increase_penalty": [{"rule": rule.pattern, "delta": 2.0}]
                    })
                    recommendations.append({
                        "deprioritize": [{"rule": rule.pattern, "new_priority": rule.priority + 1}]
                    })
        
        # Create certificate
        certificate = {
            "aux_table_hash": sha256(str(self.aux_table).encode()).hexdigest(),
            "k": self.k,
            "selected_regions": clone_regions,
            "scores": [score],
            "cost": total_penalty,
            "phi_original": list(phi_original),
            "phi_clone": list(phi_clone),
            "health_score": health_score,
            "recommendations": recommendations,
            "timestamp": "2025-09-03T00:13:00"  # Would use datetime.now().isoformat() in production
        }
        
        # Save certificates
        self._save_certificate(certificate)
        self.certificate_history.append(certificate)
        
        return {
            "score": score,
            "certificate": certificate,
            "error_detected": error_detected
        }
    
    def _save_certificate(self, certificate: Dict[str, Any]) -> None:
        """Save certificate in both CAV and JSON formats"""
        # Save as .cav
        with open("clonecertificate.cav", "w") as f:
            f.write("# OBINexus Directed Evolution Certificate\n")
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
        
        # Save as .json
        with open("clonecertificate.json", "w") as f:
            json.dump(certificate, f, indent=2)
    
    def update_aux_table(self, certificate: Dict[str, Any]) -> None:
        """Update auxiliary table based on certificate recommendations"""
        for rec in certificate["recommendations"]:
            if "increase_penalty" in rec:
                for update in rec["increase_penalty"]:
                    for rule in self.aux_table:
                        if rule.pattern == update["rule"]:
                            rule.penalty += update["delta"]
                            print(f"Updated penalty for {rule.pattern} to {rule.penalty}")
            
            if "deprioritize" in rec:
                for update in rec["deprioritize"]:
                    for rule in self.aux_table:
                        if rule.pattern == update["rule"]:
                            rule.priority = update["new_priority"]
                            print(f"Updated priority for {rule.pattern} to {rule.priority}")
        
        # Re-sort table by priority
        self.aux_table.sort(key=lambda x: x.priority, reverse=True)
    
    def generate_mitochondrial_feedback(self, genome: str) -> Dict[str, Any]:
        """Complete mitochondrial feedback loop"""
        # Step 1: Compose intervals
        regions = self.compose_intervals(genome)
        
        # Step 2: Score clone
        result = self.score_clone(genome, regions)
        
        # Step 3: Apply feedback if errors detected
        if result["error_detected"]:
            print("Errors detected, updating auxiliary table...")
            self.update_aux_table(result["certificate"])
        
        return result

def main():
    # Initialize mitochondrial feedback engine
    engine = MitochondrialFeedbackEngine(k=4)
    
    # Define auxiliary table (from §4)
    aux_rules = [
        AuxRule("ATCG", {"short_hair", "healthy", "mammal_safe"}, {"splice", "validate"}, 1, 0.5, (-1, 1)),
        AuxRule("CGTA", {"long_hair", "healthy", "mammal_safe"}, {"splice", "check_drift"}, 2, 1.0, (-0.5, 0.5)),
        AuxRule("GCTA", {"long_hair", "risky"}, {"exclude", "log_error"}, 3, 2.0, None),
        AuxRule("TTTT", {"lesion", "error"}, {"exclude", "flag_mito"}, 4, 5.0, None),
    ]
    
    for rule in aux_rules:
        engine.add_rule(rule)
    
    # Test genome with error pattern
    genome = "ATCGCGTATTTTATCG"  # Includes TTTT to trigger feedback
    
    # Run complete mitochondrial feedback loop
    result = engine.generate_mitochondrial_feedback(genome)
    
    # Print results
    print(f"Selected regions: {result['certificate']['selected_regions']}")
    print(f"Score: {result['score']}")
    print(f"Certificate saved to clonecertificate.cav and clonecertificate.json")
    
    # Display certificate summary
    print("\nCertificate Summary:")
    print(f"Original properties: {result['certificate']['phi_original']}")
    print(f"Clone properties: {result['certificate']['phi_clone']}")
    print(f"Health score: {result['certificate']['health_score']}")
    print(f"Cost: {result['certificate']['cost']}")
    print(f"Recommendations: {result['certificate']['recommendations']}")

if __name__ == "__main__":
    main()
