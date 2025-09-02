# obinexus-as2-splicing/src/constraints/constraint_solver.py
from typing import List, Tuple, Set
from .aux_rule import AuxRule, AuxRuleEngine

class ConstraintSolver:
    """Solver for geometric constraint satisfaction"""
    
    def __init__(self):
        self.rule_engine = AuxRuleEngine()
        self.aux_space_rules: List[AuxRule] = []
    
    def add_constraint_rule(self, rule: AuxRule) -> None:
        """Add a constraint rule to the solver"""
        self.aux_space_rules.append(rule)
        self.rule_engine.add_rule(rule)
    
    def solve_constraints(self, sequences: List[str]) -> List[Tuple[str, float]]:
        """
        Apply constraint rules to a list of sequences
        
        Returns:
            List of tuples (modified_sequence, penalty)
        """
        results = []
        
        for seq in sequences:
            modified_seq, penalty = self.rule_engine.apply_rules(seq)
            results.append((modified_seq, penalty))
        
        return results
    
    def find_optimal_solution(self, sequences: List[str]) -> str:
        """
        Find the sequence with the lowest penalty after applying constraints
        """
        solutions = self.solve_constraints(sequences)
        
        if not solutions:
            return ""
        
        # Find solution with minimum penalty
        best_solution = min(solutions, key=lambda x: x[1])
        return best_solution[0]
