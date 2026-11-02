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

import Mathlib.Data.Fintype.Card
import Mathlib.LinearAlgebra.Eigenspace.Basic

/-!
# The boundary of the sector count

Two facts about the labels the diagnostic uses, one correction, and the true statement
where the correction sits.

## What is proved here

1. `k` commuting involutions cut out at most `2 ^ k` joint sectors, because a joint
   sector is a sign vector and there are `2 ^ k` of them (`card_sectorLabel`).
2. Swapping one sign (`flipSign i`, the sector swap listed as Priority 4 in
   `docs/future_work.md`) is an involution, hence injective, and has no fixed label:
   the sectors pair up (`flipSign_involutive`, `flipSign_injective`,
   `flipSign_ne_self`).
3. `eigenspace_isCompl`: the `+1` and `-1` eigenspaces of an involution are
   complementary when `2` is invertible, so their dimensions *add up* to the ambient
   dimension.

## The correction

`docs/future_work.md` Priority 4 used to ask for a proof that "finite `+1` and `-1`
eigenspaces have equal dimension", and the docstring of
`RiemannFramework.InvolutionEigenspace` listed the same item. **That statement is
false.** `signFlip = diag(1, 1, -1)` satisfies `T * T = 1` and has a two-dimensional
`+1` eigenspace against a one-dimensional `-1` eigenspace.

This is not a corner case to be patched: unequal sectors are exactly what
`docs/mixed_sectors.md` measures, and a dominant block is the situation the
equal-block posterior gets wrong. The diagnostic must not assume equal dimensions,
and `eigenspaces_can_differ` makes that assumption one compiling error away rather
than one paragraph away.

None of this says anything about the Riemann hypothesis or about any particular
Hamiltonian. Every operator statement carries `T * T = 1` as an explicit hypothesis,
and the counterexample is a three-dimensional linear map over `ℚ`.
-/

namespace RiemannFramework

/-! ## The labels: `2 ^ k` sectors, paired by the swap -/

/-- A joint sector label: one sign per involution. -/
abbrev SectorLabel (k : ℕ) := Fin k → Bool

/-- `k` involutions cut out exactly `2 ^ k` sign vectors. -/
theorem card_sectorLabel (k : ℕ) : Fintype.card (SectorLabel k) = 2 ^ k := by
  simp [SectorLabel]

/-- The sector swap: flip the `i`-th sign and leave the others alone. -/
def flipSign {k : ℕ} (i : Fin k) (label : SectorLabel k) : SectorLabel k :=
  Function.update label i (!(label i))

/-- Swapping a sign twice is the identity. -/
theorem flipSign_involutive {k : ℕ} (i : Fin k) : Function.Involutive (flipSign i) := by
  intro label
  funext j
  by_cases h : j = i
  · subst h
    simp [flipSign, Function.update]
  · simp [flipSign, Function.update, h]

/-- The sector swap is injective. -/
theorem flipSign_injective {k : ℕ} (i : Fin k) : Function.Injective (flipSign i) :=
  (flipSign_involutive i).injective

/-- No sector is its own image under the swap: the sectors pair up without a fixed point. -/
theorem flipSign_ne_self {k : ℕ} (i : Fin k) (label : SectorLabel k) :
    flipSign i label ≠ label := by
  intro h
  have h' := congrFun h i
  simp [flipSign, Function.update] at h'

/-! ## The correction: the eigenspaces need not have equal dimension -/

/-- The involution `(a, b, c) -> (a, b, -c)` on `ℚ × ℚ × ℚ`. -/
def signFlip : Module.End ℚ (ℚ × ℚ × ℚ) where
  toFun x := (x.1, x.2.1, -x.2.2)
  map_add' x y := by
    ext <;> simp [add_comm]
  map_smul' c x := by
    simp

/-- The map squares to the identity, so it is a genuine involution. -/
theorem signFlip_is_involution : signFlip * signFlip = 1 := by
  apply LinearMap.ext
  intro x
  simp [signFlip]

/-- The `+1` and `-1` eigenspaces of an involution are **not** in general equal.

This is the machine-checked refutation of the equal-dimension item that used to be
listed as future work. The witness is `(0, 0, 1)`: an eigenvector of `signFlip` with
eigenvalue `-1` and not with eigenvalue `+1`. -/
theorem eigenspaces_can_differ :
    Module.End.eigenspace signFlip 1 ≠ Module.End.eigenspace signFlip (-1) := by
  intro h
  have mem : (0, 0, 1) ∈ Module.End.eigenspace signFlip (-1) := by
    rw [Module.End.mem_eigenspace_iff]
    simp [signFlip]
  rw [← h] at mem
  rw [Module.End.mem_eigenspace_iff] at mem
  norm_num [signFlip] at mem

/-! ## The true statement: the eigenspaces are complementary -/

section Complement

variable {K V : Type*} [Field K] [AddCommGroup V] [Module K V]

/-- An involution splits every vector into a `+1` part and a `-1` part, provided
`2 ≠ 0`, so the two eigenspaces are complementary and their dimensions add up.

Equality of the dimensions is the claim that fails: `eigenspaces_can_differ` is the
counterexample. What holds is the sum. -/
theorem eigenspace_isCompl (T : Module.End K V) (hT : T * T = 1) [NeZero (2 : K)] :
    IsCompl (Module.End.eigenspace T 1) (Module.End.eigenspace T (-1)) := by
  have hTT : ∀ x : V, T (T x) = x := by
    intro x
    have h := congrArg (fun f : Module.End K V => f x) hT
    simpa using h
  have plus_mem : ∀ x : V,
      ((2 : K)⁻¹ • (x + T x)) ∈ Module.End.eigenspace T 1 := by
    intro x
    rw [Module.End.mem_eigenspace_iff, one_smul, map_smul, map_add, hTT x, add_comm]
  have minus_mem : ∀ x : V,
      ((2 : K)⁻¹ • (x - T x)) ∈ Module.End.eigenspace T (-1) := by
    intro x
    rw [Module.End.mem_eigenspace_iff, map_smul, map_sub, hTT x, neg_one_smul,
      ← smul_neg, neg_sub]
  refine IsCompl.of_eq ?_ ?_
  · rw [eq_bot_iff]
    intro x hx
    rw [Submodule.mem_inf] at hx
    obtain ⟨h1, h2⟩ := hx
    rw [Module.End.mem_eigenspace_iff] at h1 h2
    rw [one_smul] at h1
    rw [neg_one_smul] at h2
    rw [Submodule.mem_bot]
    have hx0 : (2 : K) • x = 0 := by
      rw [two_smul]
      nth_rewrite 1 [← h1]
      rw [h2, neg_add_cancel]
    exact (smul_eq_zero.mp hx0).resolve_left (NeZero.ne (2 : K))
  · rw [eq_top_iff]
    intro x _
    have key : (2 : K)⁻¹ • (x + T x) + (2 : K)⁻¹ • (x - T x) = x := by
      rw [← smul_add]
      have hsum : (x + T x) + (x - T x) = (2 : K) • x := by
        rw [two_smul]
        abel
      rw [hsum, smul_smul, inv_mul_cancel₀ (NeZero.ne (2 : K)), one_smul]
    exact Submodule.mem_sup.mpr ⟨_, plus_mem x, _, minus_mem x, key⟩

end Complement

end RiemannFramework
