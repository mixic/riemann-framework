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
with a composable security proof. The purpose of this article is to define
the abstraction, identify possible experiments, and state the results that
would be required before making security claims.

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
current design rather than merely unproven: detection is a constant function of
the disturbance (see §3.4), so no error-rate-to-information relation can be
derived from it. The caution in the sentence above is also sharpened in the
opposite direction — it is not only that one must not claim *every* attack is
detected with certainty, but that some attacks are detected with probability
**zero**.

Meeting the requirement would need the receiver to test eigen*value* consistency,
which requires either a shared secret or a BB84-style basis-sampling check in
which Alice and Bob sacrifice a subset of bits to estimate the error rate. That
is a change to the protocol, not to the analysis.

### 4.2 Comparison with BB84

| Feature | BB84 | DSIN proposal |
|:---|:---|:---|
| Encoding | Polarization, phase, or another qubit basis | Eigenvalue of a sector involution |
| Security basis | Multiple incompatible bases | One proposed symmetry measurement, possibly with additional checks |
| Disturbance mechanism | No-cloning and basis mismatch | Sector mixing or loss of involution covariance |
| Main ideal condition | Qubit channel and measurement assumptions | `sigma`-compatible channel and accessible sector projectors |
| Security status | Established security proofs under explicit models | Conceptual proposal; no complete security proof |
| Experimental status | Mature implementations | No demonstrated DSIN implementation |

The comparison should not imply that a single DSIN observable automatically
provides the same security guarantees as BB84. A protocol needs a complete
security reduction, not only an invariant observable.

### 4.3 Supersymmetry and the Witten index

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
   disturbance. (**Answered, and the answer is yes.** The fermionic phase flip
   `diag(I, -I)` does not commute with `sigma`, inverts every transmitted bit,
   and leaves the detector silent: measured `BER = 1.0000`, detection `0.0000`.
   See §3.4.)

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
| Detection metric | A *graded* disturbance measure, so that detection probability scales with the disturbance instead of saturating at 1 (or reading 0) for any nonzero attack; see §3.4 |
| Eigenvalue consistency | A receiver test that distinguishes "an eigenstate" from "the eigenstate that was sent", without a shared secret — otherwise `diag(I, -I)` remains a total undetectable break |
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
a graded measure, and a non-commuting perturbation that merely swaps the
eigenvalues (`diag(I, -I)`) inverts every bit while leaving every detector
reading unchanged (§3.4). The honest summary is therefore that DSIN currently
possesses an exact commuting channel and no detection guarantee at all, which is
a weaker position than "a commuting Hamiltonian plus a disturbance observable"
would suggest.

The proposal shares a useful structural vocabulary with the Dimension-Shift
approach to the Riemann Hypothesis: involutions, fixed loci, sector structure,
and possible index or spectral constraints. The analogy is suggestive, but it
is not an implication between RH and cryptographic security.

The next step is an experiment with an explicit noise and attack model. A
successful DSIN protocol would require a complete security proof, a physical
implementation, and a comparison with established quantum-key-distribution
security definitions.

## References

- Bennett, C. H. and Brassard, G. (1984). *Quantum cryptography: Public key distribution and coin tossing*.
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
