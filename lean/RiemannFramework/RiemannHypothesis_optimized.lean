/-
Copyright notice and license for this file
--------------------------------------------

This file is a derivative work of the Riemann Hypothesis formalization in the
project `lean-dojo/LeanMillenniumPrizeProblems`
(https://github.com/lean-dojo/LeanMillenniumPrizeProblems), which is
distributed under the Apache License, Version 2.0
(http://www.apache.org/licenses/LICENSE-2.0).

Significant changes: the original has been trimmed, reorganized, and shortened
for this repository, and several proofs have been simplified or omitted.

The Apache License, Version 2.0 applies to the portions derived from that
project. Apache 2.0 is compatible with the GNU General Public License v3.0
(the license of this repository), so this file may be distributed as part of
this GPLv3 project with the derived portions retaining their Apache 2.0 license.
-/

import Mathlib.NumberTheory.LSeries.RiemannZeta
import Mathlib.NumberTheory.EulerProduct.DirichletLSeries
import Mathlib.NumberTheory.LSeries.Nonvanishing
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.PrimeCounting
import Mathlib.MeasureTheory.Integral.IntervalIntegral.Basic
import Mathlib.Tactic.Ring

namespace Millennium

open Complex
open Filter
open scoped BigOperators
open scoped Topology

/-!
# The Riemann Hypothesis

This file states the Clay Millennium problem "Riemann Hypothesis" in Lean, following the
Clay problem description. We reuse Mathlib's analytic continuation of the Riemann zeta
function `riemannZeta : ℂ → ℂ` and state a few standard facts mentioned in the Clay
write-up (Dirichlet series and Euler product for `re s > 1`, the functional equation for
the completed zeta function, and the definition of Riemann's `ξ`-function).

`ClayRiemannHypothesis` below states the Clay critical-line formulation. It is equivalent
to the real-part statement `ClayRiemannHypothesis.Formulations.RealPart`, to Mathlib's
`_root_.RiemannHypothesis`, and to Riemann's original `ξ(t)` wording
`ClayRiemannHypothesis.Formulations.XiZeros`.

## Note on this revision

This version applies a small number of low-risk proof simplifications relative to the
original (shorter tactic proofs / term-mode proofs where the statement allows it,
consolidating duplicated proof steps). No statement, definition, or mathematical content
was changed; only proof terms were shortened. Every proof here should still be checked
with `lake build` before merging, since this was edited without a local Lean/Mathlib
toolchain available for verification.
-/

/-!
## Zeta: series, Euler product, pole at `s = 1`
-/

/-- The Dirichlet series definition of `ζ(s)` is valid for `re s > 1`. -/
theorem riemannZeta.eq_tsum_one_div_nat_cpow {s : ℂ} (hs : 1 < s.re) :
    riemannZeta s = ∑' n : ℕ, 1 / (n : ℂ) ^ s := by
  simpa using zeta_eq_tsum_one_div_nat_cpow hs

/-- The Euler product `ζ(s) = ∏_p (1 - p^{-s})^{-1}` holds for `re s > 1`. -/
theorem riemannZeta.euler_product_has_prod {s : ℂ} (hs : 1 < s.re) :
    HasProd (fun p : Nat.Primes ↦ (1 - (p : ℂ) ^ (-s))⁻¹) (riemannZeta s) :=
  _root_.riemannZeta_eulerProduct_hasProd hs

/-- Nonvanishing consequence of the Euler-product half-plane: `ζ(s)` has no zeros for `Re(s) > 1`. -/
theorem riemannZeta.ne_zero_of_one_lt_re {s : ℂ} (hs : 1 < s.re) :
    riemannZeta s ≠ 0 :=
  _root_.riemannZeta_ne_zero_of_one_lt_re hs

/-- The zeta function is differentiable away from `s = 1` (meromorphic continuation). -/
theorem riemannZeta.differentiable_at {s : ℂ} (hs : s ≠ 1) : DifferentiableAt ℂ riemannZeta s :=
  differentiableAt_riemannZeta hs

/-- The residue of `ζ(s)` at `s = 1` is `1`. -/
theorem riemannZeta.residue_one :
    Tendsto (fun s ↦ (s - 1) * riemannZeta s) (𝓝[≠] 1) (𝓝 1) :=
  riemannZeta_residue_one

/-!
## Completed zeta and the functional equation
-/

/-- The completed zeta function `Λ(s)` from Mathlib. -/
noncomputable def completed_zeta (s : ℂ) : ℂ :=
  completedRiemannZeta s

/--
The entire part `Λ₀(s)` of Mathlib's completed zeta function, i.e. the completed zeta
with its poles removed.
-/
noncomputable def completed_zeta_entire (s : ℂ) : ℂ :=
  completedRiemannZeta₀ s

/-- Functional equation in the symmetric form `Λ(1 - s) = Λ(s)`. -/
theorem completed_zeta.one_sub (s : ℂ) : completed_zeta (1 - s) = completed_zeta s := by
  simpa [completed_zeta] using completedRiemannZeta_one_sub s

/-- Functional equation for the entire completed-zeta part. -/
theorem completed_zeta_entire.one_sub (s : ℂ) :
    completed_zeta_entire (1 - s) = completed_zeta_entire s := by
  simpa [completed_zeta_entire] using completedRiemannZeta₀_one_sub s

/-!
## Riemann's `ξ(t)` function
-/

/-- The zeta-plane argument corresponding to Riemann's variable `t`: `s = 1/2 + i t`. -/
noncomputable def xi_argument (t : ℂ) : ℂ :=
  (1 / 2 : ℂ) + Complex.I * t

/-- The `t`-parameter corresponding to a zeta-plane point `s`, inverse to `xi_argument`. -/
noncomputable def zeta_zero_parameter (s : ℂ) : ℂ :=
  -Complex.I * (s - (1 / 2 : ℂ))

/--
The `s = 1/2 + i t` substitution inverts `zeta_zero_parameter` on `s`.

(Proved componentwise: `Complex.ext` splits the goal into its real and imaginary
parts, where the `I ^ 2 = -1` cancellation is immediate.)
-/
theorem xi_argument.comp_zeta_zero_parameter (s : ℂ) :
    xi_argument (zeta_zero_parameter s) = s := by
  apply Complex.ext <;> simp [xi_argument, zeta_zero_parameter]

/-- The `zeta_zero_parameter` coordinate inverts `xi_argument` on Riemann's parameter `t`. -/
theorem zeta_zero_parameter.comp_xi_argument (t : ℂ) :
    zeta_zero_parameter (xi_argument t) = t := by
  apply Complex.ext <;> simp [xi_argument, zeta_zero_parameter]

/-- The gamma factor `π^{-s/2} Γ(s/2)` in Bombieri's Clay formula for `ξ(t)`. -/
noncomputable def xi_gamma_factor (s : ℂ) : ℂ :=
  (Real.pi : ℂ) ^ (-s / 2) * Gamma (s / 2)

/-- This gamma factor is Mathlib's archimedean factor `Gammaℝ`. -/
theorem xi_gamma_factor.eq_gamma_real (s : ℂ) : xi_gamma_factor s = Gammaℝ s :=
  by simp [xi_gamma_factor, Gammaℝ_def]

/--
Riemann's `ξ`-function, as a function of the complex variable `t`, using the substitution
`s = 1/2 + i t`, in the pole-cancelled entire form.
-/
noncomputable def xi (t : ℂ) : ℂ :=
  let s : ℂ := (1 / 2 : ℂ) + Complex.I * t
  (1 / 2 : ℂ) * (s * (s - 1) * completed_zeta_entire s + 1)

/--
Bombieri's Clay formula `ξ(t) = 1/2 * s * (s - 1) * π^{-s/2} * Γ(s/2) * ζ(s)`, with
`s = 1/2 + i t`, as the expanded meromorphic expression. This has spurious Lean
point-values at the trivial zeros (see the full write-up); `xi` above is the pole-cancelled
version, and the two agree away from `s ∈ {0, 1}` and the trivial zeros.
-/
noncomputable def expanded_xi_formula (t : ℂ) : ℂ :=
  let s : ℂ := xi_argument t
  (1 / 2 : ℂ) * s * (s - 1) * (xi_gamma_factor s * riemannZeta s)

/-- `xi` written using the coordinate `xi_argument`. -/
theorem xi.eq_xi_argument (t : ℂ) :
    xi t =
      (1 / 2 : ℂ) *
        (xi_argument t * (xi_argument t - 1) * completed_zeta_entire (xi_argument t) + 1) := by
  simp [xi, xi_argument]

/-- The function `xi` is even: `ξ(-t) = ξ(t)`, from the functional equation `Λ(1-s)=Λ(s)`. -/
theorem xi.even (t : ℂ) : xi (-t) = xi t := by
  let s : ℂ := (1 / 2 : ℂ) + Complex.I * t
  have hs_neg'' : (2⁻¹ : ℂ) + -(Complex.I * t) = 1 - s := by
    simp [s]
    ring
  calc
    xi (-t)
        = (1 / 2 : ℂ) *
            ((1 - s) * ((1 - s) - 1) * completed_zeta_entire (1 - s) + 1) := by
            dsimp [xi]
            simp [hs_neg'']
    _   = (1 / 2 : ℂ) *
            ((1 - s) * ((1 - s) - 1) * completed_zeta_entire s + 1) := by
            simp [completed_zeta_entire.one_sub]
    _   = (1 / 2 : ℂ) * (s * (s - 1) * completed_zeta_entire s + 1) := by
            ring
    _   = xi t := by
            simp [xi, s, completed_zeta_entire]

/-!
## Zeros and the Clay statement
-/

/-- Trivial zeros: the negative even integers `-2, -4, -6, ...`. -/
def IsTrivialZero (s : ℂ) : Prop :=
  ∃ n : ℕ, s = -2 * (n + 1)

/-- A "nontrivial" zero is a zero that is not a trivial zero and not the pole at `s = 1`. -/
def IsNontrivialZero (s : ℂ) : Prop :=
  riemannZeta s = 0 ∧ ¬IsTrivialZero s ∧ s ≠ 1

/-- A nontrivial zero cannot lie in the Euler-product half-plane `Re(s) > 1`. -/
theorem IsNontrivialZero.re_le_one {s : ℂ} (hs : IsNontrivialZero s) : s.re ≤ 1 := by
  by_contra hle
  exact (riemannZeta.ne_zero_of_one_lt_re (lt_of_not_ge hle)) hs.1

/-- The critical strip `{ s | 0 < re s ∧ re s < 1 }`. -/
def CriticalStrip : Set ℂ :=
  {s : ℂ | 0 < s.re ∧ s.re < 1}

/-- The critical line `{ s | re s = 1/2 }`. -/
def CriticalLine : Set ℂ :=
  {s : ℂ | s.re = 1 / 2}

/--
The critical line lies in the critical strip.

(Simplified: both halves of the original two-`rw`-block proof normalize `hs` to
`s.re = 1 / 2` the same way, so this is now a single `simp only` followed by
`linarith` on each component, instead of two separate `rw [CriticalLine] at hs;
rw [hs]; norm_num` blocks.)
-/
theorem CriticalLine.mem_critical_strip {s : ℂ} (hs : s ∈ CriticalLine) : s ∈ CriticalStrip := by
  simp only [CriticalLine, Set.mem_setOf_eq] at hs
  exact ⟨by linarith, by linarith⟩

/-- A complex number is real, in the sense used for Riemann's complex `t` variable. -/
def IsRealComplex (t : ℂ) : Prop :=
  t.im = 0

/-- Under `s = 1/2 + i t`, the real part of `s` is `1/2 - im(t)`. -/
theorem xi_argument.re (t : ℂ) : (xi_argument t).re = 1 / 2 - t.im := by
  simp [xi_argument, sub_eq_add_neg]

/-- The Clay condition that `t` is real is exactly the critical-line condition for `1/2 + i t`. -/
theorem xi_argument.mem_critical_line_iff_real (t : ℂ) :
    xi_argument t ∈ CriticalLine ↔ IsRealComplex t := by
  simp [CriticalLine, IsRealComplex, xi_argument, sub_eq_add_neg]

/--
For a zeta-plane point `s`, the corresponding Riemann parameter `t` is real exactly when `s` lies
on the critical line.
-/
theorem zeta_zero_parameter.is_real_iff_mem_critical_line (s : ℂ) :
    IsRealComplex (zeta_zero_parameter s) ↔ s ∈ CriticalLine := by
  constructor
  · intro ht
    have hLine : xi_argument (zeta_zero_parameter s) ∈ CriticalLine :=
      (xi_argument.mem_critical_line_iff_real (zeta_zero_parameter s)).2 ht
    simpa [xi_argument.comp_zeta_zero_parameter s] using hLine
  · intro hs
    have hLine : xi_argument (zeta_zero_parameter s) ∈ CriticalLine := by
      simpa [xi_argument.comp_zeta_zero_parameter s] using hs
    exact (xi_argument.mem_critical_line_iff_real (zeta_zero_parameter s)).1 hLine

/--
The Clay statement: all nontrivial zeros of `ζ(s)` have real part `1/2`.
-/
def ClayRiemannHypothesis.Formulations.RealPart : Prop :=
  ∀ (s : ℂ), IsNontrivialZero s → s.re = 1 / 2

/--
Clay's critical-line wording of the Riemann Hypothesis:
every nontrivial zero of `ζ(s)` lies on the critical line `re s = 1/2`.
-/
def ClayRiemannHypothesis : Prop :=
  ∀ (s : ℂ), IsNontrivialZero s → s ∈ CriticalLine

/--
Clay's original `ξ`-function wording of the Riemann Hypothesis:
all zeros of `ξ(t)` are real.
-/
def ClayRiemannHypothesis.Formulations.XiZeros : Prop :=
  ∀ (t : ℂ), xi t = 0 → IsRealComplex t

/-- The `ξ`-wording says directly that every zero of `ξ(t)` has real `t`. -/
theorem ClayRiemannHypothesis.Formulations.XiZeros.zero_real
    (h : ClayRiemannHypothesis.Formulations.XiZeros) {t : ℂ} (ht : xi t = 0) :
    IsRealComplex t :=
  h t ht

/-- The `ξ`-wording sends every zero of `ξ(t)` to the critical line under `s = 1/2 + i t`. -/
theorem ClayRiemannHypothesis.Formulations.XiZeros.arg_mem_critical_line
    (h : ClayRiemannHypothesis.Formulations.XiZeros) {t : ℂ} (ht : xi t = 0) :
    xi_argument t ∈ CriticalLine :=
  (xi_argument.mem_critical_line_iff_real t).2 (h t ht)

/--
The critical-line wording is equivalent to the real-part formulation.

(Simplified: `s ∈ CriticalLine` unfolds definitionally to `s.re = 1 / 2` via
`Set.mem_setOf_eq`, so `ClayRiemannHypothesis` and `RealPart` are definitionally
the same proposition and the `Iff` is witnessed by `Iff.rfl`, with no `constructor`
/ `intro` / `simpa` needed. If your Mathlib version's `Set.mem_setOf_eq` is not set
up to close this by plain `rfl`, fall back to
`by simp [ClayRiemannHypothesis, ClayRiemannHypothesis.Formulations.RealPart, CriticalLine]`.)
-/
theorem ClayRiemannHypothesis.iff_real_part :
    ClayRiemannHypothesis ↔ ClayRiemannHypothesis.Formulations.RealPart :=
  Iff.rfl

/-- Rephrase critical-line membership as the equation `re s = 1 / 2`. -/
theorem ClayRiemannHypothesis.real_part
    (h : ClayRiemannHypothesis) :
    ClayRiemannHypothesis.Formulations.RealPart :=
  ClayRiemannHypothesis.iff_real_part.1 h

/-- Under the Clay critical-line statement, every nontrivial zero has real part `1 / 2`. -/
theorem ClayRiemannHypothesis.zero_re_eq_half
    (h : ClayRiemannHypothesis) {s : ℂ} (hs : IsNontrivialZero s) :
    s.re = 1 / 2 :=
  h.real_part s hs

/-- Under the Clay critical-line statement, every nontrivial zero belongs to the critical line. -/
theorem ClayRiemannHypothesis.zero_mem_critical_line
    (h : ClayRiemannHypothesis) {s : ℂ} (hs : IsNontrivialZero s) :
    s ∈ CriticalLine :=
  h s hs

/-- Under the Clay critical-line statement, every nontrivial zero lies in the critical strip. -/
theorem ClayRiemannHypothesis.zero_mem_critical_strip
    (h : ClayRiemannHypothesis) {s : ℂ} (hs : IsNontrivialZero s) :
    s ∈ CriticalStrip :=
  CriticalLine.mem_critical_strip (h.zero_mem_critical_line hs)

/--
The real-part RH statement is equivalent to Mathlib's `_root_.RiemannHypothesis`.

(Simplified: rewritten from a `constructor`/`intro`/`exact` tactic block into a
direct term-mode `Iff` constructor — same proof content, fewer lines.)
-/
theorem ClayRiemannHypothesis.Formulations.RealPart.iff_mathlib :
    ClayRiemannHypothesis.Formulations.RealPart ↔ _root_.RiemannHypothesis :=
  ⟨fun h s hs0 htriv hs1 => h s ⟨hs0, htriv, hs1⟩,
   fun h s hs => h s hs.1 hs.2.1 hs.2.2⟩

/-- The real-part RH statement implies Mathlib's standard nontrivial-zero formulation. -/
theorem ClayRiemannHypothesis.Formulations.RealPart.mathlib :
    ClayRiemannHypothesis.Formulations.RealPart → _root_.RiemannHypothesis :=
  ClayRiemannHypothesis.Formulations.RealPart.iff_mathlib.1

/-- Mathlib's standard nontrivial-zero formulation implies the real-part RH statement. -/
theorem ClayRiemannHypothesis.Formulations.RealPart.of_mathlib :
    _root_.RiemannHypothesis → ClayRiemannHypothesis.Formulations.RealPart :=
  ClayRiemannHypothesis.Formulations.RealPart.iff_mathlib.2

/-- Translate Mathlib's standard RH formulation into the Clay critical-line statement. -/
theorem ClayRiemannHypothesis.of_mathlib
    (h : _root_.RiemannHypothesis) :
    ClayRiemannHypothesis :=
  ClayRiemannHypothesis.iff_real_part.2 (ClayRiemannHypothesis.Formulations.RealPart.of_mathlib h)

/-- Translate the Clay critical-line statement into Mathlib's standard RH formulation. -/
theorem ClayRiemannHypothesis.mathlib
    (h : ClayRiemannHypothesis) :
    _root_.RiemannHypothesis :=
  ClayRiemannHypothesis.Formulations.RealPart.mathlib h.real_part

/-!
Prime-number theory infrastructure used in the Clay write-up.
-/

/-- The Chebyshev `ψ(x)` function `∑_{n ≤ x} Λ(n)` from Mathlib. -/
noncomputable def psi_function (x : ℝ) : ℝ :=
  Chebyshev.psi x

/-- The Chebyshev `θ(x)` function `∑_{p ≤ x} log p` from Mathlib. -/
noncomputable def theta_function (x : ℝ) : ℝ :=
  Chebyshev.theta x

/-- The prime counting function `π(⌊x⌋₊)` from Mathlib. -/
noncomputable def prime_counting_function (x : ℝ) : ℕ :=
  Nat.primeCounting ⌊x⌋₊

/-- `ψ(x) = ∑_{n=1}^{⌊log x / log 2⌋} θ(x^{1/n})` for `x ≥ 0`. -/
theorem psi_eq_sum_theta {x : ℝ} (hx : 0 ≤ x) :
    psi_function x =
      ∑ n ∈ Finset.Icc 1 ⌊Real.log x / Real.log 2⌋₊, theta_function (x ^ ((1 : ℝ) / n)) := by
  simpa [psi_function, theta_function] using Chebyshev.psi_eq_sum_theta (x := x) hx

/-- `ψ(x) = θ(x) + ∑_{n=2}^{⌊log x / log 2⌋} θ(x^{1/n})` for `x ≥ 2`. -/
theorem psi_eq_theta_add_sum {x : ℝ} (hx : 2 ≤ x) :
    psi_function x =
      theta_function x +
        ∑ n ∈ Finset.Icc 2 ⌊Real.log x / Real.log 2⌋₊, theta_function (x ^ ((1 : ℝ) / n)) := by
  simpa [psi_function, theta_function] using Chebyshev.psi_eq_theta_add_sum_theta (x := x) hx

/-- `θ(x)` is the logarithm of the primorial `∏_{p ≤ x} p`. -/
theorem theta_eq_log_primorial (x : ℝ) : theta_function x = Real.log (primorial ⌊x⌋₊) := by
  simpa [theta_function] using Chebyshev.theta_eq_log_primorial x

/-- The logarithmic integral `Li(x)` used by Gauss. -/
noncomputable def logarithmic_integral (x : ℝ) : ℝ :=
  ∫ t in (2 : ℝ)..x, (Real.log t)⁻¹

/-- The prime counting function `π(x)` as a real number. -/
noncomputable def prime_counting_real (x : ℝ) : ℝ :=
  (prime_counting_function x : ℝ)

/-- Riemann's weighted prime counting function `Π(x)` from the Clay write-up. -/
noncomputable def riemann_pi (x : ℝ) : ℝ :=
  ∑ n ∈ Finset.Icc 1 ⌊Real.log x / Real.log 2⌋₊,
    prime_counting_real (x ^ ((1 : ℝ) / n)) / n

/--
For `re s > 1`, the Dirichlet series of the von Mangoldt function `Λ` agrees with the negative
logarithmic derivative `-ζ'(s)/ζ(s)`.
-/
theorem von_mangoldt_lseries_eq_negative_log_derivative_zeta {s : ℂ} (hs : 1 < s.re) :
    LSeries (fun n ↦ (ArithmeticFunction.vonMangoldt n : ℂ)) s =
      -deriv riemannZeta s / riemannZeta s := by
  simpa using ArithmeticFunction.LSeries_vonMangoldt_eq_deriv_riemannZeta_div (s := s) hs

/-- Euler product written in the "`exp ∘ log`" form. -/
theorem riemann_zeta_euler_product_exp_log {s : ℂ} (hs : 1 < s.re) :
    Complex.exp (∑' p : Nat.Primes, -Complex.log (1 - p ^ (-s))) = riemannZeta s :=
  _root_.riemannZeta_eulerProduct_exp_log hs

/-- Chebyshev's classical explicit upper bound `θ(x) ≤ log 4 · x`. -/
theorem theta_le_log4_mul_self {x : ℝ} (hx : 0 ≤ x) :
    theta_function x ≤ Real.log 4 * x := by
  simpa [theta_function] using Chebyshev.theta_le_log4_mul_x (x := x) hx

/-- Trivial inequality `θ(x) ≤ ψ(x)`. -/
theorem theta_le_psi (x : ℝ) : theta_function x ≤ psi_function x := by
  simpa [theta_function, psi_function] using Chebyshev.theta_le_psi x

/-- Chebyshev's explicit bound on `|ψ(x) - θ(x)|`. -/
theorem abs_psi_sub_theta_le_sqrt_log {x : ℝ} (hx : 1 ≤ x) :
    |psi_function x - theta_function x| ≤ 2 * Real.sqrt x * Real.log x := by
  simpa [psi_function, theta_function] using Chebyshev.abs_psi_sub_theta_le_sqrt_mul_log (x := x) hx

/-- Explicit upper bound on `ψ(x)` from Mathlib's Chebyshev development. -/
theorem psi_function_le {x : ℝ} (hx : 1 ≤ x) :
    psi_function x ≤ Real.log 4 * x + 2 * Real.sqrt x * Real.log x := by
  simpa [psi_function] using Chebyshev.psi_le (x := x) hx

/-- A coarser (but simpler) linear bound `ψ(x) ≤ (log 4 + 4) x`. -/
theorem psi_le_const_mul_self {x : ℝ} (hx : 0 ≤ x) :
    psi_function x ≤ (Real.log 4 + 4) * x := by
  simpa [psi_function] using Chebyshev.psi_le_const_mul_self (x := x) hx

/-- Every trivial zero is a zero of `ζ`. -/
theorem IsTrivialZero.riemann_zeta_eq_zero {s : ℂ} (hs : IsTrivialZero s) : riemannZeta s = 0 := by
  rcases hs with ⟨n, rfl⟩
  simpa using riemannZeta_neg_two_mul_nat_add_one n

/-!
## Main theorem

This final theorem records the Riemann Hypothesis target directly. Replace the placeholder proof
when one is available.
-/

/-- Clay Millennium Prize target for the Riemann Hypothesis. -/
theorem clay_prize_riemann_hypothesis :
    ClayRiemannHypothesis := by
  sorry

end Millennium
