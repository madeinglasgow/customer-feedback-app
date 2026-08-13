from app.models import FeedbackCategory, UrgencyLevel
from app.services.triage import TriageEngine, build_default_ruleset
from app.services.triage.rules.base import contains_term
from tests.conftest import make_submission


def assess(message, category=FeedbackCategory.PRODUCT, order_id=None, history=None):
    engine = TriageEngine(build_default_ruleset(billing_history_lookup=history))
    return engine.assess(
        make_submission(message=message, category=category, order_id=order_id)
    )


class TestContainsTerm:
    def test_matches_whole_words_only(self):
        assert contains_term("the kiln fired the glaze beautifully", ["fire"]) is None

    def test_matches_word_case_insensitively(self):
        assert contains_term("There was a FIRE in the box", ["fire"]) == "fire"

    def test_matches_phrases(self):
        assert contains_term("it caught fire yesterday", ["caught fire"]) == "caught fire"


class TestSafetyHazard:
    def test_safety_term_is_critical(self):
        result = assess("The heater started sparking and then caught fire.")
        assert result.level == UrgencyLevel.CRITICAL
        assert result.rule == "safety_hazard"

    def test_applies_across_categories(self):
        result = assess(
            "The package arrived with smoke damage and burned wrapping",
            category=FeedbackCategory.SHIPPING,
        )
        assert result.level == UrgencyLevel.CRITICAL

    def test_fired_is_not_fire(self):
        result = assess("The glaze is beautifully fired ceramic, love it")
        assert result.level == UrgencyLevel.LOW  # compliment, not a safety issue
        assert result.rule == "compliment"


class TestSuspectedFraud:
    def test_unauthorized_charge_is_critical(self):
        result = assess(
            "There is a charge on my card I did not authorize",
            category=FeedbackCategory.BILLING,
        )
        assert result.level == UrgencyLevel.CRITICAL
        assert result.rule == "suspected_fraud"

    def test_fraud_fires_outside_billing_too(self):
        result = assess("I think this whole thing is a scam", category=FeedbackCategory.OTHER)
        assert result.level == UrgencyLevel.CRITICAL


class TestChurnThreat:
    def test_leaving_threat_is_high(self):
        result = assess("Fix this or I am taking my business elsewhere")
        assert result.level == UrgencyLevel.HIGH
        assert result.rule == "churn_threat"


class TestRepeatedBillingFailure:
    def test_retry_phrasing_is_high(self):
        result = assess(
            "My card was charged twice for the same order",
            category=FeedbackCategory.BILLING,
        )
        assert result.level == UrgencyLevel.HIGH
        assert result.rule == "repeated_billing_failure"

    def test_history_of_two_prior_complaints_is_high(self):
        result = assess(
            "My payment did not go through today",
            category=FeedbackCategory.BILLING,
            history=lambda email: 2,
        )
        assert result.level == UrgencyLevel.HIGH
        assert result.rule == "repeated_billing_failure"

    def test_single_prior_complaint_stays_normal(self):
        result = assess(
            "My payment did not go through today",
            category=FeedbackCategory.BILLING,
            history=lambda email: 1,
        )
        assert result.level == UrgencyLevel.NORMAL

    def test_rule_does_not_apply_outside_billing(self):
        result = assess(
            "This has failed again and again",
            category=FeedbackCategory.PRODUCT,
        )
        assert result.rule != "repeated_billing_failure"


class TestLostPackage:
    def test_lost_with_order_id_is_high(self):
        result = assess(
            "My package never arrived",
            category=FeedbackCategory.SHIPPING,
            order_id="ORD-1234",
        )
        assert result.level == UrgencyLevel.HIGH
        assert result.rule == "lost_package"

    def test_lost_without_order_id_is_normal(self):
        result = assess("My package never arrived", category=FeedbackCategory.SHIPPING)
        assert result.level == UrgencyLevel.NORMAL
        assert "cannot trace" in result.rationale


class TestCompliment:
    def test_pure_compliment_is_low(self):
        result = assess("Thank you, the quality is excellent!")
        assert result.level == UrgencyLevel.LOW
        assert result.rule == "compliment"

    def test_mixed_sentiment_is_not_a_compliment(self):
        result = assess("I love the design but it arrived broken")
        assert result.level == UrgencyLevel.NORMAL
        assert result.rule == "category_baseline"


class TestEngineAndBaselines:
    def test_highest_severity_wins(self):
        result = assess(
            "Great product usually, but this one caught fire. I love your store."
        )
        assert result.level == UrgencyLevel.CRITICAL
        assert result.rule == "safety_hazard"

    def test_plain_complaint_gets_category_baseline(self):
        result = assess("The color is different from the photos")
        assert result.level == UrgencyLevel.NORMAL
        assert result.rule == "category_baseline"

    def test_other_category_baseline_is_low(self):
        result = assess("Just wanted to mention your site font is odd", category=FeedbackCategory.OTHER)
        assert result.level == UrgencyLevel.LOW
        assert result.rule == "category_baseline"
