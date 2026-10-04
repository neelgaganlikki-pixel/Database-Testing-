"""Unit and component tests verifying the API Self-Healing System (Section 29)."""
import pytest
from self_healing import (
    APIHealer,
    ConfidenceEngine,
    SelfHealingConfig,
    SelfHealingDict,
    SelfHealingResponse,
)


class DummyResponse:
    """Mock requests.Response for testing."""
    def __init__(self, data: dict, status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


class TestAPISelfHealing:
    """Verifies all 10 API self-healing capabilities defined in the specification."""

    def setup_method(self):
        SelfHealingConfig.reset_defaults()
        SelfHealingConfig.set_enabled(True)
        SelfHealingConfig.set_api_enabled(True)

    def teardown_method(self):
        SelfHealingConfig.reset_defaults()

    def test_01_original_field_exists(self):
        """1. Original field exists: returns cleanly with zero overhead and no healing needed."""
        payload = {"customer_id": 101, "email": "alice@example.com"}
        data = SelfHealingDict(payload)
        assert data["customer_id"] == 101
        assert data["email"] == "alice@example.com"

    def test_02_field_renamed_high_confidence(self):
        """2. Field renamed: recovers when expected 'userName' changes to 'username'."""
        payload = {"username": "NeelGagan", "email": "neel@example.com"}
        data = SelfHealingDict(payload)
        # Expected field was userName
        healed_value = data["userName"]
        assert healed_value == "NeelGagan"

    def test_03_nested_field_changed(self):
        """3. Nested field changed: recovers when a nested object attribute changes case/format."""
        payload = {
            "customer": {
                "first_name": "Neel",
                "phone_number": "+1-555-0199"
            }
        }
        data = SelfHealingDict(payload)
        # Expected 'phoneNumber' inside customer dict
        assert data["customer"]["phoneNumber"] == "+1-555-0199"

    def test_04_jsonpath_changed(self):
        """4. JSONPath changed: adapts from $.data.user.name to $.result.user.name."""
        payload = {
            "result": {
                "user": {
                    "name": "Alice"
                }
            }
        }
        val, healed_path, conf = APIHealer.heal_jsonpath(payload, "$.data.user.name")
        assert val == "Alice"
        assert conf >= 0.85
        assert "result.user.name" in healed_path

    def test_05_schema_changed_diagnostic(self):
        """5. Schema changed: detects schema mapping (userId -> id, userName -> username)."""
        actual_payload = {
            "id": 42,
            "username": "tester",
            "active": True
        }
        expected_schema = {
            "userId": int,
            "userName": str,
            "active": bool
        }
        mappings = APIHealer.heal_schema(actual_payload, expected_schema)
        assert mappings["userId"] == "id"
        assert mappings["userName"] == "username"
        assert mappings["active"] == "active"

    def test_06_multiple_possible_mappings_selects_best(self):
        """6. Multiple possible mappings: selects candidate with highest composite score."""
        payload = {
            "cust_id": 500,
            "customer_identifier": 500,
            "unrelated_field": "test"
        }
        data = SelfHealingDict(payload)
        # 'customer_id' should map to 'customer_identifier' or 'cust_id' with high confidence
        val = data["customer_id"]
        assert val == 500

    def test_07_high_confidence_mapping_heals(self):
        """7. High-confidence mapping: customerId -> customer_id heals automatically."""
        payload = {"customer_id": 999}
        data = SelfHealingDict(payload)
        assert data["customerId"] == 999

    def test_08_low_confidence_mapping_fails_safely(self):
        """8. Low-confidence mapping: unrelated fields (e.g. total_amount -> password) MUST fail."""
        payload = {"password": "secret", "is_active": True}
        data = SelfHealingDict(payload)
        with pytest.raises(KeyError):
            _ = data["total_amount"]

    def test_09_endpoint_version_change(self):
        """9. Endpoint version change: suggests /api/v2/users when /api/v1/users is requested."""
        known_routes = ["/api/v2/users", "/api/v2/orders", "/api/v2/products"]
        candidate = APIHealer.resolve_endpoint_alternative(
            client_session=None,
            base_url="http://127.0.0.1:8000",
            method="GET",
            endpoint="/api/v1/users",
            known_routes=known_routes
        )
        assert candidate == "/api/v2/users"

    def test_10_healing_disabled_preserves_strict_failure(self):
        """10. Healing disabled: when SELF_HEALING_ENABLED=False, KeyError is raised."""
        SelfHealingConfig.set_api_enabled(False)
        payload = {"username": "Neel"}
        data = SelfHealingDict(payload)
        with pytest.raises(KeyError):
            _ = data["userName"]

