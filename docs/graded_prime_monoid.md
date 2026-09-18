# The Graded Prime Monoid

## Abstract

`docs/spherical_number_systems.md` asks a question in testable form: does
multiplication of prime objects recover unique factorization? This article
answers it, and the answer is narrower than the intuition that prompted it.

A "number system whose dimension increases under multiplication" is, made
precise, the **free commutative monoid on the primes**: the monoid `V` of
finitely supported exponent vectors under componentwise addition, with

```text
phi : (N_{>0}, x) -> (V, +),       phi(n) = (v_p(n))_p
```

a bijection by the fundamental theorem of arithmetic. Two things follow, and
both are short.

**The operation is forced.** Exponent-vector addition is not one rule among
several compatible with unique factorization; it is the only one. The proof is
one line, and it does not need associativity or commutativity as hypotheses.

**This is why the primon gas is exact.** With `H|n> = log(n)|n>`, the energy is
a *linear functional of the exponent vector*, so `Tr[e^{-sH}]` is a sum of a
product over a free commutative monoid — and that is a product of sums, i.e. the
Euler product. The factorization is the monoid structure, not a coincidence of
the arithmetic.

The honest reading is deflationary, in the same way and for the same reason that
`docs/dimension_shift_involution.md` section 2.1 deflates the dimension-shift
prototype: the intuition, once precise, turns out to describe structure that
ordinary arithmetic already has. No new number system is produced, and nothing
here bears on the location of the zeros.

## 1. The identification

Let `P` be the primes and let

```text
V = { v : P -> N : v(p) = 0 for all but finitely many p }
```

be the finitely supported exponent vectors, stored sparsely as `{prime: exp}`.
The fundamental theorem of arithmetic is the statement that

```text
phi(n) = (v_p(n))_p
```

is a bijection from `N_{>0}` onto `V`. It is multiplicative by construction,
since `v_p(m n) = v_p(m) + v_p(n)`.

So `(N_{>0}, x)` **is** the free commutative monoid on the primes: the free
commutative monoid on a set `S` is the set of finitely supported `N`-valued
functions on `S` under addition, and here `S = P`. The phrase "free commutative"
is doing the work in the rest of this article — it is what licenses turning a
sum of a product into a product of sums.

This is grade-school arithmetic, restated. The restatement is the point: it is
what makes the slogan "the dimension increases under multiplication" precise
enough to be either true or false.

## 2. The uniqueness theorem

> **Theorem.** Let `phi` be as above, and let `star` be *any* operation
> `V x V -> V` satisfying
>
> ```text
> phi(m n) = phi(m) star phi(n)        for all m, n >= 1.
> ```
>
> Then `star` is componentwise addition.
>
> *Proof.* `phi` is surjective, being a bijection. Given `v, w` in `V`, choose
> `m, n` with `v = phi(m)` and `w = phi(n)`. Then
>
> ```text
> v star w = phi(m) star phi(n) = phi(m n) = phi(m) + phi(n) = v + w,
> ```
>
> using multiplicativity of `star` in the middle and `v_p(m n) = v_p(m) +
> v_p(n)` at the end. ∎

Two remarks on the statement, because both matter and both are easy to miss.

**Nothing else is assumed.** `star` need not be associative, commutative, or
have an identity. Surjectivity of `phi` alone pins it down on all of `V`.
Associativity and commutativity are consequences, not hypotheses — so "the only
*associative* rule" would be a weaker theorem than the one that holds.

**The theorem is nearly content-free, and that is the finding.** Its whole
content is that `phi` is a bijection, which is unique factorization. The claim
"addition is the only multiplication rule compatible with unique factorization"
is therefore not a discovery about the primes; it is unique factorization,
re-read as a statement about a monoid isomorphism. Anyone hoping the slogan
names an *alternative* arithmetic should note that no choice was ever available.

### 2.1 The rival rules, and where each first breaks

The theorem says addition is forced. The module also runs six plausible rival
rules over `1..200` and reports the first pair where each contradicts unique
factorization. This illustrates the theorem; it does not establish it, since no
finite enumeration could.

| rule | description | first failure | expected | produced |
|:---|:---|:---|:---|:---|
| `addition` | componentwise addition of exponents | — | — | — |
| `concatenate_prime_factors` | glue the two lists of prime factors | — | — | — |
| `exponent_max` | keep the larger exponent per prime | `2 x 2` | 4 | 2 |
| `exponent_product` | multiply the exponents per prime | `1 x 2` | 2 | 1 |
| `support_union` | union of supports, exponent 1 | `1 x 4` | 4 | 2 |
| `exponent_xor` | xor the exponents per prime | `2 x 2` | 4 | 1 |

The second row is the interesting one, and it is not a rival at all.
**Concatenating the lists of prime factors is the same operation as adding the
exponent vectors.** A multiset union of prime factors and a componentwise sum of
exponents are two notations for one thing, so the literal "the dimension grows"
reading is not ruled out by the theorem — it is an instance of it. The test
`test_addition_and_factor_concatenation_are_the_same_rule` pins that agreement
rather than leaving it as an aside.

## 3. The grading, and what "dimension" can honestly mean

`V` is graded by total degree:

```text
Omega(v) = sum_p v(p)         and       Omega(m n) = Omega(m) + Omega(n).
```

`Omega(n)` is the number of prime factors of `n` counted with multiplicity, and
it is the only "dimension" in the slogan that survives inspection: the degree of
`phi(n)` counts how many generators went into building `n`, and multiplication
adds degrees. `V` is the direct sum of the finite sets `V_d = {v : Omega(v) = d}`.

| `Omega` | count up to 64 | examples |
|:---|:---|:---|
| 0 | 1 | 1 |
| 1 | 18 | 2, 3, 5, 7, 11, 13, ... |
| 2 | 22 | 4, 6, 9, 10, 14, 15, ... |
| 3 | 13 | 8, 12, 18, 20, 27, 28, ... |
| 4 | 7 | 16, 24, 36, 40, 54, 56, 60 |
| 5 | 2 | 32, 48 |
| 6 | 1 | 64 |

What this does *not* say is that the system has a dimension in the sense that
`C` has dimension 2 over `R`, or that multiplying two elements produces an
element in a larger ambient space. The ambient space `V` is fixed; what grows is
the degree of the element within it, and the size of its support. A dimension
that increased without bound would need an inverse limit of ambient spaces, and
no such object is constructed here or needed for the arithmetic.

## 4. Why this makes the primon gas exact

`primon_gas.py` builds `H|n> = log(n)|n>` on `l^2(N)` and records
`Tr[e^{-sH}] = zeta(s)`. The reason the trace factorizes is the monoid
structure of section 1, in one line: the energy is a **linear functional of the
exponent vector**,

```text
log(n) = sum_p v_p(n) log(p) = <lambda, phi(n)>,        lambda_p = log(p),
```

so summing `n^{-s} = exp(-s <lambda, phi(n)>)` over `N_{>0}` is summing
`prod_p x_p^{v_p}` over the free commutative monoid, with `x_p = p^{-s}`. A sum
of a product over a *free commutative* monoid is a product of sums — that is what
"free commutative" means, and it is the whole content of the Euler product:

```text
sum_{v in V} prod_p x_p^{v_p}  =  prod_p sum_{a >= 0} x_p^a  =  prod_p 1/(1 - x_p).
```

### 4.1 The finite identity, checked

`euler_box_sum` enumerates the monoid truncated to a box `0 <= v_p <= D` over a
finite prime basis; `euler_product_formula` computes the same quantity as a
product of per-prime geometric series. They must agree, and they do:

| quantity | value |
|:---|:---|
| basis | `(2, 3, 5, 7, 11, 13)` |
| degree cap | 3 |
| monoid elements enumerated | 4096 |
| enumerated box sum | `1.611347623448060` |
| product formula | `1.611347623448065` |
| relative difference | `3.31e-15` |

The residual is floating-point round-off, not a truncation error: the identity
is algebraic and exact for any finite box. `test_box_sum_equals_the_product_formula`
checks it at `s = 2.0`, `1.5`, `3.0` and at a non-real `s = 2 + 3i`, since the
identity does not require `Re(s) > 1` — only the interpretation of the limit as
`zeta(s)` does.

### 4.2 The truncation climbs to `zeta(s)`

The box over the primes `<= P` is the sum of `n^{-s}` over the `P`-smooth numbers
with exponents at most `D`. Raising either cap adds terms, so the box approaches
`zeta(s)` from below:

| prime cap `P` | generators | degree cap `D` | box sum | relative error |
|:---|:---|:---|:---|:---|
| 13 | 6 | 4 | `1.616310119471` | `1.74e-02` |
| 97 | 25 | 12 | `1.641945172154` | `1.82e-03` |
| 997 | 168 | 40 | `1.644725190239` | `1.27e-04` |
| 1999 | 303 | 40 | `1.644838146904` | `5.83e-05` |

`zeta(2) = 1.6449340668482264`. This is the same limit that
`primon_gas.trace_convergence` measures along the `n <= N` truncation; the
difference is only which truncation of the same monoid is taken, and the
`smooth` one is the monoid-natural one.

`output/graded_prime_monoid_convergence.png` plots both panels of that table.

## 5. What this does not do

**It does not produce a new number system.** `V` is not an extension of `C`, and
the theorem of section 2 is a statement about ordinary arithmetic. The module
constructs no ambient space in which the primes are new objects.

**It does not touch the zeros.** The eigenvalues of `H` are `log(n)`, not the
imaginary parts of the zeta zeros; `docs/spherical_number_systems.md` section 3.4
is explicit that an operator whose spectrum *is* the zeros is a separate and
still-open construction. Nothing here proves anything about the Riemann
Hypothesis.

**It does not close the programme's open question.** The uniqueness theorem says
that *given* unique factorization the operation is forced. Whether some richer
system could both contain the primes and force the zeros onto a fixed locus is
exactly the open question, and this article does not address it. What the theorem
does is remove one candidate answer: "a number system whose multiplication adds
dimensions" cannot be that system, because it is not new.

## 6. Relation to the rest of the repository

| this article | the parallel |
|:---|:---|
| The slogan, made precise, is unique factorization restated | `dimension_shift_involution.md` §2.1: the prototype map is an affine map restated |
| Both were screened before numerics were built on them (`future_work.md` §3.3) | the affine-reduction gate is the same kind of filter |
| The residue is a *precise statement of what already holds*, not a new object | the residue there is `Fix(sigma) = Re(s) = 1/2`, true but non-forcing |
| The primon gas anchors the Euler product exactly | `primon_gas.py`, and `future_work.md` Priority 5.1 |

`docs/future_work.md` Priority 5 records that the dimension-shift model "has no
derived prime structure" and that the primon gas "anchors the Euler product, not
the zeros". This article supplies the structure that was implicitly being
appealed to when the model was said to have none — and confirms that it anchors
the Euler product and nothing further.

## References

- Julia, B. (1990). *Statistical mechanics of the arithmetic gas*.
- Spector, D. (1990). *Supersymmetry and the Möbius inversion function*.
- Bost, J.-B. and Connes, A. (1995). *Hecke algebras, type III factors and phase transitions with spontaneous symmetry breaking in number theory*.
- Hardy, G. H. and Wright, E. M. (1938). *An Introduction to the Theory of Numbers* (the fundamental theorem of arithmetic).

## Disclaimer

This article is not a proof of the Riemann Hypothesis, and it does not claim to
be. It is a precise statement of a slogan, together with a short theorem showing
that the slogan describes ordinary arithmetic rather than extending it. The
computations here check the hypotheses of that theorem over a range and illustrate
its conclusion; they do not replace it.
