# obinexus-as2-splicing/src/constraints/aux_rule.py
from dataclasses import dataclass
from typing import Set, Tuple, Optional, Dict, List
import re

@dataclass
class AuxRule:
    """Auxiliary rule for constraint-based sequence manipulation"""
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

class AuxRuleEngine:
    """Engine for applying auxiliary rules to sequences"""
    
    def __init__(self):
        self.rules: List[AuxRule] = []
        self.prototype_map: Dict[str, Set[str]] = {}  # Maps prototypes to sequences
    
    def add_rule(self, rule: AuxRule) -> None:
        """Add a rule to the engine"""
        self.rules.append(rule)
        # Sort rules by priority (highest first)
        self.rules.sort(key=lambda x: x.priority, reverse=True)
    
    def register_prototype(self, name: str, sequences: Set[str]) -> None:
        """Register a prototype with associated sequences"""
        self.prototype_map[name] = sequences
    
    def match_sequence(self, sequence: str) -> List[AuxRule]:
        """Find all rules that match a sequence"""
        matched_rules = []
        
        for rule in self.rules:
            # Check pattern match
            if not rule.compiled_pattern.search(sequence):
                continue
                
            # Check prototype tags
            sequence_prototypes = self._get_sequence_prototypes(sequence)
            if not rule.proto_tags.issubset(sequence_prototypes):
                continue
                
            # Check bounds if specified
            if rule.bounds and not (rule.bounds[0] <= len(sequence) <= rule.bounds[1]):
                continue
                
            matched_rules.append(rule)
        
        return matched_rules
    
    def _get_sequence_prototypes(self, sequence: str) -> Set[str]:
        """Get all prototypes that include this sequence"""
        sequence_prototypes = set()
        
        for proto_name, proto_sequences in self.prototype_map.items():
            if sequence in proto_sequences:
                sequence_prototypes.add(proto_name)
        
        return sequence_prototypes
    
    def apply_rules(self, sequence: str) -> Tuple[str, float]:
        """
        Apply all matching rules to a sequence
        
        Returns:
            Tuple of (modified_sequence, total_penalty)
        """
        matched_rules = self.match_sequence(sequence)
        modified_sequence = sequence
        total_penalty = 0.0
        
        for rule in matched_rules:
            modified_sequence = self._apply_actions(modified_sequence, rule.actions)
            total_penalty += rule.penalty
        
        return modified_sequence, total_penalty
    
    def _apply_actions(self, sequence: str, actions: Set[str]) -> str:
        """Apply actions to a sequence"""
        result = sequence
        
        for action in actions:
            if action == "reverse":
                result = result[::-1]
            elif action == "complement":
                result = self._dna_complement(result)
            elif action.startswith("trim:"):
                # Extract trim length from action
                try:
                    length = int(action.split(":")[1])
                    result = result[:length]
                except (ValueError, IndexError):
                    pass
            elif action.startswith("insert:"):
                # Extract insertion from action
                try:
                    insertion = action.split(":")[1]
                    result = result + insertion
                except IndexError:
                    pass
        
        return result
    
    def _dna_complement(self, sequence: str) -> str:
        """Return the complement of a DNA sequence"""
        complement_map = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
        return ''.join(complement_map.get(base, 'N') for base in sequence)
