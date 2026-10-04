"""API Self-Healing Engine: Handles response field renames, JSONPath changes, schema drift, and endpoint versioning."""
import os
import inspect
from typing import Any, Dict, List, Optional, Tuple, Union

from self_healing.config import SelfHealingConfig
from self_healing.confidence import ConfidenceEngine
from self_healing.history import HealingHistory
from self_healing.reporter import HealingReporter
from utils.logger import logger


def get_current_test_name() -> str:
    """Introspects call stack to determine the active test function name."""
    for frame in inspect.stack():
        func_name = frame.function
        if func_name != "get_current_test_name" and func_name.startswith("test_"):
            return func_name
    return "API_Test"


class SelfHealingDict(dict):
    """
    Intelligent Dictionary proxy for API JSON responses.
    Transparently behaves like a standard dict, but upon encountering a missing key,
    activates the confidence engine to evaluate candidate fields for legitimate structural changes.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None, parent_path: str = "$"):
        super().__init__()
        self._parent_path = parent_path
        if data:
            for k, v in data.items():
                self[k] = self._wrap_value(v, f"{parent_path}.{k}")

    def _wrap_value(self, val: Any, current_path: str) -> Any:
        if isinstance(val, dict) and not isinstance(val, SelfHealingDict):
            return SelfHealingDict(val, current_path)
        elif isinstance(val, list):
            return [self._wrap_value(item, f"{current_path}[{idx}]") for idx, item in enumerate(val)]
        return val

    def __getitem__(self, key: Any) -> Any:
        # Standard fast path: key exists
        if key in self:
            return super().__getitem__(key)

        # If self-healing is disabled, preserve native KeyError
        if not SelfHealingConfig.is_api_enabled():
            raise KeyError(key)

        test_name = get_current_test_name()
        expected_key = str(key)
        history = HealingHistory.get_instance()
        reporter = HealingReporter.get_instance()

        # Step 1: Check historical validated mapping
        known = history.get_known_mapping("API", expected_key)
        if known and known.get("healed") in self:
            candidate_key = known["healed"]
            confidence = known.get("confidence", 0.95)
            val = super().__getitem__(candidate_key)
            reporter.log_api_healing(
                test_name=test_name,
                expected=expected_key,
                candidate=candidate_key,
                value_type=type(val).__name__,
                confidence=confidence,
                status="HEALED",
                reason="Restored from previously validated healing history",
                context={"path": f"{self._parent_path}.{candidate_key}", "historical": True}
            )
            history.record_success("API", expected_key, candidate_key, confidence, test_name)
            return val

        # Step 2: Analyze candidates in the current dictionary
        candidates = list(self.keys())
        if not candidates:
            reporter.log_api_healing(
                test_name=test_name,
                expected=expected_key,
                candidate="None",
                value_type="None",
                confidence=0.0,
                status="REJECTED",
                reason="Response object contains no candidate keys"
            )
            raise KeyError(key)

        best_candidate: Optional[str] = None
        best_confidence: float = 0.0

        for cand in candidates:
            cand_val = super().__getitem__(cand)
            score = ConfidenceEngine.calculate_confidence(
                expected=expected_key,
                candidate=str(cand),
                expected_val=None,
                candidate_val=cand_val,
                context_score=0.7
            )
            if score > best_confidence:
                best_confidence = score
                best_candidate = cand

        threshold = SelfHealingConfig.get_confidence_threshold()

        # Step 3: Healing validation gate
        if best_candidate and best_confidence >= threshold:
            val = super().__getitem__(best_candidate)
            reporter.log_api_healing(
                test_name=test_name,
                expected=expected_key,
                candidate=best_candidate,
                value_type=type(val).__name__,
                confidence=best_confidence,
                status="HEALED",
                reason=f"Candidate passed confidence threshold ({best_confidence:.2f} >= {threshold:.2f})",
                context={"path": f"{self._parent_path}.{best_candidate}"}
            )
            history.record_success(
                category="API",
                original=expected_key,
                healed=best_candidate,
                confidence=best_confidence,
                test_name=test_name,
                reason="Dynamic field rename candidate validated"
            )
            return val

        # Step 4: Confidence below threshold -> Fail safely without masking defects
        reporter.log_api_healing(
            test_name=test_name,
            expected=expected_key,
            candidate=best_candidate or "None",
            value_type=type(super().__getitem__(best_candidate)).__name__ if best_candidate else "Unknown",
            confidence=best_confidence,
            status="REJECTED",
            reason=f"Confidence {best_confidence:.2f} is below required threshold {threshold:.2f}"
        )
        raise KeyError(key)


class SelfHealingResponse:
    """Wrapper around requests.Response that instruments `.json()` with SelfHealingDict."""

    def __init__(self, response: Any):
        self._raw_response = response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw_response, name)

    def json(self, **kwargs) -> Any:
        raw_json = self._raw_response.json(**kwargs)
        if isinstance(raw_json, dict):
            return SelfHealingDict(raw_json)
        elif isinstance(raw_json, list):
            return [SelfHealingDict(item) if isinstance(item, dict) else item for item in raw_json]
        return raw_json


class APIHealer:
    """Static and instance methods for API contract, schema, and JSONPath healing."""

    @staticmethod
    def heal_jsonpath(data: Dict[str, Any], path: str) -> Tuple[Optional[Any], Optional[str], float]:
        """
        Evaluates a JSONPath such as '$.data.user.name'.
        If path fails, searches candidate branches for equivalent values.
        Returns (healed_value, healed_path, confidence).
        """
        clean_path = path.lstrip("$.").strip()
        tokens = clean_path.split(".")

        # Try direct resolution
        curr = data
        found = True
        for t in tokens:
            if isinstance(curr, dict) and t in curr:
                curr = curr[t]
            else:
                found = False
                break

        if found:
            return curr, path, 1.0

        if not SelfHealingConfig.is_api_enabled():
            return None, None, 0.0

        # Attempt to locate target leaf key in tree
        target_key = tokens[-1]
        candidates: List[Tuple[Any, str, float]] = []

        def search_tree(node: Any, current_path: str):
            if isinstance(node, dict):
                for k, v in node.items():
                    p = f"{current_path}.{k}"
                    score = ConfidenceEngine.calculate_name_similarity(target_key, k)
                    if score >= SelfHealingConfig.get_confidence_threshold():
                        candidates.append((v, p, score))
                    search_tree(v, p)
            elif isinstance(node, list):
                for idx, item in enumerate(node):
                    search_tree(item, f"{current_path}[{idx}]")

        search_tree(data, "$")

        if candidates:
            # Sort by highest confidence score
            candidates.sort(key=lambda x: x[2], reverse=True)
            best_val, best_path, best_score = candidates[0]
            reporter = HealingReporter.get_instance()
            reporter.log_api_healing(
                test_name=get_current_test_name(),
                expected=path,
                candidate=best_path,
                value_type=type(best_val).__name__,
                confidence=best_score,
                status="HEALED",
                reason=f"JSONPath structure alternative validated ({best_path})"
            )
            return best_val, best_path, best_score

        return None, None, 0.0

    @staticmethod
    def heal_schema(actual_data: Dict[str, Any], expected_schema: Dict[str, type]) -> Dict[str, str]:
        """
        Analyzes differences between expected schema types and actual payload keys.
        Generates mapped dictionary: { expected_key: candidate_key }.
        """
        mappings: Dict[str, str] = {}
        threshold = SelfHealingConfig.get_confidence_threshold()

        for exp_key, exp_type in expected_schema.items():
            if exp_key in actual_data:
                mappings[exp_key] = exp_key
                continue

            # Candidate evaluation
            best_cand = None
            best_score = 0.0
            for act_key, act_val in actual_data.items():
                if act_key in mappings.values():
                    continue
                type_match = 1.0 if isinstance(act_val, exp_type) else 0.1
                score = (ConfidenceEngine.calculate_name_similarity(exp_key, act_key) * 0.6) + (type_match * 0.4)
                if score > best_score:
                    best_score = score
                    best_cand = act_key

            if best_cand and best_score >= threshold:
                mappings[exp_key] = best_cand
                logger.info(
                    f"[API-SELF-HEALING] Possible schema mapping: {exp_key} -> {best_cand} "
                    f"(Confidence: {best_score * 100:.1f}%)"
                )

        return mappings

    @staticmethod
    def resolve_endpoint_alternative(
        client_session: Any,
        base_url: str,
        method: str,
        endpoint: str,
        known_routes: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Evaluates alternative endpoint path if a known route exists with high confidence.
        Does NOT brute-force or send random requests.
        """
        if not known_routes:
            return None

        clean_endpoint = endpoint.strip("/")
        best_route = None
        best_score = 0.0

        for route in known_routes:
            clean_route = route.strip("/")
            score = ConfidenceEngine.calculate_name_similarity(clean_endpoint, clean_route)
            if score > best_score:
                best_score = score
                best_route = route

        if best_route and best_score >= SelfHealingConfig.get_confidence_threshold():
            logger.info(
                f"[API-SELF-HEALING] Endpoint candidate identified: {endpoint} -> {best_route} "
                f"(Confidence: {best_score * 100:.1f}%)"
            )
            return best_route

        return None
