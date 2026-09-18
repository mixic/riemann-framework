<!--
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
-->

# Dimension-Shift Involution for Quantum Communication Networks

> **Speculative research proposal:** DSIN is not a deployed cryptographic
> protocol and has no composable security proof. The simulation code is a toy
> model for exploring sector symmetry, noise, and disturbance.

## Abstract

Classical quantum communication networks encode information in quantum states
and transmit it through channels affected by decoherence, loss, and possible
eavesdropping. Security proofs for protocols such as BB84 rely on precise
quantum-mechanical facts, including the no-cloning theorem and the inability
to perfectly distinguish non-orthogonal states.

This article proposes a speculative alternative abstraction: a
**Dimension-Shift Involution Network (DSIN)**. Information is represented by
an eigenvalue or sector label of a `Z_2`-graded Hilbert space rather than by a
single physical coordinate of a qubit. The central operation is a discrete
involution `sigma` that exchanges two sectors. The `+1` and `-1` eigenspaces
are symmetric and antisymmetric channels.

The proposal is motivated by the same structural pattern used in the
Dimension-Shift approach to the Riemann Hypothesis: an involution, a fixed
locus, and a sector symmetry. It is not currently a cryptographic protocol
with a composable security proof, and the analysis below shows that its central
observable cannot support one: an adversary who measures that observable
directly learns every bit while producing exactly the readings of a noiseless
channel (§4.1), and the entropic-uncertainty route that would supply a bound is
unavailable to a design with a single published basis (§4.3). The purpose of
this article is to define the abstraction, identify possible experiments, and
state the results that would be required before making security claims.

## 1. Motivation

### 1.1 Limits of qubit-based communication

Quantum communication is affected by several practical and structural issues:

| Limitation | Consequence |
|:---|:---|
| Decoherence | Quantum coherence degrades over distance and time |
| Loss | Photons may be absorbed or scattered in a channel |
| Detector vulnerabilities | Measurement devices can introduce side channels |
| Trusted nodes | Long-distance repeaters may require additional trust assumptions |
| Key-rate bounds | Information transmission is limited by channel capacity and noise |

These problems cannot be removed merely by changing notation. Any DSIN
implementation would still be a physical quantum system and would have to
model noise, loss, finite temperature, measurement error, and device attacks.

### 1.2 The Dimension-Shift alternative

The proposed abstraction asks:

> What if information were encoded in the sector or symmetry label of a state,
rather than in one continuously varying state coordinate?

The DSIN idea has three ingredients:

1. information is encoded in an eigenspace of a sector involution;
2. transmission is governed by a Hamiltonian or channel compatible with that
   involution;
3. an operation that changes the sector symmetry may be detected by measuring
   the involution observable.

The third point is a hypothesis. A measurement that does not commute with the
involution can disturb the encoded state, but the resulting error probability
must be calculated for a specified attack and physical channel.

## 2. Mathematical Framework

### 2.1 A graded Hilbert space

Let the state space be a `Z_2`-graded Hilbert space

```text
H = H_b direct_sum H_f,
```

where `H_b` is the bosonic sector and `H_f` is the fermionic sector. A pure
state belonging entirely to one sector has a parity label, but a general
state can be a superposition of both sectors.

### 2.2 The sector-swapping involution

For matched basis states, define

```text
sigma |b, k> = |f, k>,
sigma |f, k> = |b, k>.
```

The finite matrix representation is

```text
sigma = [[0, I],
         [I, 0]],
```

where `I` is the identity on one sector. It has the properties

```text
sigma^2 = I,
sigma^dagger = sigma,
sigma^dagger sigma = I.
```

Thus its eigenvalues are `+1` and `-1`. The corresponding eigenspaces are

```text
|psi_plus>  = (|b, k> + |f, k>) / sqrt(2),
|psi_minus> = (|b, k> - |f, k>) / sqrt(2).
```

The `+1` eigenspace is the fixed subspace `Fix(sigma)`. The `-1` eigenspace
is the antisymmetric subspace.

### 2.3 The channel Hamiltonian

A two-sector Hamiltonian can be written as

```text
H = [[H_b, V],
     [V^dagger, H_f]],
```

where `V` couples the sectors. Exact preservation of the involution requires
an appropriate commutation relation:

```text
[H, sigma] = 0.
```

When this holds, the Hamiltonian preserves the `+1` and `-1` eigenspaces, so
an eigenvalue label of `sigma` is conserved during ideal closed-system
evolution.

This is a symmetry-protection statement, not automatically a topological
protection statement. Topological protection requires additional global
structure, such as a phase invariant, a gap, and robustness under a specified
class of perturbations.

## 3. The DSIN Protocol

### 3.1 Encoding

A sender encodes a classical bit in the eigenvalue of `sigma`:

```text
bit 0 -> |psi_0> = (|b, k> + |f, k>) / sqrt(2),  sigma|psi_0> = +|psi_0>,
bit 1 -> |psi_1> = (|b, k> - |f, k>) / sqrt(2),  sigma|psi_1> = -|psi_1>.
```

The states are orthogonal for matched normalized sector states. A concrete
implementation must specify how the sector states are prepared, how `k` is
chosen, and how the sender and receiver share the required reference frame.

Encoding a bit only in a sector label is not sufficient by itself. If the
receiver cannot coherently access both sectors, the relative phase that
defines the `+1` and `-1` states may be inaccessible.

### 3.2 Transmission

If the channel evolution is generated by a Hamiltonian satisfying
`[H, sigma] = 0`, then

```text
sigma exp(-i H t) |psi_b>
  = (-1)^b exp(-i H t) |psi_b>.
```

The ideal encoded eigenvalue is therefore conserved. In an open system, this
condition must be replaced by a statement about the quantum channel `E`, for
example covariance under the involution:

```text
E(sigma rho sigma^dagger)
  = sigma E(rho) sigma^dagger.
```

Channel covariance alone does not guarantee a noiseless bit channel. It only
states that the noise respects the symmetry. The channel's error rate and
capacity still need to be computed.

### 3.3 Decoding

The receiver measures the observable associated with the sector involution.
In the ideal model, the projectors are

```text
P_plus  = (I + sigma) / 2,
P_minus = (I - sigma) / 2.
```

The measurement outcome identifies the encoded bit without requiring full
state tomography. In a physical system, implementing these projectors may be
as difficult as measuring the original qubit basis, so the hardware cost must
be included in any comparison.

### 3.4 Eavesdropping and disturbance

Suppose an adversary applies an operation or measurement that does not commute
with `sigma`. It may mix the two eigenspaces and create decoding errors. For
an attack represented by a channel `A`, the relevant question is whether

```text
A(P_plus rho P_plus) and A(P_minus rho P_minus)
```

remain distinguishable at the receiver.

The statement "non-commuting means a random result" is too strong in general.
The outcome distribution depends on the attack, the input state, the channel
noise, and the receiver's measurement. A valid security analysis must bound
the information gained by the adversary as a function of the observed error
rate.

**Measured status.** `dsin.py` now supplies the numbers, and they run against the
hoped-for picture. Two findings from `scripts/run_dsin_verification.py`
(`n = 500`, seed 42):

- The detector is **binary, not graded**. It tests whether the received state is
  *an* eigenstate of `sigma` (`|<sigma>| = 1`), so any departure from the
  eigenspace trips it at full strength. The symmetry-breaking sweep reports a
  detection rate of `1.0000` at every attack strength, from `eps = 0.1` to
  `eps = 1.0`, while only the BER responds to `eps` (`0.010 -> 0.260 -> 0.404`).
  A cautious eavesdropper is therefore caught with the same probability as a
  reckless one, and the relation between error rate and leaked information
  **degenerates to a constant**.
- An attack exists that is **non-commuting and completely undetectable**. The
  fermionic phase flip `diag(I, -I)` does not commute with `sigma`, yet it maps
  the `+1` eigenspace onto the `-1` eigenspace. The received state is still a
  `sigma` eigenstate, of the *opposite* eigenvalue, so `|<sigma>| = 1`,
  detection stays at `0.0000`, and every bit is inverted (measured
  `BER = 1.0000`). See the `phi = pi` row of the phase-noise sweep.
- **Neither flat detection figure is a calibrated probability, and the detector
  is unchanged.** An earlier revision of `symmetry_breaking_attack` reported a
  flat `≈ 0.53`; that figure measured the fraction of rounds whose state the
  attack could disturb at all — not a detection capability — because the
  perturbation it applied lay inside the `-1` eigenspace and left bit-1 states
  untouched. Correcting the attack gives a flat `1.0000`, which records only that
  the alarm is binary. Detection probability is a step function of attack
  strength in both cases, so this correction is not progress on §4.1; it is the
  same gap measured correctly.
- **The flatness is a thresholding artefact, and removing it does not help.** The
  graded statistic behind the detector — the mean deviation
  `|1 - |<sigma>||`, which is the detector's input before thresholding and is now
  the `mean_sigma_deviation` field of `SimulationResult` — is smooth and monotone
  in the attack strength:

  | attack | mean `\|1 - \|<sigma>\|\|` | thresholded detection |
  |:---|:---|:---|
  | symmetry-breaking `eps = 0.05` | 0.0100 | 1.0000 |
  | `eps = 0.1` | 0.0389 | 1.0000 |
  | `eps = 0.3` | 0.2739 | 1.0000 |
  | `eps = 0.5` | 0.5083 | 1.0000 |
  | `eps = 1.0` | 0.6958 | 1.0000 |

  (`n = 1000`, seed 42; pinned by
  `test_mean_sigma_deviation_is_graded_where_detection_is_a_step`.) So the step
  function comes from the `> 1e-6` threshold, not from an uninformative
  observable, and a *graded* detector is one line away.

  It would not help. Grading the detector changes where the alarm trips; it does
  not change what the statistic *says*, and the statistic is **non-monotone in
  damage**. Three channels, measured on the same `n = 1000`, seed 42 run:

  | channel | mean `\|1 - \|<sigma>\|\|` | detection | BER |
  |:---|:---|:---|:---|
  | no eavesdropper | `2.22e-16` | 0.0000 | 0.0000 |
  | `sigma`-basis measurement (§4.1) | `2.22e-16` | 0.0000 | 0.0000 |
  | phase flip at `phi = pi` | `2.22e-16` | 0.0000 | **1.0000** |

  The second and third rows are adversarial and the first is not, yet all three
  are the same point of the statistic. The phase flip inverts every bit while
  reporting a perfectly undisturbed channel; the `sigma`-basis measurement
  extracts every bit while reporting the same. No function of this observable
  can bound the adversary's information, so the obstruction is not its
  quantization but its invalidity as a security statistic. The BER does witness
  the break, which is why §4.1 points there.

  One floating-point detail is worth recording, because it is a real defect and
  not cosmetic: `1 - |<sigma>|` is *negative* for the ideal channel
  (`-2.22e-16`), since `|<sigma>|` rounds a few ulps above 1. The field therefore
  stores `|1 - |<sigma>||`, which agrees with the intuitive form for every
  physical state (`|<sigma>| <= 1`) and matches the expression the detector
  thresholds, so the two cannot drift apart.

## 4. Security Analysis Requirements

### 4.1 A no-shift statement

A possible informal claim is:

> If the ideal channel preserves `sigma` and an adversarial operation changes
> the `sigma` eigenspace, then the receiver may observe a nonzero bit-error
> rate.

To turn this into a theorem, one must specify:

- the state preparation and measurement model;
- the adversary's allowed operations and ancillas;
- whether the adversary has access to both sectors;
- the noise and loss model;
- the error observable and statistical test;
- the relation between error rate and leaked information.

A proof must not claim that every non-commuting attack gives the same error or
that every attack is detected with certainty.

**Status of the sixth requirement.** It is now known to be unsatisfiable in the
current design rather than merely unproven, and for a sharper reason than "the
detector is binary". The graded statistic behind the detector is smooth and
monotone in attack strength (§3.4), so its apparent flatness is an artefact of
thresholding. What defeats the requirement is that the statistic is
**non-monotone in damage**: it reads the same value as an undisturbed channel
both under `diag(I, -I)`, which inverts every bit, and under a `sigma`-basis
measurement, which recovers every bit. An observable that reports a perfectly
undisturbed channel under a total break cannot bound the adversary's information
at any resolution.

The obstruction can be stated exactly.

> **Proposition (no `sigma`-based security bound).** Let `rho_b` be the encoding
> of bit `b`, let `A` be any eavesdropping strategy, let `A(rho_b)` be the state
> that reaches Bob, and put `dev(A) = mean_b |1 - |<sigma>|` on that state. Let
> `I(A)` be the mutual information between `b` and the adversary's record. Then
> there is no function `f` with `I(A) <= f(dev(A))` for all `A`.
>
> *Proof.* Take `A_id` to be the identity: `dev = 0` and `I = 0`. Take `A_meas`
> to be the projective measurement of `sigma` followed by resending the
> post-measurement state. Since `rho_b` is a `sigma` eigenstate of eigenvalue
> `(-1)^b`, the Born rule makes the outcome `b` with probability 1, so `I = 1`
> bit; and the post-measurement state of a state already in the measured
> eigenspace is that state, so `dev = 0` as well. Equal deviation, different
> leakage. ∎

Both halves are implemented (`dsin.py`,
`sigma_basis_intercept_attack`) and measured: `BER = 0.0000`, detection
`0.0000`, adversarial outcome equal to the transmitted bit `1.0000` of the time,
and a deviation bit-identical to the no-eavesdropper run. The caution in the
informal claim above is sharpened in the opposite direction too — it is not only
that one must not claim *every* attack is detected with certainty, but that some
attacks are detected with probability **zero** while being maximally
informative.

Meeting the requirement would need the receiver to test eigen*value* consistency,
which requires either a shared secret or a BB84-style basis-sampling check in
which Alice and Bob sacrifice a subset of bits to estimate the error rate. That
is a change to the protocol, not to the analysis, and §4.3 explains why a change
of that kind is not a matter of adding a check: it is the difference between
having one observable and having two.

It is worth being precise about where the gap lies, because the graded statistic
a security argument would use already exists. The BER *is* continuous in attack
strength — `0.010 -> 0.260 -> 0.404` over `eps = 0.1 -> 1.0` at `n = 500` — and
the BER is what BB84 thresholds. Two things are nevertheless missing. First, a
parameter-estimation step: the simulator can report the BER because it knows the
transmitted bits, but the protocol gives Alice and Bob no way to estimate it, so
the number exists in the analysis and not in the protocol. Second, any bound
relating that BER to the adversary's information.

The binary `sigma` check cannot substitute for either. It is an early-warning
witness that costs no sacrificed bits, and it can be fooled completely — a
zero-cost warning that is sometimes exactly wrong. The gap is therefore
structural, in the protocol, rather than merely a missing continuous observable.

### 4.2 Comparison with BB84

| Feature | BB84 | DSIN proposal |
|:---|:---|:---|
| Encoding | Polarization, phase, or another qubit basis | Eigenvalue of a sector involution |
| Security basis | Multiple incompatible bases | One proposed symmetry measurement, possibly with additional checks |
| Conjugate observable for an uncertainty relation | `X`, mutually unbiased with `Z` (`c = 1/2`) | None available; the `sigma` eigenbasis has overlap `1` with itself (`c = 1`) |
| Cost to the adversary of measuring in the right basis | A wrong basis guess half the time | Zero: the encoding basis is published (§4.3) |
| Disturbance mechanism | No-cloning and basis mismatch | Sector mixing or loss of involution covariance |
| Main ideal condition | Qubit channel and measurement assumptions | `sigma`-compatible channel and accessible sector projectors |
| Security status | Established security proofs under explicit models | Conceptual proposal; no complete security proof, and §4.1 shows the proposal's own statistic cannot carry one |
| Experimental status | Mature implementations | No demonstrated DSIN implementation |

The comparison should not imply that a single DSIN observable automatically
provides the same security guarantees as BB84. A protocol needs a complete
security reduction, not only an invariant observable.

### 4.3 Entropic uncertainty relations and why one observable is not enough

This section answers a specific question: can the symmetry-breaking observable be
turned into an actual theorem — an entropic uncertainty relation, or some other
bound relating the observable to the adversary's information — of the kind that
makes BB84's security proof work? The answer has two halves, and they point in
opposite directions.

**For the design as specified, no — and the impossibility is the theorem.** §4.1
proves that no function of the `sigma` deviation bounds the adversary's
information. That is not a failure to find the right inequality; it is a
statement that the quantity to be bounded is unbounded while the statistic reads
exactly zero, witnessed by an explicit attack that is maximally informative and
perfectly invisible.

**Why the standard route cannot even be set up.** The Berta–Christandl–Colbeck
uncertainty relation, the tool behind modern QKD security arguments, has the form

```text
H(Z | E) + H(X | B) >= log2(1/c) + H(A | B),      c = max_{z,x} |<z|x>|^2,
```

for two measurements `Z` and `X` on the same system. Its entire quantitative
content sits in the `log2(1/c)` term, and that term measures *how incompatible
the two measurements are*. When the two measurements coincide, `c = 1` and
`log2(1/c) = 0`; and measuring `Z` is then noiseless in its own eigenbasis, so
`H(Z | B) = H(A | B)` and the inequality reduces to the vacuous `H(Z | E) >= 0`.
That is the single-observable case, and it bounds nothing: nothing forces the
adversary to be uncertain, because she can perform exactly the measurement the
legitimate receiver performs. Adding a check, a threshold, or a graded statistic
does not change `c`.

The point is easiest to see next to BB84. BB84's immunity to the
measurement-in-the-encoding-basis attack is not a property of `Z`; it is a
property of the *pair* `{Z, X}` together with Alice's private choice between
them. An adversary who measures `Z` is correct on half the rounds and destroys
the other half. In DSIN the encoding basis is fixed and public, so her
measurement is correct on every round, and §4.1's attack exploits exactly that.

**What the repair would cost.** A pair of mutually unbiased bases does exist in
the DSIN sector: the `sigma` eigenbasis `{|b,k> +- |f,k>}/sqrt(2)` and the sector
basis `{|b,k>, |f,k>}` have overlap

```text
|<b,k| (|b,k> + |f,k>)/sqrt(2)>|^2 = 1/2,
```

so `c = 1/2` and `log2(1/c) = 1` bit: a non-degenerate uncertainty relation, and
a protocol with a genuine BB84-shaped security argument. But each 2-dimensional
sector block, spanned by `{|b,k>, |f,k>}`, then carries exactly one qubit and
exactly one unbiased pair — that pair *is* BB84's `{Z, X}` up to relabelling. The
involution supplies names for the two bases; it does not supply a third
incompatibility, a larger key space per round, or a cheaper disturbance
mechanism. So the entropic route is available, but what it proves is BB84's
theorem about BB84's structure, with the sector labels as notation.

This is a negative result about the observable, not about the wider programme.
It is recorded here because "the detector did not fire" and "the adversary
learned nothing" are different statements, and the DSIN proposal currently
conflates them.

### 4.4 Design requirements for a viable protocol

> **Status: this section states requirements, not results.** Its only measured
> content is a *negative* fact — that the most natural repair relocates the
> obstruction of §4.1 instead of removing it — together with one small existence
> check that keeps direction (b) from being vacuous. Nothing here is a security
> claim, nothing here is evidence that a working protocol exists, and no part of
> it should be cited as support for the DSIN proposal. It is recorded so that the
> next attempt does not have to rediscover the obstruction, and so that any
> future claim can be checked against an explicit list.

#### 4.4.1 Why the obstruction relocates

Section 4.1 shows that no function of the `sigma` deviation can bound leakage,
because the adversary can measure `sigma` itself. The natural repair is to stop
encoding the payload in the `sigma` *eigenvalue* and encode it in the interior of
`Fix(sigma)` instead. There is room: `dim Fix(sigma) = d`, and the encoding
`|b,k> +- |f,k>` used only a one-dimensional slice of it. Write the encoded state
as `|+>_sector (x) v`, with `v` any state of `C^d`. The offset half works, and
the measurements confirm it:

| probe (`d = 4`) | `<sigma>` |
|:---|:---|
| arbitrary interior states of `Fix(sigma)` | `+1.000000000000000` |
| after the phase flip `diag(I, -I)` | `-1.000000000000000` |
| after the adversary measures the k-index | `+1.000000000000000` |

The second row is real progress. Because every legitimate state now lies in
`Fix(sigma)` rather than in `Fix(sigma) u Anti(sigma)`, the receiver can test
`<sigma> = +1` instead of `|<sigma>| = 1`, and the phase flip — invisible under the
old test, and a total break — is caught. The first row says the adversary's
`sigma` measurement has become harmless: a stabilizer measurement returns the
syndrome, every codeword has the same syndrome, so it reveals nothing about `v`.

The third row is the obstruction, and it is not a detail of this encoding.

> **Observation (relocation).** Let `W` be the payload subspace and `O` the
> observable the legitimate receiver uses to read the payload. If `O` is
> available to the adversary and its eigenbasis contains a basis of `W`, then
> measuring `O` reveals the payload and maps `W` into `W`. So if `W` is a fixed
> subspace, the post-measurement state stays inside it, and every stabilizer of
> `W` — hence every function of its syndrome — is unchanged.
>
> *Proof.* Write the state as a superposition of the basis of `W` contained in
> `O`'s eigenbasis; the projective measurement collapses it onto one of those
> vectors, which lies in `W`. ∎

In coding language: a stabilizer detects errors that move the state *out* of the
code space, and the adversary's payload measurement is a **logical operator** — it
acts within the code space and commutes with every stabilizer by definition.
Detecting it would require a stabilizer to distinguish two states of the same code
space, which is what "same code space" forbids. A code that is fixed and public is
therefore transparent to the one operation that decides the question.

This also explains a pattern worth naming, because it recurred several times while
this track was being worked on: repairs to this design did not fail so much as
*relocate*. That was not a run of bad luck. It was the observation above asserting
itself.

#### 4.4.2 The requirements

Any design in this track has to meet all four.

| | Requirement | Why |
|:---|:---|:---|
| R1 | The encoding is drawn per round from a set, and the adversary cannot know the choice before the state arrives | Otherwise R2 has nothing to bite on, and §4.1 applies verbatim |
| R2 | A wrong guess must be detectable: the candidate encodings must overlap by a constant amount, so measuring the wrong one disturbs | This is the MUB condition, and it is the whole content of BB84 |
| R3 | The choice is announced after the fact, and costs no key material | So that R1 is free; this is sifting |
| R4 | The receiver has an information-free check | The one thing this construction actually supplies |

R1–R3 are BB84's content under different words, and no relabelling removes them.
If a design meets them by choosing among mutually unbiased bases of a
`d`-dimensional system, it *is* high-dimensional QKD, and its security rests on
the high-dimensional uncertainty relation (`c = 1/d`, hence `log2 d` bits) rather
than on anything specific to sectors. What the involution can then add is R4: a
syndrome that costs no sacrificed rounds. That makes the involution a **code**,
not a **cipher**.

#### 4.4.3 Direction (b): let the involution be the per-round choice

This is the only variant found so far in which the symmetry does cryptographic
work rather than supplying names for a basis.

Work with *reflections* rather than sector swaps. For any `d`-dimensional subspace
`F` of a `2d`-dimensional space, `sigma_F = 2 P_F - I` is a Hermitian involution
with `Fix(sigma_F) = F`, so the family of candidate involutions is exactly the
family of `d`-dimensional subspaces. Two such subspaces are **unbiased** when
`|<psi|phi>|^2 = 1/(2d)` for all unit `psi` in `F` and `phi` in `F'`. Alice draws
`F` privately, prepares inside it, and transmits; Bob draws `F'` and measures;
they sift on `F = F'` and announce the choice only for the rounds they keep, so R3
holds and the randomness is free.

This is not vacuous. At `d = 1` it reproduces the ordinary MUB condition in
dimension 2 (`1/(2d) = 1/2`, with `|0>` and `|+>`), which is BB84 — consistent
with §4.3. And at `d = 2` a pair of unbiased 2-dimensional subspaces of `C^4`
exists:

```text
F  = span{e1, e2}
F' = span{(e1 + e2 + e3 + e4)/2, (e1 - e2 + e3 - e4)/2}

all four cross overlaps:  0.25  =  1/(2d)
```

Both reflections are Hermitian, square to the identity, and evaluate to `+1` on
their own fixed locus. So direction (b) is a definite object rather than a hope.

**What is not established** — and this is the first thing anyone pursuing it
should determine — is how large such a family can be. The size of the family is
the size of the randomness budget `R1` draws on, so it sets how much the sifting
step costs, and nothing in this document says whether a family of more than two
unbiased subspaces exists for any `d >= 2`. Until that is settled, direction (b)
is a well-posed question and not a design.

#### 4.4.4 Direction (c): let the frame itself be the secret

The alternative is that the sector decomposition — the involution, not merely the
basis — is unknown to the adversary, and the payload is carried in sector-relative
structure that is meaningful only to someone holding the frame. This is the only
version in which the *symmetry* rather than the per-round randomness is the
secret, and it connects to the established literature on quantum communication
with limited reference frames (Bartlett, Rudolph and Spekkens).

It is also the hardest, and the difficulty is structural rather than technical.
The states are prepared *in* the frame, so they carry information about it, and an
adversary with many rounds can estimate it — the standard frame-alignment attack.
Making this work requires showing either that any frame estimate good enough to
read the payload also produces a disturbance large enough to detect, or that the
payload is invariant under the frame information the transmitted states leak.
Neither is obvious, and no argument for either is offered here. This direction
should be treated as a question, not a plan.

#### 4.4.5 The experiment that would settle direction (b)

Direction (b) reduces to a comparison of key rates under matched noise:

1. high-dimensional QKD in dimension `d`, using the `d+1` mutually unbiased bases
   that exist when `d` is a prime power;
2. the same protocol with the `sigma` syndrome available to the receiver as a
   herald.

If the herald does not improve the key rate, direction (b) *is* high-dimensional
QKD and the sector structure is decoration. That is a falsifiable question about a
design rather than about the current one, it can be answered with the existing
harness, and it is the cheapest way to find out whether this track has anything
left in it.

#### 4.4.6 What would remain true even if direction (b) worked

Even a successful direction (b) would leave the Riemann Hypothesis analogy where
§5.1 already places it. The construction's one provable statement is that a
`sigma`-commuting channel preserves `Fix(sigma)` — the trivial direction of the
implication. The content of RH is that *everything* lies on the fixed locus, which
is the open direction. The shared structure lives on the easy side on both sides
at once, and nothing in this section changes that.

### 4.5 Supersymmetry and the Witten index

If the Hamiltonian has a supercharge `Q`, a supersymmetric construction may
have the form

```text
H = {Q, Q^dagger}.
```

A Witten index can be defined under suitable analytical conditions as a
difference of zero-mode counts. In the repository's finite numerical model,
`witten_index` simply counts eigenvalues close to zero in two matrices.
That diagnostic is not a proof that a physical system is supersymmetric or
that its index is topologically invariant.

Continuous perturbations preserve an index only when the required operator
domains, spectral gap, and boundary conditions are controlled. Those
conditions must be established before using the index as a security claim.

## 5. Connection to the Riemann Hypothesis

### 5.1 Shared structural pattern

| Structure | Dimension-Shift RH model | DSIN model |
|:---|:---|:---|
| Involution | Functional-equation reflection and conjugate reflection | Sector swap `sigma` |
| Fixed locus | Critical line `Re(s) = 1/2` | `+1` eigenspace `Fix(sigma)` |
| Sector structure | Spectral or arithmetic sectors | Bosonic and fermionic sectors |
| Positivity/index idea | Weil positivity or spectral reality | Channel invariants and possible Witten index |
| Statistics | GUE-like zero spacings | Candidate sector-coupled spectra |

The shared pattern is a useful source of hypotheses. It is not a proof that
security of one system implies RH, or that a proof of RH would automatically
secure a communication protocol.

### 5.2 The deeper connection

Both proposals ask whether a discrete symmetry can make a preferred subspace
structurally stable rather than accidental. In the RH setting, the desired
conclusion concerns the location of all non-trivial zeros. In DSIN, the
conclusion concerns preservation and detectability of a communication label.

The analogy becomes mathematically meaningful only if both sides supply their
missing forcing or robustness theorem:

- RH needs a theorem excluding zeros outside the critical line;
- DSIN needs a composable security theorem against an explicit attack model.

## 6. Possible Experimental Realizations

| Candidate platform | Sector candidates | Coupling or control |
|:---|:---|:---|
| Superconducting circuits | Distinct mode or excitation sectors | Microwave control and tunable couplers |
| Trapped ions | Motional and internal-state sectors | Laser coupling |
| Photonic lattices | Even and odd modes | Waveguide coupling |
| Topological materials | Edge and bulk sectors | Surface or interface coupling |
| Cold atoms | Band or spin sectors | Raman transitions |

The first experiment should not attempt a full cryptographic claim. It should
measure:

1. whether the sector-swap observable can be prepared and measured;
2. whether the implemented channel approximately commutes with `sigma`;
3. how decoherence and loss change the `sigma`-error rate;
4. whether controlled non-commuting perturbations are detected;
5. whether an adversary can gain information without producing a detectable
   disturbance. (**Answered, and the answer is yes, twice.** The fermionic phase
   flip `diag(I, -I)` does not commute with `sigma`, inverts every transmitted
   bit, and leaves the detector silent: measured `BER = 1.0000`, detection
   `0.0000` (§3.4). More sharply, an adversary who measures `sigma` — the
   receiver's own observable — recovers every bit, with `BER = 0.0000` and
   detection `0.0000`, because the encoding basis is public (§4.1). The second
   attack is the one that rules out a security bound.)

## 7. Open Problems

| Problem | Required result |
|:---|:---|
| Channel capacity | Capacity and error correction for a noisy DSIN channel |
| Noise model | A physical model for dephasing, loss, and sector leakage |
| Attack model | Security bounds against general quantum operations and ancillas |
| Authentication | A method for authenticating the involution reference and measurement |
| Multi-party protocols | Extension to entanglement distribution and network routing |
| Experimental realization | A platform with controllable sectors and reliable projectors |
| Topological protection | A genuine invariant and gap, not only a commuting Hamiltonian |
| Detection metric | **Supplied, and shown insufficient.** `mean_sigma_deviation` is the graded statistic the row used to ask for, and grading the detector changes nothing that matters: the statistic is non-monotone in damage and cannot bound leakage (§3.4, §4.1). The open problem is a *valid* statistic, not a graded one |
| Eigenvalue consistency | A receiver test that distinguishes "an eigenstate" from "the eigenstate that was sent", without a shared secret — otherwise `diag(I, -I)` remains a total undetectable break |
| Uncertainty relation | A second observable mutually unbiased with `sigma`, so that an entropic uncertainty relation has a non-degenerate `log2(1/c)` term. §4.3 shows the natural candidate exists (the sector basis, `c = 1/2`) but makes the protocol BB84 in a 2-dimensional block, so it supplies no DSIN-specific security |
| Parameter estimation | A protocol-level way for Alice and Bob to estimate the error rate without the simulator's knowledge of the transmitted bits (§4.1) |
| Encoding randomness (R1–R3) | A per-round encoding choice the adversary cannot guess, detectable when guessed wrong, and announced after the fact at no cost in key material. §4.4.2 argues this is BB84's content under other words, and that no relabelling removes it |
| Unbiased involution families | How many pairwise-unbiased `d`-dimensional fixed loci exist in `2d` dimensions. Existence at `d = 2` is verified; the family size is the randomness budget R1 draws on, and it is unknown (§4.4.3) |
| Secret frame | Whether a sector frame can stay secret when the transmitted states are prepared in it — the standard frame-alignment problem, and the only direction in which the symmetry rather than the per-round randomness is the secret (§4.4.4) |
| RH connection | A precise theorem relating the two mathematical structures |

## 8. Conclusion

The Dimension-Shift Involution Network is a speculative abstraction for
quantum communication. It replaces ordinary basis encoding with an eigenvalue
of a discrete sector-swap symmetry. In the ideal closed-system model, a
Hamiltonian commuting with the involution preserves that label, and
non-commuting perturbations can create a measurable disturbance.

They need not, however, and the simulation now shows both halves of that
distinction. The commuting channel is exact — `||[H, sigma]||_F = 0.00e+00` at
machine precision for every dimension tested — so the one provable statement in
this track holds. But the detector is a witness of symmetry breaking rather than
a security statistic, and it fails in both directions at once: a non-commuting
perturbation that merely swaps the eigenvalues (`diag(I, -I)`) inverts every bit
while leaving every detector reading unchanged, and an adversary who simply
measures `sigma` — the receiver's own observable, in the published encoding basis
— recovers every bit with no disturbance and no alarm at all (§3.4, §4.1). No
function of the detector's statistic can bound that adversary's information, and
the entropic-uncertainty route that would supply such a bound is unavailable to a
single-observable design (§4.3). The honest summary is therefore that DSIN
currently possesses an exact commuting channel and no detection guarantee at all,
which is a weaker position than "a commuting Hamiltonian plus a disturbance
observable" would suggest. Section 4.4 converts that verdict into a requirements
list for any successor, and records two directions that are at least well-posed —
but it states requirements rather than results, and claims no security.

The proposal shares a useful structural vocabulary with the Dimension-Shift
approach to the Riemann Hypothesis: involutions, fixed loci, sector structure,
and possible index or spectral constraints. The analogy is suggestive, but it
is not an implication between RH and cryptographic security.

A successful DSIN protocol would require a complete security proof, a physical
implementation, and a comparison with established quantum-key-distribution
security definitions. As the design stands, the ordering has to be reversed: one
of the requirements in §4.4.2 must be met by a concrete construction before a
security proof is even well-posed, and §4.4.5 gives the experiment that would
settle whether the more promising of the two directions is anything beyond
high-dimensional QKD under other names.

## References

- Bennett, C. H. and Brassard, G. (1984). *Quantum cryptography: Public key distribution and coin tossing*.
- Berta, M., Christandl, M., Colbeck, R., Renes, J. M., and Renner, R. (2010). *The uncertainty principle in the presence of quantum memory*. Nature Physics.
- Cerf, N. J., Bourennane, M., Karlsson, A., and Gisin, N. (2002). *Security of quantum key distribution using d-level systems*. Physical Review Letters.
- Bartlett, S. D., Rudolph, T., and Spekkens, R. W. (2007). *Reference frames, superselection rules, and quantum information*. Reviews of Modern Physics.
- Witten, E. (1981). *Dynamical breaking of supersymmetry*. Nuclear Physics B.
- Montgomery, H. L. (1973). *The pair correlation of zeros of the zeta function*.
- Connes, A. (1999). *Trace formula in noncommutative geometry and the zeros of the Riemann zeta function*.
- Clay Mathematics Institute. *Millennium Problems: Riemann Hypothesis*.

## Disclaimer

This article is a speculative research proposal, not a proof of security or a
working cryptographic protocol. The DSIN construction, its physical
realization, and its connection to the Riemann Hypothesis remain unproven.
No claim is made that the Riemann Hypothesis has been proved or that DSIN
currently provides security equivalent to BB84.
