# The Graded Prime-Exponent Monoid

## Abstract

A natural-sounding proposal is that a number system whose *dimension increases
under multiplication* might do for arithmetic what extending `R` to `C` did for
analysis. This article makes that proposal precise, and the precise version is
narrower than the slogan.

Written as zero-padding alone -- `1 -> (1,0) -> (1,0,0) -> ...` -- the idea has no
multiplication rule at all. It is an embedding, not an algebra, and it adds
nothing. There is exactly one multiplication rule that is *forced* once the
dimension is required to grow compatibly with multiplication: encode a number by
its vector of prime exponents, and let multiplication be coordinatewise addition
of exponent vectors. That rule is not a new axiom; it is unique factorisation
restated.

The resulting object is the free abelian monoid on the primes,
`bigoplus_p N_{>=0}`, presented as the direct limit of `N_{>=0}^k` under the
"pad with one more coordinate" inclusions.
`python/riemann_framework/graded_prime_monoid.py` constructs it, checks the
isomorphism to `(N_{>0}, x)` by brute force, and makes the connection to
`primon_gas.py` checkable rather than asserted.

This is not a sixth speculative track. It is the algebraic object already
implicit in the primon gas, given an explicit name.

## 1. Padding alone is inert

The `1 -> (1,0) -> (1,0,0) -> ...` tower is the first thing the slogan suggests.
It is arithmetically empty: padding changes the ambient space and never the
number. `dimension_tower(12, max_dim=6)` produces six elements, all of which
`to_int()` to 12, and `pad_to` is invertible by trimming.

That is worth recording rather than skipping, because it isolates what the idea
was actually missing. Padding is a *container*. A number system needs a
multiplication rule, and the next section identifies the only one available.

One trap lives here. The tower must start at the element's **ambient length** --
the index of its largest prime -- and not at its *dimension*. Those agree only
when the exponent tuple has no internal zeros:

| `n` | `GradedPrimeNumber` | dimension | ambient length |
|:---|:---|:---|:---|
| 12 | `(2, 1)` | 2 | 2 |
| 30 | `(1, 1, 1)` | 3 | 3 |
| 35 | `(0, 0, 1, 1)` | 2 | 4 |
| 97 | `(0, ..., 0, 1)` | 1 | 25 |

Starting at the dimension calls `pad_to(1)` on a length-25 tuple, which is a pad
*down* and raises. An earlier revision did exactly that and crashed for **81 of
the first 100 integers** -- every `n` not divisible by 2. Its guard tested the
same wrong quantity, so it did not catch the case either. See section 7.

## 2. The one multiplication rule

Encode `n = prod_p p^{e_p}` as its exponent vector, `from_int(n)`. Then define

```text
from_int(a) * from_int(b)  :=  from_int(a b),
```

which computes to coordinatewise addition of the exponent vectors, extended to
the larger of the two lengths. The claim that this is the *only* rule compatible
with unique factorisation is a theorem, and it is short.

> **Theorem.** Let `phi(n) = (v_p(n))_p` be the exponent vector of `n`, and let
> `star` be *any* operation on exponent vectors satisfying
> `phi(m n) = phi(m) star phi(n)`. Then `star` is componentwise addition.
>
> *Proof.* `phi` is surjective, being a bijection by unique factorisation. Given
> `v, w` choose `m, n` with `v = phi(m)`, `w = phi(n)`. Then
> `v star w = phi(m) star phi(n) = phi(m n) = phi(m) + phi(n) = v + w`. QED

Associativity, commutativity and an identity are **not** hypotheses; they are
consequences. `verify_monoid_isomorphism(n_max)` checks the conclusion by brute
force -- every pair `(a, b)` with `1 <= a, b <= n_max`, asserting
`from_int(a) * from_int(b) == from_int(a * b)` -- together with the round trip
`from_int(n).to_int() == n`. At `n_max = 80` that is 6400 pairs, all passing.

The honest reading is deflationary, and it is the finding: the
dimension-increasing number system is `(N_{>0}, x)` seen through its prime
factorisation. No alternative arithmetic was ever available to choose between.

### 2.1 The rivals, and where each first breaks

`verify_monoid_isomorphism` checks that addition *does* agree with integer
multiplication. That leaves the interesting half unstated, so the module also
runs six rules a "dimension-increasing number system" naturally suggests and
reports the first pair where each contradicts unique factorisation. At
`n_max = 200`:

| rule | what it is | first failure | required | produced |
|:---|:---|:---|:---|:---|
| `multiplication` | coordinatewise addition of exponents | — | — | — |
| `concatenate_prime_factors` | glue the two lists of prime factors | — | — | — |
| `exponent_max` | keep the larger exponent at each prime | `2 x 2` | 4 | 2 |
| `exponent_product` | multiply the exponents at each prime | `1 x 2` | 2 | 1 |
| `support_union` | union of supports, exponent 1 | `1 x 4` | 4 | 2 |
| `exponent_xor` | xor the exponents at each prime | `2 x 2` | 4 | 1 |

The second row is the interesting one, and it is not a rival at all.
**Concatenating the lists of prime factors is the same operation as adding the
exponent vectors.** A multiset union of prime factors and a componentwise sum of
exponents are two notations for one thing, so the literal "the dimension grows"
reading is not ruled out by the theorem -- it is an instance of it. The module
says so rather than pretending to refute it, and
`test_concatenating_prime_factors_is_the_same_rule_not_a_rival` pins the
agreement rather than leaving it as an aside.

This illustration is not the proof. The proof is the surjectivity argument above,
and no finite enumeration could replace it; what the table adds is concreteness,
so the claim that addition is forced has something to point at.

`candidate_rule_report` refuses `n_max < 4`. Below that the rivals' smallest
counterexamples lie outside the loop -- `2 x 2` for `exponent_max` and
`exponent_xor`, `1 x 4` for `support_union` -- and a rule would be reported as
holding without having been tested anywhere it fails.

## 3. Three notions of "dimension", and only one of them grows

This is where the slogan is easiest to misread, so the three candidates are worth
separating explicitly. They are all real, and they behave differently.

| notion | definition | under multiplication | `n = 12` | `n = 97` |
|:---|:---|:---|:---|:---|
| `omega(n)` | distinct primes dividing `n` | **subadditive**: `<= omega(m) + omega(n)`, equality iff `gcd(m,n) = 1` | 2 | 1 |
| `Omega(n)` | prime factors with multiplicity | **additive**: `Omega(m n) = Omega(m) + Omega(n)` | 3 | 1 |
| ambient length | index of the largest prime factor | **max**: `max(len m, len n)` | 2 | 25 |

`omega` is the dimension this module is built on, and it is the reading the
slogan intends: the number of independent directions an element occupies. It is
subadditive because shared primes do not open a new direction -- `dim(6) = 2` and
`dim(10) = 2` but `dim(60) = 3`, since 2 is shared -- while `dim(6) = 2` and
`dim(35) = 2` give `dim(210) = 4`, because the supports are disjoint.

Two consequences follow, and neither is a defect:

- **Product dimension is bounded by the sum**, so multiplication cannot
  manufacture directions that were not already available between the two factors.
- **Nothing here is unbounded growth in the sense that `C/R` has dimension 2.**
  The ambient space is fixed at `bigoplus_p N_{>=0}`; what changes is which finite
  piece of it an element needs, and how many directions it occupies.

`Omega` is the additive grade, and it is the one that grows without bound; it is
also the one whose generating function is the primon gas energy. The ambient
length is the filtration degree: it says how many *generators were made
available*, and multiplication never raises it. Confusing these three is the main
available error, and a statement about one is not a statement about another.

## 4. The direct limit

The pieces

```text
V_k = { v : v(p) = 0 for all p > p_k }  ~=  N_{>=0}^k
```

are nested under the inclusion that appends a zero coordinate, and their union is
all of `bigoplus_p N_{>=0}`. So

```text
colim_k V_k  =  bigoplus_p N_{>=0},
```

which is the free abelian monoid on the primes -- exactly the `1 -> (1,0) ->
(1,0,0) -> ...` pattern, but now carrying the one multiplication rule that
pattern can support rather than silent padding. Read as integers rather than
vectors, `V_k` is the set of `p_k`-smooth numbers, i.e. the numbers of dimension
at most `k` in the ambient-length sense.

The inclusion is injective and a monoid homomorphism; `pad_to` is its concrete
form, and `GradedPrimeNumber.__eq__` implements the direct-limit identification by
comparing *trimmed* tuples, so `(1,)` and `(1, 0)` are the same element while
`(0, 0, 1, 1)` is correctly distinct from `(1, 1)`.

## 5. The bridge to the primon gas

`l^2(N)` with basis `|n>` is this monoid's group algebra, and multiplication in
the monoid is what makes `n^{-s} * m^{-s} = (n m)^{-s}` hold. The energy

```text
H |n> = log(n) |n>
```

is a **linear functional of the exponent vector**,
`log(n) = sum_p v_p(n) log(p)`, which is the structural reason the trace
factorises.

`bridge_to_primon_gas(n_max)` partitions `1..n_max` by dimension, sums each part's
contribution to `sum n^-s`, and *compares the total against
`primon_gas.trace_exp(s, n_max)`* rather than telling the reader to. At
`n_max = 2000` the two agree to machine precision.

**What that check does and does not establish.** The two sides are the same sum
computed two ways, so it verifies that the partition by dimension is complete and
correctly totalled. It does *not* verify that the sum factorises. That is the next
section, and the distinction is worth keeping, because a regrouping that happens
to be complete is much weaker evidence than a factorisation.

## 6. The Euler product is this monoid's zeta-like sum

The factorisation is the statement that a sum of a product over a *free
commutative* monoid is a product of sums. Both sides are computable, and
`euler_product_from_grading` checks them against each other:

```text
sum over v with 0 <= v_p <= D of  q^{omega(v)} prod_p p^{-s v_p}
    =
prod_{p <= P} ( 1 + q * sum_{a=1..D} p^{-s a} ).
```

The local factor is the whole content, and it is the step that makes the grading
by `omega` -- distinct primes -- give the Euler product rather than some other
regrouping:

```text
sum_{a >= 0} q^{omega(p^a)} p^{-s a}  =  1 + q * p^{-s} / (1 - p^{-s}),
```

because `omega(p^a)` is 0 at `a = 0` and 1 for every `a >= 1`. At `q = 1` that is

```text
1 + p^{-s}/(1 - p^{-s})  =  1/(1 - p^{-s}),
```

which is exactly the Euler factor. So the monoid structure, and not a coincidence
of the arithmetic, is what makes the primon gas trace exact.

Measured, at `s = 2`, `prime_limit = 13` (six primes), `degree_cap = 6`, over
117649 exponent vectors:

| `q` | monoid sum | product of local factors | agree |
|:---|:---|:---|:---|
| 1.0 | `1.617818572943` | `1.617818572943` | yes |
| 0.5 | `1.287692900299` | `1.287692900299` | yes |

And the `q = 1` product, which is `prod_p 1/(1 - p^{-s})` once the degree cap is
removed, climbs toward `zeta(2) = 1.6449340668482264` as primes are added:

| prime limit | truncated Euler product | relative error |
|:---|:---|:---|
| 13 | `1.617917661314` | `1.64e-02` |
| 97 | `1.641945196621` | `1.82e-03` |
| 997 | `1.644725190239` | `1.27e-04` |
| 9973 | `1.644917920746` | `9.82e-06` |
| 99991 | `1.644932747203` | `8.02e-07` |

`output/graded_prime_monoid_convergence.png` plots both panels of that table.

## 7. Defects found on review, and what they cost

Both were found by reading the code and then measuring, not by reading the tests.

**The module did not import.** It used `factorint`, `prime` and `primerange` from
sympy, which is neither installed nor declared in `pyproject.toml`. The module
raised `ModuleNotFoundError`, its test file failed at *collection*, and the whole
suite went down with it. `primon_gas.factorize` already provides exact
trial-division factorisation, and this repository deliberately depends only on
mpmath/numpy/scipy -- `affine_reduction.py` records removing a sympy dependency
for the same reason. `test_no_package_module_imports_sympy` now scans import
statements by AST rather than by substring, since two modules mention sympy in
prose to explain its removal.

**`dimension_tower` crashed for most inputs.** Covered in section 1: it started at
the element's dimension instead of its ambient length, and the guard tested the
same wrong quantity. 81 of the first 100 integers raised.

**Why the tests missed the second one.** The tower tests used `12` and `30`, whose
exponent tuples have no internal zeros -- precisely the case where the two
quantities coincide. A test that passes is not evidence that the surrounding cases
pass, and the fix here is a parametrised regression over `3, 5, 7, 10, 14, 35, 97`,
all of which have internal zeros.

## 8. What this does not do

**It does not produce a new number system.** The object is isomorphic to
`(N_{>0}, x)`; the module's whole point is that the isomorphism is checkable. The
slogan's "dimension" is `omega`, a function on the integers, not a new coordinate
that arithmetic did not already have.

**It does not touch the zeros.** The eigenvalues of `H` are `log(n)`, not the
imaginary parts of the zeta zeros. This anchors the Euler product and says nothing
about where the zeros are.

**It does not close the programme's open question.** Whether some richer system
could both contain the primes and force the zeros onto a fixed locus is untouched.
What this does is remove one candidate answer: "a number system whose
multiplication adds dimensions" cannot be that system, because it is not new.

## 9. Files

| file | role |
|:---|:---|
| `python/riemann_framework/graded_prime_monoid.py` | the monoid, the isomorphism check, the bridge, the Euler check |
| `python/tests/test_graded_prime_monoid.py` | 52 tests |
| `scripts/run_graded_prime_monoid_demo.py` | prints all five parts and writes the figure |
| `output/graded_prime_monoid_convergence.png` | the Euler product approaching `zeta(2)` |

## References

- Julia, B. (1990). *Statistical mechanics of the arithmetic gas*.
- Spector, D. (1990). *Supersymmetry and the Möbius inversion function*.
- Bost, J.-B. and Connes, A. (1995). *Hecke algebras, type III factors and phase transitions with spontaneous symmetry breaking in number theory*.
- Hardy, G. H. and Wright, E. M. (1938). *An Introduction to the Theory of Numbers* (the fundamental theorem of arithmetic).

## Disclaimer

This article is not a proof of the Riemann Hypothesis and does not claim to be. It
is a precise statement of a slogan, a short theorem showing that the slogan
describes ordinary arithmetic rather than extending it, and computations that
check the theorem's hypotheses over a range and the factorisation identity
directly. The computations illustrate; they do not replace the proof in section 2.
