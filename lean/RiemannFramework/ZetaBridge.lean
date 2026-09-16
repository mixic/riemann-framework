-- Riemann Framework
-- Copyright (C) 2026 MILAN NIKOLIC
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.

import Mathlib.NumberTheory.LSeries.RiemannZeta
import Mathlib.NumberTheory.LSeries.Nonvanishing
import Mathlib.NumberTheory.Harmonic.ZetaAsymp

open Complex
open scoped ComplexConjugate

namespace RiemannFramework

/-!
# Bridging the involution `σ` to Mathlib's functional equation

This module owns the reflection in the critical line, `σ(s) = 1 - conj s`, and everything the
functional equation has to say about it. `ZetaConjecture.lean` imports this file and states the
Riemann Hypothesis in terms of `σ`; nothing here depends on that file, so there is no cycle.

`σ` is the composition of the functional equation's reflection `s ↦ 1 - s` with complex
conjugation `s ↦ conj s`. That is the whole reason the involution is interesting, and the whole
reason it is not enough. What is machine-checked here:

* **The two zero symmetries Mathlib supplies.** `Λ(1 - s) = Λ(s)` and `ζ(conj s) = conj (ζ s)`.

* **`σ`-invariance of the zero set** (Section 3): composing them gives `ζ s = 0 → ζ (σ s) = 0`.
  This is real content, derived rather than assumed. It also yields the classical quadruple
  symmetry `{ρ, 1 - ρ, conj ρ, 1 - conj ρ}` with no outstanding cases.

* **The reformulation of the wall** (Section 4). `σ` is an involution whose fixed points are
  exactly the critical line, so `σ`-invariance partitions the zeros into orbits of size 1 or 2.
  Since `σ` preserves the imaginary part while reflecting the real part about `1/2`, a size-2
  orbit is a *pair of distinct zeros at the same height whose real parts sum to `1`*. Hence the
  open condition "every nontrivial zero is fixed by `σ`" is precisely "there are no `σ`-twin
  nontrivial zeros" — still equivalent to RH.

* **The verdict** (Section 5). Because invariance is a theorem, the implication
  "invariance ⟹ fixedness" is *itself equivalent to the Riemann Hypothesis*. The functional
  equation supplies the symmetry but cannot supply the absence of 2-cycles.

Nothing here proves the Riemann Hypothesis. Every declaration in this file is `sorry`- and
`axiom`-free; the single open obligation lives in `ZetaConjecture.lean` as
`zeros_are_fixed_by_sigma`.

## Three traps in this part of Mathlib

* **Do not use unrestricted `simp` on goals containing `conj`.** In this version of Mathlib
  `starRingEnd_apply` (`starRingEnd R x = star x`) and `star_def` (`(Star.star : ℂ → ℂ) = conj`)
  are both simp lemmas and rewrite into each other, so `simp`/`simpa` diverge. The proofs below
  use `simp only` with an explicit lemma list, or plain `rw` steps.

* **`riemannZeta_conj` lives in `Mathlib.NumberTheory.Harmonic.ZetaAsymp`**, not in the
  `RiemannZeta` module, so that import is required.

* **`conj` is notation in the `ComplexConjugate` scope**, so `open scoped ComplexConjugate` is
  required; `open Complex` alone does not bring it in.

## No prefactor side condition

An earlier draft of this file required the functional-equation prefactor
`2 * (2π)^{-s} * Γ(s) * cos(π s / 2)` to be non-zero. It is not needed. Mathlib's
`riemannZeta_one_sub` states

    ζ(1 - s) = 2 * (2 * π) ^ (-s) * Gamma s * cos (π * s / 2) * ζ(s),

so `ζ s = 0` gives `ζ (1 - s) = 0` outright: the left-hand side is *proportional* to `ζ s`.
Nonvanishing of the prefactor would be needed only for the converse
`ζ (1 - s) = 0 → ζ s = 0`, which `σ`-invariance never uses. Hence no `Γ`-nonvanishing lemma and
no `cos ≠ 0` lemma appear anywhere below.
-/

/-!
## 1. The involution `σ` and its fixed points
-/

/-- The reflection in the critical line, `σ(s) = 1 - conj s`. It is the composite of the
functional equation's `s ↦ 1 - s` with complex conjugation. -/
def sigma (s : ℂ) : ℂ := 1 - conj s

/-- `σ` reflects the real part about `1/2`. -/
theorem sigma_re (s : ℂ) : (sigma s).re = 1 - s.re := by
  have h : sigma s = 1 - conj s := rfl
  rw [h, Complex.sub_re, Complex.one_re, Complex.conj_re]

/-- `σ` preserves the imaginary part: a `σ`-partner sits at the *same height*. -/
theorem sigma_im (s : ℂ) : (sigma s).im = s.im := by
  have h : sigma s = 1 - conj s := rfl
  rw [h, Complex.sub_im, Complex.one_im, Complex.conj_im]
  ring

/-- `σ` is an involution. Proved componentwise, which sidesteps the `conj`/`star` simp cycle. -/
theorem sigma_involutive : Function.Involutive sigma := by
  intro s
  apply Complex.ext
  · rw [sigma_re, sigma_re]
    ring
  · rw [sigma_im, sigma_im]

/-- If `Re(s) = 1/2` then `σ` fixes `s`. -/
theorem fixed_point_of_re_eq_half {s : ℂ} (h : s.re = 1 / 2) : sigma s = s := by
  apply Complex.ext
  · rw [sigma_re, h]
    norm_num
  · rw [sigma_im]

/-- If `σ` fixes `s` then `Re(s) = 1/2`. -/
theorem re_of_fixed_point_eq_half {s : ℂ} (h : sigma s = s) : s.re = 1 / 2 := by
  have h_re : (1 : ℝ) - s.re = s.re := by
    rw [← sigma_re s, h]
  linarith

/-- **The core algebraic result:** the fixed locus of `σ` is exactly the critical line. -/
theorem sigma_fixed_iff_re_eq_half (s : ℂ) : sigma s = s ↔ s.re = 1 / 2 :=
  ⟨re_of_fixed_point_eq_half, fixed_point_of_re_eq_half⟩

/-- The open critical strip `0 < re s < 1`.

The strip is where the hypotheses of Mathlib's functional equation hold automatically and where
`σ` acts, so it is the natural home for the verdict in Section 5. (`Millennium.CriticalStrip` in
`RiemannHypothesis_optimized.lean` is the same region, but that file belongs to the Clay
formalization; the framework's own files do not depend on it.) -/
def InCriticalStrip (s : ℂ) : Prop :=
  0 < s.re ∧ s.re < 1

/-- `σ` preserves the critical strip. -/
theorem sigma_inCriticalStrip_iff (s : ℂ) :
    InCriticalStrip (sigma s) ↔ InCriticalStrip s := by
  unfold InCriticalStrip
  rw [sigma_re]
  constructor <;> intro ⟨h1, h2⟩ <;> constructor <;> linarith

/-!
## 2. The zero symmetries available from Mathlib
-/

/-- The functional equation `Λ(1 - s) = Λ(s)`, read as a statement about the zeros of the
completed zeta function. -/
theorem completedRiemannZeta_zero_iff_one_sub (s : ℂ) :
    completedRiemannZeta s = 0 ↔ completedRiemannZeta (1 - s) = 0 := by
  rw [completedRiemannZeta_one_sub]

/-- Conjugation symmetry of the zeros, from Mathlib's `riemannZeta_conj`. -/
theorem riemannZeta_zero_conj {s : ℂ} (hs : riemannZeta s = 0) :
    riemannZeta (conj s) = 0 := by
  rw [riemannZeta_conj, hs, map_zero]

/-- The functional equation `ζ(1 - s) = 2 * (2π)^{-s} * Γ(s) * cos(π s / 2) * ζ(s)`, read as a
statement about the zeros. No prefactor nonvanishing is required — see the module docstring. -/
theorem riemannZeta_zero_one_sub {s : ℂ} (hnonpos : ∀ n : ℕ, s ≠ -n) (hs1 : s ≠ 1)
    (h : riemannZeta s = 0) : riemannZeta (1 - s) = 0 := by
  rw [riemannZeta_one_sub hnonpos hs1, h, mul_zero]

/-- A point with `0 < re s < 1` satisfies the side conditions of Mathlib's functional equation:
it is neither `1` nor a non-positive integer. -/
theorem ne_neg_nat_and_ne_one {s : ℂ} (h1 : 0 < s.re) (h2 : s.re < 1) :
    (∀ n : ℕ, s ≠ -n) ∧ s ≠ 1 := by
  constructor
  · intro n hn
    have hre : s.re = -(n : ℝ) := by rw [hn]; simp
    have hn_nonneg : (0 : ℝ) ≤ (n : ℝ) := Nat.cast_nonneg n
    linarith
  · intro h
    rw [h] at h2
    norm_num at h2

/-!
## 3. `σ`-invariance of the zero set, from the functional equation
-/

/-- **The zero set is `σ`-invariant.** Composing conjugation symmetry with the functional
equation: `ζ s = 0` gives `ζ (conj s) = 0`, and the functional equation at `conj s` gives
`ζ (1 - conj s) = 0`, which is `ζ (σ s) = 0`.

The side conditions of `riemannZeta_one_sub` are supplied in the form `0 < re s < 1`, which is
stable under `conj` (via `Complex.conj_re`), so no conjugation juggling of hypotheses is needed. -/
theorem riemannZeta_zero_sigma {s : ℂ} (hre : 0 < s.re) (hre_lt : s.re < 1)
    (h : riemannZeta s = 0) : riemannZeta (sigma s) = 0 := by
  have hre_conj : (0 : ℝ) < (conj s).re := by rw [Complex.conj_re]; exact hre
  have hre_conj_lt : (conj s).re < 1 := by rw [Complex.conj_re]; exact hre_lt
  obtain ⟨hnonpos, hs1⟩ := ne_neg_nat_and_ne_one hre hre_lt
  obtain ⟨hnonpos', hs1'⟩ := ne_neg_nat_and_ne_one hre_conj hre_conj_lt
  have hfe : riemannZeta (1 - conj s) = 0 :=
    riemannZeta_zero_one_sub hnonpos' hs1' (riemannZeta_zero_conj h)
  show riemannZeta (1 - conj s) = 0
  exact hfe

/-- **The classical quadruple symmetry.** A zero in the critical strip comes with `1 - ρ`,
`conj ρ` and `1 - conj ρ`. All four branches are closed: the conjugates by conjugation
symmetry, `1 - ρ` by the functional equation, and `1 - conj ρ` by their composite, `σ`. -/
theorem riemannZeta_zero_quadruple {ρ : ℂ} (hre : 0 < ρ.re) (hre_lt : ρ.re < 1)
    (hρ : riemannZeta ρ = 0) :
    riemannZeta ρ = 0 ∧ riemannZeta (1 - ρ) = 0 ∧
      riemannZeta (conj ρ) = 0 ∧ riemannZeta (1 - conj ρ) = 0 := by
  have hconj : riemannZeta (conj ρ) = 0 := riemannZeta_zero_conj hρ
  have hone_sub : riemannZeta (1 - ρ) = 0 := by
    obtain ⟨hnonpos, hs1⟩ := ne_neg_nat_and_ne_one hre hre_lt
    exact riemannZeta_zero_one_sub hnonpos hs1 hρ
  have hsigma : riemannZeta (1 - conj ρ) = 0 := riemannZeta_zero_sigma hre hre_lt hρ
  exact ⟨hρ, hone_sub, hconj, hsigma⟩

/-!
## 4. Reformulating the wall as the absence of 2-cycles
-/

/-- **Reformulation of the RH via `σ`.** The fixed-point form and the real-part form of the wall
are the same condition. This is the `σ`-reformulation; it is not yet RH itself, because it omits
the side condition `s ≠ 1` that Mathlib's `RiemannHypothesis` carries. -/
theorem rh_iff_zeros_fixed_by_sigma :
    (∀ s : ℂ, riemannZeta s = 0 → ¬ (∃ n : ℕ, s = -2 * (n + 1)) → sigma s = s)
      ↔ (∀ s : ℂ, riemannZeta s = 0 → ¬ (∃ n : ℕ, s = -2 * (n + 1)) → s.re = 1 / 2) := by
  constructor
  · intro h s hs htriv
    exact re_of_fixed_point_eq_half (h s hs htriv)
  · intro h s hs htriv
    exact fixed_point_of_re_eq_half (h s hs htriv)

/-- A `σ`-partner sits at the same height, with the real part reflected about `1/2`. -/
theorem sigma_partner_same_height (s : ℂ) :
    (sigma s).im = s.im ∧ (sigma s).re + s.re = 1 :=
  ⟨sigma_im s, by rw [sigma_re]; ring⟩

/-- **The reformulation.** The reflection of a nontrivial zero is never a *different* zero
exactly when every nontrivial zero is fixed. -/
theorem fixed_on_zeros_iff_no_distinct_reflection :
    (∀ s : ℂ, riemannZeta s = 0 → ¬ (∃ n : ℕ, s = -2 * (n + 1)) → s ≠ 1 → sigma s = s)
      ↔ (∀ s t : ℂ, riemannZeta s = 0 → ¬ (∃ n : ℕ, s = -2 * (n + 1)) → s ≠ 1 →
            t = sigma s → t = s) := by
  constructor
  · intro h s t hz htriv hs1 ht
    rw [ht, h s hz htriv hs1]
  · intro h s hz htriv hs1
    exact h s (sigma s) hz htriv hs1 rfl

/-- **The wall is equivalent to the absence of `σ`-twin nontrivial zeros**, hence to the
Riemann Hypothesis. Since `ζ s = 0` already forces `ζ (σ s) = 0`, the entire remaining content
is that the reflected zero is never a *new* one. -/
theorem riemannHypothesis_iff_no_two_cycle :
    RiemannHypothesis ↔
      ¬ ∃ s : ℂ, riemannZeta s = 0 ∧ ¬ (∃ n : ℕ, s = -2 * (n + 1)) ∧ s ≠ 1 ∧
        sigma s ≠ s := by
  constructor
  · rintro h ⟨s, hz, htriv, hs1, hne⟩
    exact hne (fixed_point_of_re_eq_half (h s hz htriv hs1))
  · intro h s hz htriv hs1
    by_contra hre
    exact h ⟨s, hz, htriv, hs1, fun hfix ↦ hre (re_of_fixed_point_eq_half hfix)⟩

/-!
## 5. The verdict: the functional equation cannot discharge the wall

Stating the verdict needs a name for the region where the functional equation applies and `σ`
acts. Restricting to the strip avoids smuggling in the (unproved here) theorem that nontrivial
zeros lie in the critical strip.
-/

/-- `σ`-invariance of the zero set, restricted to the critical strip. -/
def StripSigmaInvariant : Prop :=
  ∀ s : ℂ, InCriticalStrip s → riemannZeta s = 0 → riemannZeta (sigma s) = 0

/-- What the wall demands, restricted to the critical strip. -/
def StripFixedOnZeros : Prop :=
  ∀ s : ℂ, InCriticalStrip s → riemannZeta s = 0 → sigma s = s

/-- The Riemann Hypothesis restricted to zeros inside the critical strip. -/
def RiemannHypothesisOnStrip : Prop :=
  ∀ s : ℂ, InCriticalStrip s → riemannZeta s = 0 → s.re = 1 / 2

/-- On the strip the functional-equation hypotheses are free (Section 3). -/
theorem stripSigmaInvariant : StripSigmaInvariant := by
  unfold StripSigmaInvariant InCriticalStrip
  intro s hs h
  exact riemannZeta_zero_sigma hs.1 hs.2 h

/-- On the strip, fixedness of the zeros is exactly the strip-restricted Riemann Hypothesis,
via `sigma_fixed_iff_re_eq_half`. -/
theorem stripFixedOnZeros_iff_riemannHypothesisOnStrip :
    StripFixedOnZeros ↔ RiemannHypothesisOnStrip := by
  unfold StripFixedOnZeros RiemannHypothesisOnStrip InCriticalStrip
  constructor
  · intro h s hs hz
    exact (sigma_fixed_iff_re_eq_half s).mp (h s hs hz)
  · intro h s hs hz
    exact (sigma_fixed_iff_re_eq_half s).mpr (h s hs hz)

/-- A zero inside the critical strip is automatically nontrivial: the trivial zeros sit at
`-2, -4, -6, …`, all with negative real part. So the standard Riemann Hypothesis implies its
strip-restricted form, and the reformulation is not a weakening of the target. -/
theorem riemannHypothesis_imp_on_strip (h : RiemannHypothesis) : RiemannHypothesisOnStrip := by
  unfold RiemannHypothesisOnStrip InCriticalStrip
  intro s hs hz
  obtain ⟨hre_pos, hre_lt⟩ := hs
  refine h s hz ?_ ?_
  · rintro ⟨n, hn⟩
    have hre : s.re = -2 * ((n : ℝ) + 1) := by rw [hn]; simp
    have hn_nonneg : (0 : ℝ) ≤ (n : ℝ) := Nat.cast_nonneg n
    linarith
  · intro h1
    rw [h1] at hre_lt
    norm_num at hre_lt

/-- **The verdict.** Since `σ`-invariance of the zero set is a theorem (`stripSigmaInvariant`),
the implication "invariance ⟹ fixedness" is *equivalent* to the Riemann Hypothesis.

This is deliberately not new mathematical content: it is the machine-checked statement that the
functional equation, having been fully used, contributes nothing towards discharging the wall.
What the functional equation buys is the symmetry `ζ s = 0 → ζ (σ s) = 0`; what the wall needs
is that the reflected zero coincide with `s`. The difference between the two is precisely the
existence of `σ`-twin zeros, which is the open problem. -/
theorem strip_invariance_imp_fixedness_iff_riemannHypothesisOnStrip :
    (StripSigmaInvariant → StripFixedOnZeros) ↔ RiemannHypothesisOnStrip := by
  rw [stripFixedOnZeros_iff_riemannHypothesisOnStrip]
  exact ⟨fun h ↦ h stripSigmaInvariant, fun h _ ↦ h⟩

end RiemannFramework
