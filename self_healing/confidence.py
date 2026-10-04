"""Confidence Engine for calculating match probability across API and Database fields."""
import re
import difflib
from typing import Any, Dict, List, Optional, Tuple, Type

# Common domain abbreviations and synonyms
SYNONYMS = {
    "cust": "customer",
    "prod": "product",
    "cat": "category",
    "ord": "order",
    "pay": "payment",
    "qty": "quantity",
    "amt": "amount",
    "num": "number",
    "desc": "description",
    "img": "image",
    "usr": "user",
    "name": "username",
}

class ConfidenceEngine:
    """Calculates weighted confidence scores for potential healing candidates."""

    @staticmethod
    def normalize_token(name: str) -> str:
        """
        Normalizes snake_case, camelCase, PascalCase, and kebab-case into a lowercase token string.
        Examples:
            'userName' -> 'user_name'
            'customerId' -> 'customer_id'
            'customer-name' -> 'customer_name'
        """
        if not name:
            return ""
        # Insert underscore between lower-to-upper transition
        s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
        # Replace hyphens and whitespace with underscores
        s2 = re.sub(r'[-\s]+', '_', s1)
        # Convert to lowercase
        return s2.lower().strip('_')

    @classmethod
    def expand_abbreviations(cls, token: str) -> str:
        """Replaces common abbreviations with full forms for semantic matching."""
        parts = token.split('_')
        expanded = [SYNONYMS.get(p, p) for p in parts]
        return '_'.join(expanded)

    @classmethod
    def calculate_name_similarity(cls, expected: str, candidate: str) -> float:
        """
        Calculates lexical and structural similarity between two identifiers (0.0 - 1.0).
        """
        if expected == candidate:
            return 1.0

        exp_norm = cls.normalize_token(expected)
        cand_norm = cls.normalize_token(candidate)

        # Exact match after case/format normalization (e.g. 'userName' vs 'user_name' or 'username')
        if exp_norm == cand_norm:
            return 0.98

        # Stripped match (e.g. 'username' vs 'user_name')
        if exp_norm.replace('_', '') == cand_norm.replace('_', ''):
            return 0.95

        # Synonym expanded match (e.g. 'cust_id' vs 'customer_id')
        exp_expanded = cls.expand_abbreviations(exp_norm)
        cand_expanded = cls.expand_abbreviations(cand_norm)
        if exp_expanded == cand_expanded:
            return 0.94

        # Disallow conflicting semantic entities (e.g. 'customer_id' vs 'product_id')
        exp_parts = set(exp_norm.split('_'))
        cand_parts = set(cand_norm.split('_'))
        conflicting_roots = {"customer", "product", "order", "payment", "category", "cart", "user"}
        exp_roots = exp_parts.intersection(conflicting_roots)
        cand_roots = cand_parts.intersection(conflicting_roots)
        if exp_roots and cand_roots and exp_roots != cand_roots:
            # Different primary entity root! Heavily penalize
            return 0.10

        # Prefix / Suffix match (e.g. 'userId' / 'user_id' vs 'id', 'cust_email' vs 'email', 'order_id' vs 'id')
        if exp_norm.endswith('_' + cand_norm) or cand_norm.endswith('_' + exp_norm):
            return 0.92
        if exp_expanded.endswith('_' + cand_expanded) or cand_expanded.endswith('_' + exp_expanded):
            return 0.92
        if exp_norm.startswith(cand_norm + '_') or cand_norm.startswith(exp_norm + '_'):
            return 0.90

        # Levenshtein / SequenceMatcher similarity on normalized and expanded forms
        base_ratio = difflib.SequenceMatcher(None, exp_norm, cand_norm).ratio()
        expanded_ratio = difflib.SequenceMatcher(None, exp_expanded, cand_expanded).ratio()
        max_ratio = max(base_ratio, expanded_ratio)

        return round(max_ratio, 4)

    @staticmethod
    def calculate_type_compatibility(expected_val: Any, candidate_val: Any) -> float:
        """
        Validates data type compatibility between expected and candidate values.
        Incompatible types receive very low confidence (e.g. integer -> string = 0.1).
        """
        if expected_val is None or candidate_val is None:
            return 0.50  # Neutral if either value is None

        type_exp = type(expected_val)
        type_cand = type(candidate_val)

        # Identical Python types
        if type_exp == type_cand:
            return 1.0

        # Numeric compatibility (int <-> float, Decimal)
        if issubclass(type_exp, (int, float)) and issubclass(type_cand, (int, float)):
            # bool is a subclass of int in Python, treat bool specially
            if type_exp is bool or type_cand is bool:
                return 0.85 if (type_exp is bool and type_cand in (int, bool)) else 0.40
            return 0.90

        # String representation of numeric vs actual numeric
        if (isinstance(expected_val, str) and isinstance(candidate_val, (int, float))) or \
           (isinstance(candidate_val, str) and isinstance(expected_val, (int, float))):
            return 0.20  # Significant type divergence

        # Incompatible collections or types
        return 0.10

    @classmethod
    def calculate_confidence(
        cls,
        expected: str,
        candidate: str,
        expected_val: Any = None,
        candidate_val: Any = None,
        context_score: float = 0.5,
        has_history: bool = False
    ) -> float:
        """
        Computes composite confidence score:
            - Name similarity: 55%
            - Type compatibility: 30% (if values supplied)
            - Structural/context compatibility: 15%
            - History bonus: +0.08
        """
        name_score = cls.calculate_name_similarity(expected, candidate)

        # If name similarity is already conflicting or very low, fail early
        if name_score < 0.30:
            return round(name_score, 4)

        has_values = expected_val is not None and candidate_val is not None
        if has_values:
            type_score = cls.calculate_type_compatibility(expected_val, candidate_val)
            composite = (name_score * 0.55) + (type_score * 0.30) + (context_score * 0.15)
        else:
            # When evaluating schema or column without runtime values
            composite = (name_score * 0.75) + (context_score * 0.25)

        if has_history:
            composite = min(1.0, composite + 0.08)

        return round(composite, 4)
