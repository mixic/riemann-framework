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

import Mathlib.LinearAlgebra.Eigenspace.Basic
import Mathlib.LinearAlgebra.FiniteDimensional.Lemmas

/-!
# Involution eigenspaces

Pure linear algebra, independent of any analytic or spectral claim: if a
linear endomorphism `T` of a vector space satisfies `T * T = 1`, then its
`+1` and `-1` eigenspaces are exactly the kernels of `T - 1` and `T + 1`,
and `T - 1` and `T + 1` annihilate each other.

None of this proves the Riemann Hypothesis or the Dimension-Shift
Hypothesis. It records the algebraic core of a `ℤ/2` symmetry, so that
later spectral statements can rest on explicit hypotheses.

Every result here is *conditional*: `T * T = 1` is an explicit hypothesis of
each statement, never something the framework establishes about a physical
Hamiltonian. None of these lemmas needs finite dimension or a
characteristic assumption.

Still open for this module, tracked in `docs/future_work.md` (Priority 4):

1. the range descriptions `T.eigenspace 1 = (T + 1).range` and
   `T.eigenspace (-1) = (T - 1).range`;
2. that the two eigenspaces are complementary and have equal dimension; and
3. that each has half the dimension of the ambient space.

Items 1-3 reduce to a rank-nullity computation over `Nat` subtraction
(`finrank` coercions plus `Nat` truncated subtraction). The mutual
annihilation identities they need are proved below; the remaining gap is
converting `T.range ≤ S.ker` plus `S.range ≤ T.ker` into
`S.range = T.ker` over `finrank`.
-/

namespace RiemannFramework

open Module

variable {K V : Type*} [Field K] [AddCommGroup V] [Module K V]

/-- Membership in the kernel of `T - 1`, unfolded pointwise. -/
private theorem mem_ker_sub_one_iff (T : Module.End K V) (x : V) : x ∈ (T - 1).ker ↔ T x = x := by
  rw [LinearMap.mem_ker, LinearMap.sub_apply, Module.End.one_apply, sub_eq_zero]

/-- Membership in the kernel of `T + 1`, unfolded pointwise. -/
private theorem mem_ker_add_one_iff (T : Module.End K V) (x : V) : x ∈ (T + 1).ker ↔ T x = -x := by
  rw [LinearMap.mem_ker, LinearMap.add_apply, Module.End.one_apply, add_eq_zero_iff_eq_neg]

/-- The pointwise form of `T * T = 1`, used to rewrite under the maps
`T - 1` and `T + 1`. -/
private theorem apply_apply_eq_self (T : Module.End K V) (hT : T * T = 1) (x : V) :
    T (T x) = x :=
  congrArg (fun f : Module.End K V => f x) hT

/-- The `+1` eigenspace of an involution is the kernel of `T - 1`. No
finite-dimensionality or characteristic assumption is needed. -/
theorem eigenspace_one_eq_ker_sub_one (T : Module.End K V) (_hT : T * T = 1) :
    T.eigenspace 1 = (T - 1).ker := by
  ext x
  rw [Module.End.mem_eigenspace_iff, one_smul, mem_ker_sub_one_iff]

/-- The `-1` eigenspace of an involution is the kernel of `T + 1`. No
finite-dimensionality or characteristic assumption is needed. -/
theorem eigenspace_neg_one_eq_ker_add_one (T : Module.End K V) (_hT : T * T = 1) :
    T.eigenspace (-1) = (T + 1).ker := by
  ext x
  rw [Module.End.mem_eigenspace_iff, neg_one_smul, mem_ker_add_one_iff]

/-- An involution satisfies `(T - 1) ∘ (T + 1) = 0`: every vector in the
range of `T + 1` is fixed by `T`. No finite-dimensionality or
characteristic assumption is needed. -/
theorem sub_one_comp_add_one (T : Module.End K V) (hT : T * T = 1) :
    (T - 1) ∘ₗ (T + 1) = 0 := by
  ext x
  show T (T x + x) - (T x + x) = (0 : Module.End K V) x
  rw [map_add]
  simp only [apply_apply_eq_self T hT x, LinearMap.zero_apply]
  abel

/-- An involution satisfies `(T + 1) ∘ (T - 1) = 0`: every vector in the
range of `T - 1` is negated by `T`. No finite-dimensionality or
characteristic assumption is needed. -/
theorem add_one_comp_sub_one (T : Module.End K V) (hT : T * T = 1) :
    (T + 1) ∘ₗ (T - 1) = 0 := by
  ext x
  show T (T x - x) + (T x - x) = (0 : Module.End K V) x
  rw [map_sub]
  simp only [apply_apply_eq_self T hT x, LinearMap.zero_apply]
  abel

/-- A map commuting with `T` preserves the kernel of `T - 1`. -/
theorem maps_ker_sub_one (T S : Module.End K V) (h : T * S = S * T) :
    ∀ x ∈ (T - 1).ker, S x ∈ (T - 1).ker := by
  intro x hx
  rw [mem_ker_sub_one_iff] at hx ⊢
  calc T (S x) = (T * S) x := rfl
    _ = (S * T) x := by rw [h]
    _ = S (T x) := rfl
    _ = S x := by rw [hx]

/-- A map commuting with `T` preserves the kernel of `T + 1`. -/
theorem maps_ker_add_one (T S : Module.End K V) (h : T * S = S * T) :
    ∀ x ∈ (T + 1).ker, S x ∈ (T + 1).ker := by
  intro x hx
  rw [mem_ker_add_one_iff] at hx ⊢
  calc T (S x) = (T * S) x := rfl
    _ = (S * T) x := by rw [h]
    _ = S (T x) := rfl
    _ = S (-x) := by rw [hx]
    _ = -S x := map_neg S x

/-- **A commuting operator preserves the involution's eigenspaces** — item 4 of the
formalization plan in `docs/future_work.md`. This is the `+1` eigenspace;
`maps_eigenspace_neg_one` is the companion.

No finite-dimensionality, rank-nullity, or characteristic assumption is involved.
This is the map being well defined on an eigenspace, not a dimension count, which
is why item 4 was separable from the equal-dimension results that the plan had
grouped it with. -/
theorem maps_eigenspace_one (T S : Module.End K V) (hT : T * T = 1) (h : T * S = S * T) :
    ∀ x ∈ T.eigenspace 1, S x ∈ T.eigenspace 1 := by
  rw [eigenspace_one_eq_ker_sub_one T hT]
  exact maps_ker_sub_one T S h

/-- Companion to `maps_eigenspace_one`: a commuting operator preserves the `-1`
eigenspace. -/
theorem maps_eigenspace_neg_one (T S : Module.End K V) (hT : T * T = 1) (h : T * S = S * T) :
    ∀ x ∈ T.eigenspace (-1), S x ∈ T.eigenspace (-1) := by
  rw [eigenspace_neg_one_eq_ker_add_one T hT]
  exact maps_ker_add_one T S h

end RiemannFramework
