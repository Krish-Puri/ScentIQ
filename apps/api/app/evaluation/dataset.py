"""SCENTIQ Benchmark Evaluation Dataset (Milestone 3 - Part 3.2).
Contains 10 curated evaluation scenarios with ground-truth relevance judgements,
personas, constraints, and feedback profiles.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from app.models.enums import FeedbackType
from app.schemas.recommendation import RecommendationConstraints


@dataclass
class PersonaProfile:
    familiarity_level: str = "enthusiast"
    preferred_families: List[str] = field(default_factory=list)
    liked_notes: List[str] = field(default_factory=list)
    liked_accords: List[str] = field(default_factory=list)
    avoid_terms: List[str] = field(default_factory=list)
    budget_max: Optional[float] = None
    occasions: List[str] = field(default_factory=list)


@dataclass
class FeedbackAction:
    fragrance_slug: str
    feedback_type: FeedbackType
    rating: Optional[float] = None


@dataclass
class EvaluationScenario:
    id: str
    name: str
    description: str
    persona: PersonaProfile
    query_constraints: RecommendationConstraints
    feedback_history: List[FeedbackAction] = field(default_factory=list)
    # Graded relevance: 3 = Highly Relevant, 2 = Relevant, 1 = Acceptable, 0 = Irrelevant
    ground_truth_relevance: Dict[str, float] = field(default_factory=dict)


EVALUATION_SCENARIOS: List[EvaluationScenario] = [
    # Scenario 1: Fresh citrus for hot/humid summer (Mumbai/Chennai)
    EvaluationScenario(
        id="SCENARIO_01",
        name="Hot & Humid Summer Fresh Citrus",
        description="Fresh citrus, aquatic and aromatic fragrances tailored for coastal Indian summers.",
        persona=PersonaProfile(
            preferred_families=["Citrus", "Aquatic"],
            liked_notes=["Bergamot", "Grapefruit", "Lemon"],
            liked_accords=["Citrus", "Aquatic"],
            occasions=["summer"],
        ),
        query_constraints=RecommendationConstraints(
            liked_families=["Citrus", "Aquatic"],
            liked_accords=["Citrus", "Aquatic"],
            occasions=["summer"],
            avoid_terms=["leather", "tobacco"],
        ),
        ground_truth_relevance={
            "armani-acqua-di-gio-edt": 3.0,
            "armani-adg-profondo-edp": 3.0,
            "afnan-turathi-blue-edp": 3.0,
            "rasasi-hawas-for-men-edp": 3.0,
            "chanel-allure-homme-sport-edt": 3.0,
            "versace-dylan-blue-edt": 2.0,
            "bombay-shaving-co-mexico-edt": 2.0,
            "the-man-company-blanc-edp": 2.0,
            "bella-vita-skai-aquatic-edp": 2.0,
            "chanel-bleu-de-chanel-edp": 1.0,
        },
    ),

    # Scenario 2: Woody and spicy for professional office wear
    EvaluationScenario(
        id="SCENARIO_02",
        name="Professional Office Woody Spicy",
        description="Refined cedar, vetiver, and subtle fresh spice without loud sweet projection.",
        persona=PersonaProfile(
            preferred_families=["Woody", "Woody Spicy"],
            liked_notes=["Cedarwood", "Vetiver", "Pink Pepper"],
            liked_accords=["Woody", "Fresh Spicy"],
            avoid_terms=["sweet", "bubblegum", "vanilla"],
            occasions=["office"],
        ),
        query_constraints=RecommendationConstraints(
            liked_families=["Woody", "Woody Spicy"],
            liked_accords=["Woody", "Fresh Spicy"],
            occasions=["office"],
            avoid_terms=["sweet", "vanilla"],
        ),
        ground_truth_relevance={
            "hermes-terre-d-hermes-edt": 3.0,
            "rasasi-fattan-pour-homme-edp": 3.0,
            "tom-ford-grey-vetiver-edp": 3.0,
            "chanel-bleu-de-chanel-edp": 3.0,
            "dior-homme-intense-edp": 2.0,
            "bella-vita-ceo-man-edp": 2.0,
            "the-man-company-black-edt": 2.0,
        },
    ),

    # Scenario 3: Affordable alternative to Creed Aventus
    EvaluationScenario(
        id="SCENARIO_03",
        name="Affordable Creed Aventus Alternative",
        description="Fruity smoky birch composition under ₹3,500 INR offering the Aventus DNA.",
        persona=PersonaProfile(
            liked_notes=["Pineapple", "Birch", "Bergamot"],
            liked_accords=["Fruity", "Smoky"],
            budget_max=3500.0,
        ),
        query_constraints=RecommendationConstraints(
            budget_max_inr=3500.0,
            hard_budget_limit=True,
            liked_accords=["Fruity", "Smoky"],
        ),
        ground_truth_relevance={
            "armaf-club-de-nuit-intense-man-edt": 3.0,
            "afnan-supremacy-silver-edp": 3.0,
            "afnan-turathi-blue-edp": 2.0,
            "rasasi-hawas-for-men-edp": 1.0,
        },
    ),

    # Scenario 4: Strict budget constraint (under ₹2,000 INR)
    EvaluationScenario(
        id="SCENARIO_04",
        name="Strict Budget Cap Under ₹2,000 INR",
        description="Strict budget ceiling enforcement where all returned options must be <= ₹2,000.",
        persona=PersonaProfile(
            budget_max=2000.0,
        ),
        query_constraints=RecommendationConstraints(
            budget_max_inr=2000.0,
            hard_budget_limit=True,
        ),
        ground_truth_relevance={
            "rasasi-fattan-pour-homme-edp": 3.0,
            "armaf-club-de-nuit-intense-man-edt": 3.0,
            "lattafa-asad-edp": 3.0,
            "lattafa-badee-al-oud-edp": 3.0,
            "lattafa-fakhar-black-edp": 3.0,
            "ajmal-kuro-edp": 3.0,
            "maison-alhambra-woody-oud-edp": 3.0,
            "maison-alhambra-tobacco-touch-edp": 3.0,
            "bella-vita-skai-aquatic-edp": 2.0,
            "bella-vita-white-oud-edp": 2.0,
            "bombay-shaving-co-mexico-edt": 2.0,
            "the-man-company-blanc-edp": 2.0,
        },
    ),

    # Scenario 5: Evening / date night with high longevity
    EvaluationScenario(
        id="SCENARIO_05",
        name="Date Night High Longevity",
        description="Warm spicy, cardamom, tonka, and vanilla concoctions for romantic evenings.",
        persona=PersonaProfile(
            preferred_families=["Amber", "Amber Spicy"],
            liked_notes=["Cardamom", "Vanilla", "Cinnamon", "Tonka Bean"],
            liked_accords=["Warm Spicy", "Vanilla", "Amber"],
            occasions=["date"],
        ),
        query_constraints=RecommendationConstraints(
            liked_families=["Amber", "Amber Spicy"],
            liked_accords=["Warm Spicy", "Vanilla", "Amber"],
            occasions=["date"],
        ),
        ground_truth_relevance={
            "ysl-la-nuit-de-lhomme-edt": 3.0,
            "kilian-angels-share-edp": 3.0,
            "lattafa-khamrah-edp": 3.0,
            "tom-ford-noir-extreme-edp": 3.0,
            "tom-ford-tobacco-vanille-edp": 3.0,
            "jpg-le-male-le-parfum-edp": 3.0,
            "afnan-9pm-edp": 2.0,
            "al-haramain-detour-noir-edp": 2.0,
        },
    ),

    # Scenario 6: Strict avoidance (absolutely no vanilla or sweet notes)
    EvaluationScenario(
        id="SCENARIO_06",
        name="Strict Avoidance: No Vanilla or Sweet Notes",
        description="Dry, mineral, earthy or pure citrus profiles with zero tolerance for vanilla or gourmand sweetness.",
        persona=PersonaProfile(
            preferred_families=["Woody", "Citrus"],
            avoid_terms=["vanilla", "sweet", "gourmand"],
        ),
        query_constraints=RecommendationConstraints(
            liked_families=["Woody", "Citrus"],
            avoid_terms=["vanilla", "sweet", "gourmand"],
        ),
        ground_truth_relevance={
            "hermes-terre-d-hermes-edt": 3.0,
            "rasasi-fattan-pour-homme-edp": 3.0,
            "tom-ford-grey-vetiver-edp": 3.0,
            "armani-acqua-di-gio-edt": 3.0,
            "chanel-bleu-de-chanel-edp": 2.0,
            "bombay-shaving-co-mexico-edt": 2.0,
        },
    ),

    # Scenario 7: Beginner versatile daily wear
    EvaluationScenario(
        id="SCENARIO_07",
        name="Beginner Signature Daily Driver",
        description="Mass-pleasing, forgiving, versatile daily fragrances with high mass-market appeal.",
        persona=PersonaProfile(
            familiarity_level="new",
            preferred_families=["Woody Aromatic", "Fresh"],
            occasions=["versatile", "casual"],
        ),
        query_constraints=RecommendationConstraints(
            liked_families=["Woody Aromatic", "Fresh"],
            occasions=["versatile", "casual"],
        ),
        ground_truth_relevance={
            "chanel-bleu-de-chanel-edp": 3.0,
            "dior-sauvage-edt": 3.0,
            "versace-dylan-blue-edt": 3.0,
            "ysl-y-edp": 3.0,
            "afnan-turathi-blue-edp": 2.0,
            "the-man-company-blanc-edp": 2.0,
            "bella-vita-ceo-man-edp": 2.0,
        },
    ),

    # Scenario 8: Niche quality / distinctive
    EvaluationScenario(
        id="SCENARIO_08",
        name="Niche Distinction & Complexity",
        description="Distinctive artistic perfumery focusing on precious raw materials (agarwood, saffron, ambergris).",
        persona=PersonaProfile(
            familiarity_level="collector",
            preferred_families=["Amber", "Woody Oriental", "Chypre"],
            liked_notes=["Oud", "Saffron", "Ambergris", "Birch"],
        ),
        query_constraints=RecommendationConstraints(
            liked_families=["Amber", "Woody Oriental", "Chypre"],
            liked_notes=["Oud", "Saffron", "Ambergris"],
        ),
        ground_truth_relevance={
            "mfk-baccarat-rouge-540-edp": 3.0,
            "tom-ford-oud-wood-edp": 3.0,
            "creed-aventus-edp": 3.0,
            "kilian-angels-share-edp": 3.0,
            "mfk-grand-soir-edp": 3.0,
            "lattafa-badee-al-oud-edp": 2.0,
            "maison-alhambra-woody-oud-edp": 2.0,
        },
    ),

    # Scenario 9: Contradictory / mutually exclusive constraints handling
    EvaluationScenario(
        id="SCENARIO_09",
        name="Contradictory Constraints: Luxury Aura on Student Budget",
        description="Query asks for luxury Tom Ford / Kilian profile but imposes hard ₹2,500 budget cap.",
        persona=PersonaProfile(
            liked_notes=["Oud", "Cognac", "Tobacco"],
            budget_max=2500.0,
        ),
        query_constraints=RecommendationConstraints(
            budget_max_inr=2500.0,
            hard_budget_limit=True,
            liked_notes=["Oud", "Tobacco"],
        ),
        ground_truth_relevance={
            "lattafa-khamrah-edp": 3.0,
            "lattafa-badee-al-oud-edp": 3.0,
            "maison-alhambra-woody-oud-edp": 3.0,
            "maison-alhambra-tobacco-touch-edp": 3.0,
            "lattafa-ameer-al-oudh-intense-edp": 2.0,
        },
    ),

    # Scenario 10: Returning user with feedback profile
    EvaluationScenario(
        id="SCENARIO_10",
        name="Returning User With Feedback History",
        description="Returning enthusiast who has given positive feedback to Rasasi Fattan and negative feedback to overly sweet gourmands.",
        persona=PersonaProfile(
            familiarity_level="enthusiast",
            preferred_families=["Woody Mineral"],
            avoid_terms=["sweet"],
        ),
        query_constraints=RecommendationConstraints(
            liked_families=["Woody Mineral"],
            avoid_terms=["sweet"],
        ),
        feedback_history=[
            FeedbackAction(fragrance_slug="rasasi-fattan-pour-homme-edp", feedback_type=FeedbackType.LIKE, rating=5.0),
            FeedbackAction(fragrance_slug="lattafa-khamrah-edp", feedback_type=FeedbackType.NOT_FOR_ME, rating=1.5),
        ],
        ground_truth_relevance={
            "rasasi-fattan-pour-homme-edp": 3.0,
            "hermes-terre-d-hermes-edt": 3.0,
            "tom-ford-grey-vetiver-edp": 3.0,
            "chanel-bleu-de-chanel-edp": 2.0,
        },
    ),
]

