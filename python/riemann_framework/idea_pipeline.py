# Riemann Framework
# Copyright (C) 2026 MILAN NIKOLIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
A small, honest pipeline for vetting speculative RH ideas, integrated onto the
modules this repository already has.

The concept (and the five stages below) come from an external
`rh_idea_framework` prototype. That prototype's value is not any single test:
it is the *structure* -- a candidate idea is a small record, and it is pushed
through a fixed sequence of cheap gates, stopping at the first one it fails.
This module keeps that structure and wires it onto the repository's existing
gates instead of re-implementing them:

    Stage A  well-formedness   -> `affine_reduction.parse_expression`
    Stage B  affine / trivial  -> `affine_reduction.check_affine_reduction`
    Stage C  statistics        -> `statistics.classify_statistics`
    Stage D  arithmetic probe  -> `probe_multiplicative_coupling` (below).
                                  This stage *gates*: the probe computes the
                                  quantity named by the arithmetic clause of a
                                  recorded falsification criterion, so a
                                  mismatch with the Euler factor carrying no
                                  p-dependence falsifies the idea instead of
                                  merely being annotated.
    Stage D2 operator screen   -> `operator_symmetry.screen_operator`
    Stage E  falsifiability    -> enforced at construction: an `Idea` without a
                                  `falsification_criterion` is not admitted.

Nothing here proves or disproves anything. The pipeline only answers, as
rigorously as each gate allows, one question:

    How far does this idea get before it (a) turns out to be a known object in
    disguise, (b) fails a statistical sanity check, or (c) reaches genuinely
    open territory?

A `Verdict` never says an idea is correct, proven, or true -- there is no code
path that can produce such a string.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import mpmath as mp
import numpy as np

from .affine_reduction import ExpressionError, check_affine_reduction, parse_expression
from .operator_symmetry import build_prime_swap_involution, screen_operator
from .statistics import classify_statistics


# Primes and sample points for the Stage D arithmetic probe. The sample points
# sit on / just off the critical line in the region of the low zeta zeros,
# which is where a "dimension-shift" proposal claims to act.
FIRST_PRIMES = (2, 3, 5, 7, 11, 13)
SAMPLE_POINTS = (0.5 + 14j, 0.5 + 21j, 0.3 + 5j)

# A per-prime error spread above this threshold means the map's interaction
# with `p^{-s}` genuinely varies with `p`. The identity map gives a spread of
# ~1e-17; a genuinely p-sensitive map gives O(0.1). The threshold only has to
# separate those two regimes, so 1e-6 is generous.
P_DEPENDENCE_THRESHOLD = 1e-6

# A largest per-prime error at or below this means the map agrees with the Euler
# factor to round-off. The mpmath comparison lands near 1e-17 when it agrees
# exactly, so the gap to the next regime is enormous.
_EULER_COMMUTES_TOLERANCE = 1e-9


class InvalidIdeaError(ValueError):
    """Raised when an idea record is missing required fields."""


@dataclass
class Idea:
    """A structured claim about a candidate map (and, optionally, an operator).

    `expression` is a closed-form map in `s` and `s_conj`, parsed by
    `affine_reduction.parse_expression`. `extra` carries anything else -- in
    particular `extra["operator"] = {"p1": 2, "p2": 3, "n_max": 500}` marks an
    operator-level idea (a prime-exponent swap on ``l^2(N)``) that should be
    routed to Stage D2 instead of the complex-plane gates.
    """

    id: str
    hypothesis: str
    expression: str
    falsification_criterion: str
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Idea":
        required = ("id", "hypothesis", "expression", "falsification_criterion")
        missing = [f for f in required if not data.get(f)]
        if missing:
            raise InvalidIdeaError(
                f"Idea record is missing required field(s): {missing}. "
                "An idea with no falsification criterion cannot be vetted."
            )
        known = {"id", "hypothesis", "expression", "falsification_criterion", "notes"}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            id=data["id"],
            hypothesis=data["hypothesis"],
            expression=data["expression"],
            falsification_criterion=data["falsification_criterion"],
            notes=data.get("notes", ""),
            extra=extra,
        )


@dataclass
class ArithmeticProbeResult:
    """Outcome of the Stage D multiplicative-coupling probe."""

    p_dependent_mismatch: bool
    max_relative_error_by_prime: dict[int, float]
    spread: float
    explanation: str
    #: True when every per-prime error is at round-off, i.e. the map agrees with
    #: the Euler factor. Distinct from a saturated failure, which also has a
    #: near-zero spread but is the opposite situation; see `regime`.
    commutes_with_euler_factor: bool
    #: One of `"commutes"`, `"uniform_failure"`, `"p_dependent"`.
    regime: str


def _build_map(expression: str):
    """Return `w(z) -> complex` for a candidate map, with genuine conjugation.

    `parse_expression` treats `s` and `s_conj` as formal independent variables;
    a complex-plane map is recovered by always passing `s = z` and
    `s_conj = conjugate(z)`.
    """
    evaluate = parse_expression(expression)

    def w(z: complex) -> complex:
        return complex(evaluate(z, z.conjugate()))

    return w


def probe_multiplicative_coupling(
    expression: str,
    primes: tuple[int, ...] = FIRST_PRIMES,
    sample_points: tuple[complex, ...] = SAMPLE_POINTS,
) -> ArithmeticProbeResult:
    """Test whether a candidate map `w` commutes with the Euler-factor map.

    For each prime `p` and sample point `s0`, compare

        w(p^{-s0})      (apply w after forming the Euler factor)

    against

        p^{-w(s0)}      (form the Euler factor after applying w)

    and record the relative error. If the mismatch *varies with p*, the map is
    treating different primes differently -- a necessary (not sufficient)
    precondition for genuine arithmetic content.

    A map that commutes with every `p^{-s}` (e.g. the identity) has zero error
    for every prime, so its spread is ~0. Note that this is a heuristic: a
    map built only from `s`, `conj(s)`, and constants may still show a nonzero
    p-dependent mismatch here (the reflection `1 - conj(s)` does), which is why
    Stage B -- the affine gate -- runs *before* this probe in the pipeline.

    Three regimes are reported in `regime`, and they are not interchangeable:

    - ``"commutes"`` -- every per-prime error is at round-off, so the map agrees
      with the Euler factor everywhere. It carries no arithmetic content.
    - ``"uniform_failure"`` -- the map fails to commute by a similar, near-total
      amount for every prime, so the spread is ~0 *because the error saturates*.
      This is also no p-dependence, but for the opposite reason, and describing
      it as "treats every prime identically" without qualification would suggest
      the map engaged the Euler factor correctly when it does the reverse.
    - ``"p_dependent"`` -- the mismatch genuinely varies with `p`. This is the
      only regime with any prospect of arithmetic content, and it is necessary,
      never sufficient.

    The middle regime is why `spread` is not trusted as a *description* of what
    happened: a diagnostic whose headline signal is a spread across a parameter
    has to be checked for accidental invariance in that parameter, which is the
    lesson of `docs/lessons_learned.md` section 14. That section records the
    same trap in this probe's predecessor, where a `log(p)` factor cancelled out
    of the relative error. This is the second instance.
    """
    w = _build_map(expression)

    max_rel_err_by_prime: dict[int, float] = {}
    for p in primes:
        errs: list[float] = []
        for s0 in sample_points:
            z = complex(s0)
            # mpmath power avoids the OverflowError that Python's complex
            # exponentiation raises for maps whose value at s0 is large; the
            # result is converted back to a Python complex before `w` sees it,
            # since `w` is typed to take a `complex`, not an `mp.mpc`.
            p_minus_z = complex(mp.mpc(p) ** (-mp.mpc(z)))
            lhs = mp.mpc(w(p_minus_z))
            rhs = mp.mpc(p) ** (-mp.mpc(w(z)))
            denom = max(abs(lhs), abs(rhs), mp.mpf(10) ** -30)
            errs.append(float(abs(lhs - rhs) / denom))
        max_rel_err_by_prime[p] = max(errs)

    errors = list(max_rel_err_by_prime.values())
    spread = max(errors) - min(errors)
    worst = max(errors)
    p_dependent_mismatch = spread > P_DEPENDENCE_THRESHOLD
    commutes = worst <= _EULER_COMMUTES_TOLERANCE

    if p_dependent_mismatch:
        regime = "p_dependent"
        explanation = (
            "The map's interaction with p^{-s}-type exponents varies across "
            f"primes (spread {spread:.3e} across {list(primes)}). This is a "
            "necessary precondition for genuine arithmetic content, but only a "
            "heuristic numeric probe -- it does not establish a real connection "
            "to the Euler product."
        )
    elif commutes:
        regime = "commutes"
        explanation = (
            "The map commutes with every tested Euler factor to round-off "
            f"(largest per-prime error {worst:.3e}): w(p^{{-s}}) = p^{{-w(s)}} "
            "for every prime sampled. A map of this kind adds no arithmetic "
            "content -- it agrees with the Euler factor everywhere, so it cannot "
            "distinguish primes because it never needs to. The identity and "
            "complex conjugation behave this way."
        )
    else:
        # The spread statistic is *accidentally invariant* here: when the
        # mismatch saturates near its maximum for every prime, the spread
        # collapses to round-off while the map fails to commute as badly as it
        # can. The verdict is unaffected (no p-dependence is no p-dependence),
        # but the description must not imply agreement.
        regime = "uniform_failure"
        explanation = (
            "The map fails to commute with the Euler factor by close to the "
            f"maximum amount for every prime sampled (largest per-prime error "
            f"{worst:.3e}), so the spread across primes collapses to "
            f"{spread:.3e}. A saturated mismatch is p-independent without being "
            "any kind of agreement: do not read this as the map treating primes "
            "correctly. Either way there is no p-dependence, so the arithmetic "
            "clause of a falsification criterion is not met."
        )

    return ArithmeticProbeResult(
        p_dependent_mismatch=p_dependent_mismatch,
        max_relative_error_by_prime=max_rel_err_by_prime,
        spread=spread,
        explanation=explanation,
        commutes_with_euler_factor=commutes,
        regime=regime,
    )


@dataclass
class Verdict:
    """What the pipeline concluded about one idea.

    `passed` means "not falsified by any gate it was subjected to" -- it is
    deliberately *not* a claim that the idea is correct, proven, or true. An
    idea that reaches `D+` or `D2` has reached open territory. Two stages can
    return `passed=False` on their own merits: stage D, when the arithmetic
    probe finds no p-dependence in the map's mismatch with the Euler factor --
    the arithmetic clause a falsification criterion normally names -- and stage
    D2, when a proposed operator does not commute with the primon Hamiltonian.
    """

    idea_id: str
    stage_reached: str
    passed: bool
    summary: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [
            f"Idea: {self.idea_id}",
            f"Stage reached: {self.stage_reached}",
            f"Status: {'not falsified so far' if self.passed else 'falsified at this stage'}",
            f"Summary: {self.summary}",
        ]
        return "\n".join(lines)


def run_pipeline(
    idea: Idea,
    spectrum: np.ndarray | None = None,
) -> Verdict:
    """Run `idea` through the gates and return an honest verdict.

    `spectrum` is an optional eigenvalue array to test at Stage C. An idea with
    no associated operator/spectrum simply has nothing to test there, and Stage
    C is skipped with a note (not a pass).
    """
    # Operator-level idea: route to Stage D2, skipping the complex-plane gates
    # (which do not apply to an operator realization). This is the fix for the
    # prototype's flaw where a "lift to l^2(N)" idea carrying a placeholder
    # expression was wrongly stopped at Stage B.
    operator_spec = idea.extra.get("operator")
    if isinstance(operator_spec, dict):
        p1 = int(operator_spec.get("p1", 2))
        p2 = int(operator_spec.get("p2", 3))
        n_max = int(operator_spec.get("n_max", 500))
        matrix = build_prime_swap_involution(n_max, p1, p2)
        operator = screen_operator(matrix, n_max)
        passed = bool(operator["commutes"])
        summary = (
            f"Stage D2 (operator-level idea): {operator['explanation']} "
            "Stage E: falsification criterion on record: "
            f"\"{idea.falsification_criterion.strip()}\""
        )
        return Verdict(
            idea_id=idea.id,
            stage_reached="D2",
            passed=passed,
            summary=summary,
            details={"operator": operator, "skipped_complex_plane_gates": True},
        )

    # Stage A: well-formedness (parse).
    try:
        parse_expression(idea.expression)
    except ExpressionError as exc:
        return Verdict(
            idea_id=idea.id,
            stage_reached="A",
            passed=False,
            summary=f"Failed well-formedness check: {exc}",
        )

    # Stage B: affine-reduction gate.
    affine = check_affine_reduction(idea.expression)
    if affine.is_affine:
        return Verdict(
            idea_id=idea.id,
            stage_reached="B",
            passed=False,
            summary=(
                "Reduces to a known affine map (reflection/rotation/scaling) in "
                "(s, conjugate(s)); not a new algebraic object. " + affine.explanation
            ),
            details={"affine": affine},
        )

    # Stage C: statistical plausibility (only when a spectrum was supplied).
    stats: dict[str, Any] | None = None
    if spectrum is not None:
        try:
            stats = classify_statistics(spectrum)
        except ValueError as exc:
            return Verdict(
                idea_id=idea.id,
                stage_reached="C",
                passed=False,
                summary=f"Could not evaluate spectrum: {exc}",
                details={"affine": affine},
            )

    # Stage D: multiplicative-coupling probe. This stage gates. The probe
    # computes exactly the quantity the arithmetic clause of a recorded
    # falsification criterion names -- does the map's mismatch with the Euler
    # factor vary with p -- so an idea whose mismatch carries no p-dependence is
    # falsified here rather than annotated and passed on. It used to be
    # informational, which let a map that fails to commute with every Euler
    # factor reach `passed=True` while its own summary said it did not engage
    # the Euler product at all.
    probe = probe_multiplicative_coupling(idea.expression)
    stage_reached = "D+" if probe.p_dependent_mismatch else "D"

    summary_parts = ["Cleared stage B (not a known affine map)."]
    if stats is not None:
        summary_parts.append(
            f"Stage C: mean gap ratio <r> = {stats['mean_r']:.4f}, "
            f"closest to {str(stats['best_fit']).upper()}."
        )
    else:
        summary_parts.append("Stage C skipped (no spectrum supplied).")
    summary_parts.append(f"Stage D: {probe.explanation}")

    details = {
        "affine": affine,
        "statistics": stats,
        "arithmetic_probe": probe,
    }

    if not probe.p_dependent_mismatch:
        summary_parts.append(
            "Stage D therefore falsifies the idea: with no p-dependence the "
            "arithmetic clause of the criterion is met. Only that clause is "
            "mechanised here; the rest of the criterion is reviewed by hand. "
            f"Recorded criterion: \"{idea.falsification_criterion.strip()}\""
        )
        return Verdict(
            idea_id=idea.id,
            stage_reached=stage_reached,
            passed=False,
            summary=" ".join(summary_parts),
            details=details,
        )

    summary_parts.append(
        "Stage E: falsification criterion on record: "
        f"\"{idea.falsification_criterion.strip()}\""
    )

    return Verdict(
        idea_id=idea.id,
        stage_reached=stage_reached,
        passed=True,
        summary=" ".join(summary_parts),
        details=details,
    )


def load_idea(path: str | Path) -> Idea:
    """Load a single idea record from a JSON file.

    JSON (rather than YAML) is used deliberately: the repository depends only on
    mpmath/numpy/scipy, and `json` is in the standard library.
    """
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InvalidIdeaError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidIdeaError(f"{path} does not contain a JSON object.")
    return Idea.from_dict(data)


def load_all_ideas(directory: str | Path) -> list[Idea]:
    """Load every `*.json` idea record in a directory, in sorted order."""
    directory = Path(directory)
    ideas: list[Idea] = []
    for p in sorted(directory.glob("*.json")):
        ideas.append(load_idea(p))
    return ideas
