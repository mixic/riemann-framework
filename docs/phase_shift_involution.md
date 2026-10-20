# The relative-phase involution in DSIN and its I/Q counterpart

*Status: interpretive note. This does not prove or disprove the Riemann
Hypothesis, and it does not claim a new modulation scheme or a security
result.*

---

## 1. The object in DSIN

DSIN uses a two-sector Hilbert space

```text
H = H_b + H_f
```

and two different involutions.

The **sector swap** is

```text
sigma = [[0, I],
         [I, 0]],
```

with `sigma^2 = I`. Its `+1` eigenspace is the equal-weight symmetric
subspace

```text
Fix(sigma) = {(u, u)/sqrt(2)}.
```

The **relative phase flip** is

```text
tau = [[I,  0],
       [0, -I]],
```

so `tau |b,k> = |b,k>` and `tau |f,k> = -|f,k>`. It satisfies
`tau^2 = I`, is unitary, and is Hermitian. Its fixed subspace is the bosonic
sector,

```text
Fix(tau) = {(u, 0)},
```

not the equal-weight subspace. The equal-weight statement belongs to
`sigma`, not `tau`.

The two involutions anticommute:

```text
sigma tau = - tau sigma.
```

Therefore `tau` maps the `+1` eigenspace of `sigma` to the `-1` eigenspace:

```text
tau |+> = |->,     tau |-> = |+>,
```

where

```text
|+> = (|b,k> + |f,k>)/sqrt(2),
|-> = (|b,k> - |f,k>)/sqrt(2).
```

If a bit is encoded in the `sigma` eigenvalue, `tau` inverts the bit. It also
changes the sign of `<sigma>` while leaving its magnitude unchanged. The
parity **meter** thresholds the deviation of `|<sigma>|` from 1, so it records
no disturbance; the data decoder still measures `sigma` and returns the
opposite bit.

In the code, `dsin.apply_phase_noise(state, pi, rng)` multiplies the
fermionic block by `exp(i pi) = -1`. In `run_simulation` this is the
`noise_type="phase"`, `noise_param=pi` row: detection `0.0000`, BER `1.0000`.
See `docs/dimension_shift_quantum_communication.md` §3.4.

---

## 2. What it is not

- **Not the sector swap.** `sigma` swaps sectors; `tau` multiplies one sector
  by `-1`. They anticommute, and their fixed loci differ.
- **Not the dimension-shift involution on the complex slice.** That prototype
  is `sigma(s) = 1 - conjugate(s)`, with fixed locus `Re(s) = 1/2`. It is a
  different object acting on a different space. The shared vocabulary
  (“involution”, “fixed locus”, “sector”) is structural, not an identity.
- **Not a continuous phase rotation.** It is the discrete element at
  `theta = pi` acting on one sector.
- **Not automatically a logical bit flip.** In the sector basis, `tau` is
  diagonal and `sigma` is the swap. In the `sigma` eigenbasis, the roles
  reverse: `sigma` is `diag(1,-1)` and `tau` is the swap. The logical action
  depends on the encoding basis.
- **Not a standard named tool in the RH literature.** Relative phase gates and
  fermionic parity `(-1)^F` are standard in quantum information and
  supersymmetry. The specific name “phase-shift involution” is not a standard
  term of art. No novelty claim is made.

---

## 3. The I/Q counterpart

At a phase mismatch `phi` in the quadrature branch, the complex baseband
symbol `x = I + jQ` becomes

```text
y = I + j Q exp(j phi)
  = (I - Q sin phi) + j (Q cos phi).
```

In real vector form, acting on `(I, Q)^T`,

```text
R(phi) = [[1, -sin(phi)],
          [0,  cos(phi)]],
det R(phi) = cos(phi).
```

At `phi = pi`,

```text
R(pi) = [[1,  0],
         [0, -1]],
```

so `y = conjugate(x)`: the Q-axis reflection. It is an involution and
preserves energy. At `phi = pi/2` the matrix is rank one; the Q component is
lost and no inverse exists.

The common shorthand

```text
y = I + exp(j phi) Q
```

omits the `j` that makes `Q` the imaginary axis. At `phi = pi` it gives
`I - Q`, a rank-one projection, not a reflection.

If the two DSIN sectors are identified with the I and Q axes, then
`tau = diag(1,-1) = R(pi)`. This is the precise algebraic correspondence: the
same real `2 x 2` matrix. It is not an identity of the two models. On the
complex plane the I/Q map at `pi` is conjugation, which is anti-linear, while
DSIN's `tau` is complex-linear on `H_b + H_f`. The agreement is real-linear,
after a choice of real basis.

The logical effect depends on the encoding:

- **DSIN:** logical states are the `sigma` eigenstates `|+>, |->`. The matrix
  `diag(1,-1)` swaps them, so the logical bit flips with probability one.
- **Standard QPSK:** the four I/Q sign combinations are the symbols. The same
  matrix flips the Q bit only. Every symbol is mapped to a different symbol,
  so the symbol error rate is `1`, but the BER is `1/2`, not `1`.
- **A rotated BPSK pair:** if the two logical states are
  `(|I> +/- |Q>)/sqrt(2)`, the reflection swaps them and the single logical
  bit flips with probability one.

The matrix is the same; the code is not.

---

## 4. Why blindness is structural

Let `C` be a constellation with prior `p(c)`, and let `R(c) = conjugate(c)`.
Consider

```text
H0: y = c + n,
H1: y = R(c) + n,
```

with circular complex Gaussian noise. If `R(C) = C` and `p(R(c)) = p(c)` for
every `c`, then for every observation `y`,

```text
p(y | H0) = p(y | H1).
```

The proof is a change of variables `c' = R(c)` in the sum defining
`p(y | H1)`. The likelihood ratio is identically zero. No threshold, no
function of the constellation, and no amount of data can distinguish the two
hypotheses. For QPSK and square QAM with uniform data, the conditions hold.

This is the engineering counterpart of DSIN's parity-meter blindness. The
meter observes a statistic that is invariant under the phase flip; the phase
flip inverts the data while leaving the statistic unchanged. An invariant
observable cannot detect the transformation that preserves it.

A pilot, a known preamble, an asymmetric constellation or prior, or a code
constraint can break the tie. Gray mapping and cyclic-shift invariance of the
symbol set do not: they are symmetries, not syndromes.

---

## 5. The runnable counterpart

The sibling `modcode-lab` checkout contains the experiment:

```text
../../modcode-lab/docs/phase-shift-involution.md
../../modcode-lab/examples/phase_imbalance_lab.py
```

It implements `PhaseImbalanceChannel`, known-phase inversion,
`tau`-aware demodulation, the log-likelihood ratio, and a pilot-based
hypothesis test. At `phi = pi`:

| detector | BER (noiseless) |
|:---|:---:|
| standard coherent, assumes `phi=0` | `0.5000` |
| oracle, knows `phi=pi` | `0.0000` |
| pilot-assisted | `0.0000` |
| blind, tests `phi=0` vs `pi` | `0.5000` |

The blind detector fails because its LLR is zero, not because it is badly
tuned. The oracle and pilot recover because they have a reference that is not
invariant under the reflection.

The experiment also shows that `phi = pi/2` is the rank-collapse case, not
`phi = pi`. The determinant `cos(phi)` is zero at `pi/2` and `-1` at `pi`.

---

## 6. What this does not establish

- It does not connect the phase flip to the zeros of zeta.
- It does not make DSIN secure, nor does it repair the single-observable
  security problem documented in
  `docs/dimension_shift_quantum_communication.md` §4.1.
- It does not show that `tau` is a new mathematical object. It is a relative
  phase gate / fermionic parity phase, written in the DSIN notation.
- It does not claim that a blind I/Q receiver can recover the reflection. The
  blind case is the control that fails.
- It does not identify the DSIN model with a physical I/Q modulator. The
  correspondence is the real `2 x 2` matrix at `phi = pi`, after identifying
  sectors with I/Q axes, and it is basis-dependent.

The honest summary is narrow: the same real involution appears in two models,
and in both the invariant observable is blind to it. The engineering fix is a
reference or a code constraint; the mathematical lesson is that a symmetry of
the representation is not a symmetry of the zeros.

---

## References

- `docs/dimension_shift_quantum_communication.md` §3.4 and §4.1.
- `python/riemann_framework/dsin.py` (`apply_phase_noise`, `run_simulation`).
- `python/riemann_framework/dsin_sigma_symmetry.py` (sector bases and the
  parity meter).
- `modcode-lab/docs/phase-shift-involution.md` and
  `modcode-lab/examples/phase_imbalance_lab.py`.
