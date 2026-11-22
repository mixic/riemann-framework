/-
  Riemann Framework
  Copyright (C) 2026 MILAN NIKOLIC

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
-/
import Mathlib.NumberTheory.Zsqrtd.GaussianInt

/-!
# A split prime defeats a norm-preimage identification of strata

The draft `references/masullo_music_of_the_primes_2026-11-20.pdf`, Section 1.3.2,
identifies the `k`-th divisorial stratum of `GL₁(𝔸_F)` with the pre-image under the
norm map of the `k`-th stratum on `GL₁(𝔸_ℚ)`. Both strata are defined by the
condition "the local component is a unit above each of the first `k` rational
primes". This file records the two facts that make that identification fail at a
split prime:

* the **model**: for an idele supported at the two places above a split prime, the
  valuation of the rational norm is the *sum* of the two local valuations, so the
  pair `(+1, -1)` has unit norm with no unit component;
* the **arithmetic certificate** in `ℤ[i]`: `5 = (2 + i)(2 - i)`, both factors have
  norm `5`, and neither is a unit — so at `p = 5` the two local components really
  can carry opposite valuations.

Nothing here is evidence for or against the Riemann hypothesis. It is a statement
about a stratification, and the last theorem is the statement that is false in the
draft, not the one that is true.
-/

namespace RiemannFramework
namespace IdeleSplit

/-! ## The valuation model -/

/-- The valuation of a local component at one of the two places above a split prime. -/
abbrev LocalValuation := ℤ

/-- An idele supported at two places above a split rational prime `p`.

Only the valuations are kept: a component's valuation is what decides whether it is
a unit, and the norm adds them. -/
structure SplitIdele where
  /-- Valuation of the component at the first place above `p`. -/
  valV1 : LocalValuation
  /-- Valuation of the component at the second place above `p`. -/
  valV2 : LocalValuation

/-- A component is a local unit exactly when its valuation is zero. -/
def IsLocalUnit (n : LocalValuation) : Prop := n = 0

/-- The valuation of the rational norm idele at `p`.

For a split prime the two completions are isomorphic to `ℚ_p`, the local norm maps
are the identity, and the idele norm multiplies the two components; hence the
valuations add. -/
def normValuation (g : SplitIdele) : LocalValuation := g.valV1 + g.valV2

/-- The norm is a unit at `p` exactly when its valuation vanishes. -/
def IsNormUnit (g : SplitIdele) : Prop := normValuation g = 0

/-- The idele with one uniformiser at the first place and its inverse at the second. -/
def cancellationIdele : SplitIdele := ⟨1, -1⟩

theorem cancellation_norm_is_unit : IsNormUnit cancellationIdele := by
  simp [IsNormUnit, normValuation, cancellationIdele]

theorem cancellation_components_are_not_units :
    ¬ IsLocalUnit cancellationIdele.valV1 ∧ ¬ IsLocalUnit cancellationIdele.valV2 := by
  constructor <;> simp [IsLocalUnit, cancellationIdele]

/-- **The identification fails already in the model.** A unit norm at a split prime
does not force the local components above it to be units, so the norm pre-image of a
stratum strictly contains the stratum. -/
theorem norm_unit_does_not_force_local_units :
    ∃ g : SplitIdele, IsNormUnit g ∧ ¬ IsLocalUnit g.valV1 ∧ ¬ IsLocalUnit g.valV2 :=
  ⟨cancellationIdele, cancellation_norm_is_unit, cancellation_components_are_not_units⟩

/-- The same statement, in the form that contradicts the draft: there is an idele
whose norm is a unit at `p` and whose components are both outside the unit group. -/
theorem preimage_strictly_contains_stratum :
    ∃ g : SplitIdele, IsNormUnit g ∧ ¬ (IsLocalUnit g.valV1 ∧ IsLocalUnit g.valV2) := by
  obtain ⟨g, hg, h1, h2⟩ := norm_unit_does_not_force_local_units
  exact ⟨g, hg, fun h => h1 h.1⟩

/-! ## The arithmetic certificate at `p = 5` -/

/-- `2 + i` as a Gaussian integer. -/
def pi1 : GaussianInt := ⟨2, 1⟩

/-- `2 - i` as a Gaussian integer. -/
def pi2 : GaussianInt := ⟨2, -1⟩

/-- The splitting of `5` in `ℤ[i]`. -/
theorem pi1_mul_pi2 : pi1 * pi2 = 5 := by
  decide

theorem norm_pi1 : Zsqrtd.norm pi1 = 5 := by
  simp [pi1, Zsqrtd.norm_def]

theorem norm_pi2 : Zsqrtd.norm pi2 = 5 := by
  simp [pi2, Zsqrtd.norm_def]

/-- `2 + i` is not a unit: its norm is `5`, and a unit in `ℤ[i]` has norm `±1`. -/
theorem pi1_not_unit : ¬ IsUnit pi1 := by
  intro h
  have hnorm : IsUnit (5 : ℤ) := (Zsqrtd.isUnit_iff_norm_isUnit pi1).mp h
  rw [Int.isUnit_iff_natAbs_eq] at hnorm
  norm_num at hnorm

/-- `2 - i` is not a unit, for the same reason. -/
theorem pi2_not_unit : ¬ IsUnit pi2 := by
  intro h
  have hnorm : IsUnit (5 : ℤ) := (Zsqrtd.isUnit_iff_norm_isUnit pi2).mp h
  rw [Int.isUnit_iff_natAbs_eq] at hnorm
  norm_num at hnorm

/-- **The certificate.** `5` splits in `ℤ[i]` into two non-units of norm `5`, so the
idele with one factor at each place has opposite local valuations and unit norm. -/
theorem split_prime_certificate :
    pi1 * pi2 = 5 ∧ Zsqrtd.norm pi1 = 5 ∧ Zsqrtd.norm pi2 = 5 ∧
      ¬ IsUnit pi1 ∧ ¬ IsUnit pi2 ∧ (1 : ℤ) + (-1 : ℤ) = 0 :=
  ⟨pi1_mul_pi2, norm_pi1, norm_pi2, pi1_not_unit, pi2_not_unit, by norm_num⟩

#print axioms norm_unit_does_not_force_local_units
#print axioms split_prime_certificate

end IdeleSplit
end RiemannFramework
