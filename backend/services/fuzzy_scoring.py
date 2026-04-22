"""
fuzzy_scoring.py — Production-Ready Fuzzy Logic Scoring Engine (Module 5)
=========================================================================
This module implements the DETERMINISTIC side of the Hybrid Fuzzy Logic + AI
scoring system. It takes 5 numerical scores extracted by the AI sub-agents
and applies a Fuzzy Inference System to calculate a mathematically fair,
reproducible final_score (0-100).

The same inputs ALWAYS produce the same output. This is legally defensible
and bias-resistant — unlike AI alone which can "mood swing" on scores.

Flow in the full pipeline:
  1. AI Agents extract raw scores (tech, growth, culture, execution, consistency)
  2. THIS module calculates the deterministic fuzzy_final_score
  3. The LLM Decision Maker receives this score and writes only the EXPLANATION

Usage:
  scorer = ApplicantFuzzyScorer()
  result = scorer.calculate_score(tech=82, growth=75, culture=90, execution=70, consistency=85)
  # result["fuzzy_final_score"] = 81.7

Dependencies:
  pip install scikit-fuzzy numpy
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)



class FuzzyScoreResult(BaseModel):
    """Result from the Fuzzy Logic scoring engine."""
    fuzzy_final_score: float = Field(description="Deterministic final score (0-100) from Fuzzy Logic math")
    deterministic_decision: str = Field(description="Decision label: 'strong_hire', 'hire', 'consider_further', or 'reject'")
    input_scores: dict = Field(description="The 5 raw input scores that were fed into the fuzzy engine")
    status: str = Field(description="'success' or 'error'")
    error_message: Optional[str] = Field(default=None)
    engine_used: str = Field(default="fuzzy_logic", description="'fuzzy_logic' or 'weighted_average_fallback'")



def extract_raw_scores_from_reports(
    screener_report,
    tech_report,
    culture_report,
    extracurricular_report=None,
    hackathon_report=None,
    code_quality_report=None,
    flight_risk_report=None,
    external_eval=None
) -> dict:
    """
    Extracts and normalizes the 5 pillar scores from all agent reports.
    Maps agent-specific fields to the 5 fuzzy logic inputs.

    Returns a dict: {tech, growth, culture, execution, consistency}
    """
    def safe_get(obj, *keys, default=50):
        """Safely extract a nested attribute from a Pydantic model or dict."""
        for key in keys:
            if obj is None:
                return default
            if hasattr(obj, key):
                obj = getattr(obj, key)
            elif isinstance(obj, dict):
                obj = obj.get(key, default)
                return obj
            else:
                return default
        return obj if isinstance(obj, (int, float)) else default

    # --- Pillar 1: Core Technical Competence ---
    tech_score = 50
    if tech_report:
        # TechReport typically has a tech_score or assessment fields
        ts = safe_get(tech_report, "technical_assessment_score", default=None)
        if ts is None:
            ts = safe_get(tech_report, "tech_score", default=None)
        if ts is None:
            # Derive from code quality if no explicit score
            cq = safe_get(code_quality_report, "code_quality_score", default=5)
            ts = min(100, int(cq * 10))
        tech_score = max(0, min(100, int(ts)))

    # --- Pillar 2: Growth Potential & Hustle ---
    growth_score = 50
    growth_signals = []
    if extracurricular_report:
        ec = safe_get(extracurricular_report, "extracurricular_score", default=None)
        if ec is not None:
            growth_signals.append(ec)
    if hackathon_report:
        hk = safe_get(hackathon_report, "hackathon_score", default=None)
        if hk is not None:
            growth_signals.append(hk)
    if growth_signals:
        growth_score = max(0, min(100, int(sum(growth_signals) / len(growth_signals))))

    # --- Pillar 3: Team & Cultural Fit ---
    culture_score = 50
    if culture_report:
        cs = safe_get(culture_report, "culture_score", default=None)
        if cs is None:
            cs = safe_get(culture_report, "cultural_fit_score", default=50)
        culture_score = max(0, min(100, int(cs)))

    # --- Pillar 4: Real-World Execution ---
    execution_score = 50
    execution_signals = []
    if external_eval and isinstance(external_eval, dict):
        ext_score = external_eval.get("overall_external_score", None)
        if ext_score is not None:
            execution_signals.append(ext_score)
    if code_quality_report:
        cq = safe_get(code_quality_report, "code_quality_score", default=5)
        # Code quality is 1-10, normalize to 0-100
        execution_signals.append(min(100, int(cq * 10)))
    if execution_signals:
        execution_score = max(0, min(100, int(sum(execution_signals) / len(execution_signals))))

    # --- Pillar 5: Consistency & Credibility ---
    consistency_score = 50
    consistency_signals = []
    if screener_report:
        sc = safe_get(screener_report, "consistency_score", default=None)
        if sc is None:
            sc = safe_get(screener_report, "credibility_score", default=50)
        consistency_signals.append(sc)
    if flight_risk_report:
        # Lower flight risk = higher consistency score
        risk_score = safe_get(flight_risk_report, "risk_score", default=0.3)
        consistency_from_risk = max(0, int((1 - risk_score) * 100))
        consistency_signals.append(consistency_from_risk)
    if consistency_signals:
        consistency_score = max(0, min(100, int(sum(consistency_signals) / len(consistency_signals))))

    return {
        "tech": tech_score,
        "growth": growth_score,
        "culture": culture_score,
        "execution": execution_score,
        "consistency": consistency_score
    }




class ApplicantFuzzyScorer:
    """
    Deterministic Fuzzy Inference System for candidate scoring.

    Takes 5 pillar scores (0-100) and outputs a mathematically calculated
    final score (0-100) using graduated membership functions and weighted rules.

    If scikit-fuzzy is not installed, falls back to an advanced weighted
    average with non-linear penalty rules.
    """

    def __init__(self):
        self._fuzzy_available = False
        self._setup_fuzzy_system()

    def _setup_fuzzy_system(self):
        """Initialize the scikit-fuzzy system. Gracefully degrades if not available."""
        try:
            import numpy as np
            import skfuzzy as fuzz
            from skfuzzy import control as ctrl

            # Antecedents (Inputs)
            self.tech = ctrl.Antecedent(np.arange(0, 101, 1), 'tech')
            self.growth = ctrl.Antecedent(np.arange(0, 101, 1), 'growth')
            self.culture = ctrl.Antecedent(np.arange(0, 101, 1), 'culture')
            self.execution = ctrl.Antecedent(np.arange(0, 101, 1), 'execution')
            self.consistency = ctrl.Antecedent(np.arange(0, 101, 1), 'consistency')

            # Consequent (Output)
            self.final_score = ctrl.Consequent(np.arange(0, 101, 1), 'final_score')

            # --- Membership Functions ---

            # Tech: stricter curve — must be meaningfully good
            self.tech['poor'] = fuzz.trimf(self.tech.universe, [0, 0, 45])
            self.tech['average'] = fuzz.trimf(self.tech.universe, [30, 55, 75])
            self.tech['good'] = fuzz.trimf(self.tech.universe, [60, 78, 95])
            self.tech['excellent'] = fuzz.trimf(self.tech.universe, [85, 100, 100])

            # Growth: forgiving curve — even average growth is positive
            self.growth['low'] = fuzz.trimf(self.growth.universe, [0, 0, 40])
            self.growth['medium'] = fuzz.trimf(self.growth.universe, [25, 55, 80])
            self.growth['high'] = fuzz.trimf(self.growth.universe, [65, 100, 100])

            # Culture: harsh penalty for bad culture fit
            self.culture['red_flag'] = fuzz.trimf(self.culture.universe, [0, 0, 35])
            self.culture['neutral'] = fuzz.trimf(self.culture.universe, [25, 55, 80])
            self.culture['champion'] = fuzz.trimf(self.culture.universe, [65, 100, 100])

            # Execution
            self.execution['basic'] = fuzz.trimf(self.execution.universe, [0, 0, 50])
            self.execution['industry_grade'] = fuzz.trimf(self.execution.universe, [40, 75, 100])

            # Consistency
            self.consistency['unreliable'] = fuzz.trimf(self.consistency.universe, [0, 0, 40])
            self.consistency['adequate'] = fuzz.trimf(self.consistency.universe, [30, 60, 85])
            self.consistency['credible'] = fuzz.trimf(self.consistency.universe, [70, 100, 100])

            # Final score output zones
            self.final_score['reject'] = fuzz.trimf(self.final_score.universe, [0, 0, 45])
            self.final_score['consider'] = fuzz.trimf(self.final_score.universe, [35, 58, 72])
            self.final_score['hire'] = fuzz.trimf(self.final_score.universe, [62, 78, 92])
            self.final_score['strong_hire'] = fuzz.trimf(self.final_score.universe, [85, 100, 100])

            # --- Fuzzy Rules ---
            rules = [
                # Fatal flaws → automatic reject
                ctrl.Rule(self.culture['red_flag'], self.final_score['reject']),
                ctrl.Rule(self.tech['poor'] & self.growth['low'], self.final_score['reject']),

                # The "Hustler Clause" — average tech but exceptional potential
                ctrl.Rule(self.tech['average'] & self.growth['high'] & self.culture['champion'], self.final_score['hire']),

                # The "Rockstar" spike — exceptional tech + real execution
                ctrl.Rule(self.tech['excellent'] & self.execution['industry_grade'], self.final_score['strong_hire']),
                ctrl.Rule(self.tech['excellent'] & self.consistency['credible'], self.final_score['strong_hire']),

                # Standard solid hire
                ctrl.Rule(self.tech['good'] & self.culture['neutral'] & self.execution['industry_grade'], self.final_score['hire']),
                ctrl.Rule(self.tech['good'] & self.culture['champion'] & self.consistency['credible'], self.final_score['hire']),

                # Mediocre — let's interview
                ctrl.Rule(self.tech['average'] & self.growth['medium'] & self.culture['neutral'], self.final_score['consider']),
                ctrl.Rule(self.tech['average'] & self.execution['basic'] & self.consistency['adequate'], self.final_score['consider']),

                # Low tech but other strong signals
                ctrl.Rule(self.tech['poor'] & self.growth['high'] & self.culture['champion'], self.final_score['consider']),
            ]

            self.scoring_system = ctrl.ControlSystem(rules)
            self.simulator = ctrl.ControlSystemSimulation(self.scoring_system)
            self._fuzzy_available = True
            logger.info("FuzzyScorer: scikit-fuzzy system initialized successfully.")

        except ImportError:
            logger.warning("FuzzyScorer: scikit-fuzzy not installed. Using weighted-average fallback. Run: pip install scikit-fuzzy numpy")
            self._fuzzy_available = False
        except Exception as e:
            logger.error(f"FuzzyScorer: Failed to initialize fuzzy system: {e}. Using fallback.")
            self._fuzzy_available = False

    def _weighted_average_fallback(self, tech, growth, culture, execution, consistency) -> float:
        """
        Advanced weighted average with non-linear penalty rules.
        Used when scikit-fuzzy is not installed.
        """
        # Culture red flag is a hard multiplier penalty
        culture_multiplier = 0.5 if culture < 35 else 1.0

        # Weights based on importance
        weights = {
            "tech": 0.35,
            "execution": 0.25,
            "culture": 0.20,
            "growth": 0.12,
            "consistency": 0.08
        }

        base_score = (
            tech * weights["tech"] +
            execution * weights["execution"] +
            culture * weights["culture"] +
            growth * weights["growth"] +
            consistency * weights["consistency"]
        )

        # Apply spike bonus: if tech OR growth is exceptional (90+), boost by 5
        spike_bonus = 5 if (tech >= 90 or growth >= 90) else 0

        final = (base_score + spike_bonus) * culture_multiplier
        return round(min(100, max(0, final)), 2)

    def calculate_score(
        self,
        tech: float,
        growth: float,
        culture: float,
        execution: float,
        consistency: float = 70
    ) -> FuzzyScoreResult:
        """
        Main scoring method. Takes 5 pillar scores (0-100) and returns a
        deterministic, mathematically fair final score.

        Args:
            tech: Core technical competence score (0-100)
            growth: Growth potential and hustle score (0-100)
            culture: Team and cultural fit score (0-100)
            execution: Real-world execution/projects score (0-100)
            consistency: Consistency and credibility score (0-100)

        Returns:
            FuzzyScoreResult with final score, decision label, and metadata.
        """
        inputs = {
            "tech": max(0, min(100, float(tech))),
            "growth": max(0, min(100, float(growth))),
            "culture": max(0, min(100, float(culture))),
            "execution": max(0, min(100, float(execution))),
            "consistency": max(0, min(100, float(consistency)))
        }

        try:
            if self._fuzzy_available:
                self.simulator.input['tech'] = inputs["tech"]
                self.simulator.input['growth'] = inputs["growth"]
                self.simulator.input['culture'] = inputs["culture"]
                self.simulator.input['execution'] = inputs["execution"]
                self.simulator.input['consistency'] = inputs["consistency"]
                self.simulator.compute()
                final_val = round(self.simulator.output['final_score'], 2)
                engine = "fuzzy_logic"
            else:
                final_val = self._weighted_average_fallback(**inputs)
                engine = "weighted_average_fallback"

            # Determine decision label
            if final_val >= 85:
                decision = "strong_hire"
            elif final_val >= 70:
                decision = "hire"
            elif final_val >= 50:
                decision = "consider_further"
            else:
                decision = "reject"

            return FuzzyScoreResult(
                fuzzy_final_score=final_val,
                deterministic_decision=decision,
                input_scores=inputs,
                status="success",
                engine_used=engine
            )

        except Exception as e:
            logger.error(f"FuzzyScorer calculation error: {e}")
            # Last resort fallback
            fallback_score = self._weighted_average_fallback(**inputs)
            return FuzzyScoreResult(
                fuzzy_final_score=fallback_score,
                deterministic_decision="consider_further",
                input_scores=inputs,
                status="error",
                error_message=str(e),
                engine_used="weighted_average_fallback"
            )




_scorer_instance = None

def get_fuzzy_scorer() -> ApplicantFuzzyScorer:
    """Returns the singleton FuzzyScorer instance (initializes on first call)."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = ApplicantFuzzyScorer()
    return _scorer_instance


if __name__ == "__main__":
    scorer = get_fuzzy_scorer()

    print("\n--- FuzzyScorer Test Cases ---")

    # Rockstar candidate
    r1 = scorer.calculate_score(tech=93, growth=80, culture=85, execution=90, consistency=88)
    print(f"Rockstar: {r1.fuzzy_final_score} → {r1.deterministic_decision} ({r1.engine_used})")

    # Hustler (average tech, exceptional hustle)
    r2 = scorer.calculate_score(tech=60, growth=96, culture=92, execution=55, consistency=70)
    print(f"Hustler:  {r2.fuzzy_final_score} → {r2.deterministic_decision}")

    # Toxic genius (great tech, terrible culture)
    r3 = scorer.calculate_score(tech=95, growth=70, culture=20, execution=85, consistency=65)
    print(f"Toxic:    {r3.fuzzy_final_score} → {r3.deterministic_decision}")

    # Average candidate
    r4 = scorer.calculate_score(tech=55, growth=55, culture=60, execution=50, consistency=60)
    print(f"Average:  {r4.fuzzy_final_score} → {r4.deterministic_decision}")

    # Weak candidate
    r5 = scorer.calculate_score(tech=30, growth=25, culture=50, execution=30, consistency=40)
    print(f"Weak:     {r5.fuzzy_final_score} → {r5.deterministic_decision}")
