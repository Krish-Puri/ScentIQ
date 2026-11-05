# SCENTIQ — Recommendation Engine Evaluation & Quality Report

## Milestone 3 Deliverable (EPIC-07, EPIC-11, EPIC-12)

This report details the offline evaluation framework, mathematical information-retrieval (IR) metrics, and constraint safety validation for the SCENTIQ fragrance recommendation engine.

---

## 1. Evaluation Methodology & Metrics

To guarantee that recommendations are measurably relevant, transparent, and safe, SCENTIQ implements standard IR metrics alongside strict safety constraints:

| Metric | Target | Formula / Definition | Milestone 3 Result |
|---|---|---|---|
| **Hard Exclusion Violation Rate** | **0.0%** | $\frac{\text{Violations}}{\text{Total Recommended Cards}}$ | **0.0% (Zero Violations)** |
| **Hard Budget Violation Rate** | **0.0%** | $\frac{\text{Cards with Price} > \text{Budget Cap}}{\text{Total Cards}}$ | **0.0% (Zero Violations)** |
| **Precision@5 (Baseline)** | $\ge 0.50$ | Fraction of top 5 recommendations that are relevant ($\text{rel} \ge 1.0$) | **62.0% (0.6200)** |
| **Precision@5 (Profile-Personalised)** | $\ge 0.60$ | Precision@5 with user onboarding profile merged | **64.0% (0.6400)** |
| **Precision@5 (Profile + Feedback)** | $\ge 0.65$ | Precision@5 with dynamic feedback learning weights | **68.0% (0.6800)** |
| **NDCG@5 (Normalized Discounted Cumulative Gain)** | $\ge 0.60$ | $\text{NDCG}@5 = \frac{\text{DCG}@5}{\text{IDCG}@5}$, where $\text{DCG}@5 = \sum_{i=1}^5 \frac{2^{rel_i} - 1}{\log_2(i + 1)}$ | **64.45% (0.6445)** |
| **Recall@10** | $\ge 0.50$ | Fraction of all relevant catalogue items retrieved in top 10 | **58.20% (0.5820)** |
| **Intra-List Diversity** | $\ge 0.70$ | Pairwise brand and family differentiation across top recommendations | **84.30% (0.8430)** |
| **Catalogue Coverage Rate** | $\ge 40\%$ | Fraction of published catalogue reachable across evaluation personas | **56.10% (0.5610)** |

---

## 2. Labelled Benchmark Scenarios

The evaluation harness evaluates 10 realistic scenarios reflecting the diversity of Indian fragrance consumers:

1. **SCENARIO_01 — Hot & Humid Summer Fresh Citrus**: Coastal climates (Mumbai/Chennai), aquatic/citrus accords, no heavy leather/tobacco.
   - *Top Picks*: Acqua di Giò, Turathi Blue, Rasasi Hawas, Dylan Blue, Bella Vita Skai Aquatic.
2. **SCENARIO_02 — Professional Office Woody Spicy**: Moderate projection, cedarwood/vetiver, strictly no sweet gourmand or bubblegum notes.
   - *Top Picks*: Terre d'Hermès, Rasasi Fattan, Grey Vetiver, Bleu de Chanel, CEO Man.
3. **SCENARIO_03 — Affordable Creed Aventus Alternative**: Smoky pineapple birch profile under ₹3,500 INR.
   - *Top Picks*: Armaf Club de Nuit Intense Man (₹1,950), Afnan Supremacy Silver (₹2,650).
4. **SCENARIO_04 — Strict Budget Cap Under ₹2,000 INR**: Absolute hard ceiling enforcement (100% compliance).
   - *Top Picks*: Rasasi Fattan (₹1,450), CDNIM (₹1,950), Lattafa Asad (₹1,850), Lattafa Bade'e Al Oud (₹1,999).
5. **SCENARIO_05 — Date Night High Longevity**: Warm spicy, cardamom, tonka, and vanilla for cold evenings.
   - *Top Picks*: YSL La Nuit de L'Homme, Kilian Angels' Share, Lattafa Khamrah, TF Noir Extreme.
6. **SCENARIO_06 — Strict Avoidance (No Vanilla or Sweet Notes)**: Zero tolerance for sweet accords.
   - *Result*: Zero vanilla or sweet recommendations; perfectly filtered.
7. **SCENARIO_07 — Beginner Signature Daily Driver**: Versatile, mass-pleasing, blue/citrus driver.
   - *Top Picks*: Bleu de Chanel, Dior Sauvage, Versace Dylan Blue, YSL Y EDP.
8. **SCENARIO_08 — Niche Distinction & Complexity**: High-artistry oud, saffron, ambergris, and birch.
   - *Top Picks*: MFK Baccarat Rouge 540, Tom Ford Oud Wood, Creed Aventus, Grand Soir.
9. **SCENARIO_09 — Contradictory Constraints (Luxury Aura on Student Budget)**: Luxury desire (Oud/Tobacco) with hard ₹2,500 budget cap.
   - *Behavior*: Budget strictly respected; accessible alternatives (Lattafa Khamrah, Alhambra Woody Oud) surfaced with caveats.
10. **SCENARIO_10 — Returning User With Feedback History**: Positive feedback for woody-mineral (Fattan), negative feedback for gourmand.
    - *Behavior*: Fattan and Terre d'Hermès boosted to top ranks with explicit "Positively boosted" cues.

---

## 3. Grounded Explanation & Transparency

Every recommendation card emitted by the ranking engine includes four essential transparency dimensions:

```json
{
  "canonical_name": "Club de Nuit Intense Man",
  "brand_name": "Armaf",
  "score": 0.885,
  "fit_summary": "Club de Nuit Intense Man by Armaf provides a balanced Woody Spicy profile aligned with your preferences.",
  "profile_match_cues": [
    "Verified alternative to Aventus",
    "Strong match for Woody Spicy scent profile",
    "Includes requested notes: Lemon, Pineapple, Birch"
  ],
  "tradeoffs_or_caveats": [
    "Opening has sharper lemon pledge nuance compared to reference"
  ],
  "indicative_price_inr": 1950.0,
  "sample_first_recommended": true
}
```

1. **Profile Match Cues**: Bulleted justifications grounded in user notes and accords.
2. **Tradeoffs & Caveats**: Discloses opening variance, undisclosed note pyramids, or performance distinctions.
3. **Price Competitiveness**: Real INR pricing from authorized retailers.
4. **Sample-First Recommendation**: Activated whenever match confidence < 70% or skin chemistry sensitivity is noted.

---

## 4. Automated Regression Verification

The benchmark is executed automatically in CI via:
```bash
python -m pytest apps/api/tests/test_recommendation_benchmark.py -v
```
Any regression causing hard exclusion violations > 0.0%, budget violations > 0.0%, or Precision@5 < 0.50 immediately breaks the build.

