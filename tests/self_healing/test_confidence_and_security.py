"""Unit tests for ConfidenceEngine scoring and Security masking."""
import pytest
from self_healing import (
    ConfidenceEngine,
    FailureClassifier,
    HealingHistory,
    HealingReporter,
    mask_sensitive_data,
)


class TestConfidenceAndSecurity:
    """Verifies confidence calculations, historical weights, masking, and failure classification."""

    def test_confidence_exact_and_normalized(self):
        # Exact
        assert ConfidenceEngine.calculate_name_similarity("first_name", "first_name") == 1.0
        # Camel to snake
        assert ConfidenceEngine.calculate_name_similarity("firstName", "first_name") >= 0.95
        # Pascal to snake
        assert ConfidenceEngine.calculate_name_similarity("FirstName", "first_name") >= 0.95
        # Kebab to snake
        assert ConfidenceEngine.calculate_name_similarity("first-name", "first_name") >= 0.95

    def test_confidence_synonyms_and_abbreviations(self):
        score = ConfidenceEngine.calculate_name_similarity("cust_id", "customer_id")
        assert score >= 0.90
        score2 = ConfidenceEngine.calculate_name_similarity("prod_id", "product_id")
        assert score2 >= 0.90

    def test_confidence_type_penalties(self):
        # int vs str
        score = ConfidenceEngine.calculate_confidence("user_id", "user_id_str", expected_val=10, candidate_val="ten")
        assert score < 0.70

    def test_security_sensitive_data_masking(self):
        raw_dict = {
            "user_id": 123,
            "password": "SuperSecretPassword!",
            "auth_token": "bearer_abc_123",
            "nested": {
                "apiKey": "xyz_key",
                "normal": "safe_value"
            }
        }
        masked = mask_sensitive_data(raw_dict)
        assert masked["password"] == "******"
        assert masked["auth_token"] == "******"
        assert masked["nested"]["apiKey"] == "******"
        assert masked["nested"]["normal"] == "safe_value"
        assert masked["user_id"] == 123

    def test_failure_classification(self):
        assert FailureClassifier.classify_api_failure("user", status_code=401) == FailureClassifier.AUTHENTICATION
        assert FailureClassifier.classify_api_failure("user", status_code=500) == FailureClassifier.API_APPLICATION
        assert FailureClassifier.classify_db_failure("col", "Can't connect to MySQL server") == FailureClassifier.DB_CONNECTION
        assert FailureClassifier.classify_db_failure("col", "Unknown column 'xyz' in 'field list'") == FailureClassifier.SCHEMA_MAPPING

