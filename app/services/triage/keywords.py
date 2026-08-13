"""Term lists used by the severity rules.

Matching is done with word boundaries (see rules/base.py), so "fire" does not
match "fired". Multi-word entries are matched as phrases.
"""

SAFETY_TERMS = [
    "fire",
    "caught fire",
    "smoke",
    "smoking",
    "sparks",
    "sparking",
    "burn",
    "burned",
    "burning",
    "shock",
    "shocked",
    "electrocuted",
    "overheat",
    "overheating",
    "explode",
    "exploded",
    "injury",
    "injured",
    "hospital",
    "unsafe",
]

FRAUD_INDICATORS = [
    "unauthorized",
    "fraud",
    "fraudulent",
    "stolen card",
    "did not authorize",
    "didn't authorize",
    "never authorized",
    "identity theft",
    "scam",
    "scammed",
]

CHURN_PHRASES = [
    "cancel my account",
    "close my account",
    "never ordering again",
    "never buying again",
    "never shopping here again",
    "switching to",
    "taking my business elsewhere",
    "last order i ever",
    "done with this company",
]

BILLING_RETRY_PHRASES = [
    "charged again",
    "charged twice",
    "double charged",
    "second time",
    "third time",
    "keeps failing",
    "failed again",
    "multiple times",
    "every month",
]

POSITIVE_TERMS = [
    "love",
    "loved",
    "great",
    "wonderful",
    "excellent",
    "amazing",
    "fantastic",
    "thank you",
    "thanks",
    "perfect",
    "beautiful",
    "beautifully",
]

NEGATIVE_TERMS = [
    "broken",
    "broke",
    "terrible",
    "awful",
    "horrible",
    "disappointed",
    "disappointing",
    "refund",
    "worst",
    "angry",
    "furious",
    "unacceptable",
]
