# The BB84 Implementation Layer

## Abstract

`bb84.py` models the BB84 *protocol*: one photon per round, a perfect source, a
perfect detector. That protocol has been secure since Mayers (1996) and
Shor-Preskill (2000), and no abstract attack will break it. The breaks that
happened in practice happened one layer down, in hardware:

- **photon-number splitting** on weak laser pulses;
- **detector blinding** (Lydersen et al. 2010), which broke commercial systems;
- timing side channels and Trojan-horse attacks on the source;
- **finite-key statistics** — the asymptotic analysis assumes infinitely many rounds.

This article documents `bb84_implementation.py`, which models the first of those
together with the source and detector physics it needs. The other three are named
below with what each would require, and are **not** implemented.

Nothing here is a security proof for or against any deployed system. It is the
standard photon-number-splitting accounting, written down so the numbers can be
checked.

## 1. What is modelled

### 1.1 The source is not a single photon

A weak coherent pulse has a Poisson photon number,

```text
p_n = e^{-mu} mu^n / n!,
```

so at `mu = 0.5` a real source is **61% vacuum, 30% single-photon, 9%
multi-photon**. The multi-photon fraction is

```text
P(n >= 2) = 1 - e^{-mu}(1 + mu),
```

and it is the resource PNS feeds on. It is small at usable `mu` and nowhere near
zero, which is the whole difficulty: lowering `mu` to suppress it also suppresses
the single-photon pulses that carry the key.

| `mu` | vacuum | single | multi |
|:---|:---|:---|:---|
| 0.1 | 0.9048 | 0.0905 | 0.0047 |
| 0.5 | 0.6065 | 0.3033 | 0.0902 |
| 1.0 | 0.3679 | 0.3679 | 0.2642 |

### 1.2 Detectors, gain and error rate

With `Y_0 = 1 - (1 - p_dark)^2` the dark-count yield of a two-detector receiver
and `eta` the end-to-end transmittance,

```text
Y_n       = 1 - (1 - Y_0)(1 - eta)^n          (yield of an n-photon pulse)
Q_mu      = 1 - (1 - Y_0) e^{-eta mu}         (gain)
Q_mu E_mu = e_0 Y_0 + e_det (Q_mu - Y_0)      (error rate)
```

with `e_0 = 1/2` for dark counts and `e_det` the misalignment error. The exact
`Y_0` rather than `2 p_dark` is what makes the `mu -> 0` limit *equal* to `Y_0`
instead of approximately so; the tests use that limit as a check, and
`test_closed_form_gain_matches_the_explicit_poisson_sum` recomputes `Q_mu` by
summing `p_n Y_n` directly, which is a different computation from the closed form
and so agrees as evidence rather than as a tautology.

### 1.3 Photon-number splitting

Eve measures the photon number without disturbing it — a quantum non-demolition
measurement; in practice she exploits loss and beam splitting. On a pulse with
`n >= 2` she keeps one photon and forwards the rest. On `n = 1` she forwards the
pulse and learns nothing. Because she holds a copy, she learns the bit with
certainty once the basis is announced during sifting, and because the photons she
forwards are the state Alice prepared, she introduces **no errors at all**.

Her information on the sifted key is therefore the fraction of detections that came
from multi-photon pulses, `f = Q_multi / Q_mu`:

| `mu` | `Q_mu` | `E_mu` | Eve holds |
|:---|:---|:---|:---|
| 0.1 | 0.009952 | 0.010098 | 0.0906 |
| 0.5 | 0.048772 | 0.010020 | 0.3782 |
| 1.0 | 0.095164 | 0.010010 | 0.6134 |
| 2.0 | 0.181271 | 0.010005 | 0.8507 |
| 5.0 | 0.393471 | 0.010002 | 0.9914 |

(`eta = 0.1`, `e_det = 0.01`, `p_dark = 1e-6`.) **The error rate is flat at
`e_det` across the whole sweep while Eve's information climbs past 0.99.** A
detector watching the error rate sees a healthy channel at every point.

![PNS: information grows while the observable does not](output/bb84_pns_attack.png)

## 2. What Alice and Bob can conclude

The consequence is a statement about what a *bound* is. Write the GLLP rate

```text
R = (1/2) Q_mu [ -f_ec H_2(E_mu) + (Q_1/Q_mu)(1 - H_2(e_1)) ].
```

The single-photon fraction `Q_1/Q_mu` is not something the observed data determine.
Eve's blocking of single-photon pulses moves `Q_1` while leaving `Q_mu` and `E_mu`
untouched — so any value down to zero is consistent with what Alice and Bob see.

| `mu` | `Q_1/Q_mu` | rate at the honest value | worst case permitted |
|:---|:---|:---|:---|
| 0.1 | 0.9092 | **+0.003688** | −0.000470 |
| 0.3 | 0.7520 | **+0.008825** | −0.001389 |
| 0.5 | 0.6218 | **+0.011648** | −0.002289 |
| 1.0 | 0.3866 | **+0.012444** | −0.004463 |

A decoy-free implementation reports the first of those columns. It is positive,
and it is an *assumption*. A bound that fails for a channel consistent with the
observed data is not a bound, and the worst case is what the data support. This is
the gap that decoy states close, by measuring enough different intensities to pin
`Q_1` down (Hwang 2003; Lo, Ma and Chen 2005).

## 3. What is not modelled

Each of these is a separate increment. None is a side effect of the current code,
and none should be claimed on its behalf.

**Detector blinding (Lydersen et al. 2010).** Requires a detector model with a
classical threshold: Eve shines bright light to drive the avalanche photodiodes
into linear mode, after which their click outcomes are controlled by her rather
than by the photon. The essential content is that a *classical* optical attack
defeats a *quantum* security argument, and modelling it needs a detector response
function, not just an efficiency.

**Timing side channels and Trojan-horse attacks.** Needs a time-resolved model of
the source and detectors, and for Trojan-horse a back-reflection channel from the
source to Eve. The content is that the modulator's timing, or light reflected off
the source, leaks the basis without touching the quantum channel.

**Finite-key statistics.** A different kind of change: not an attack but a
correction. The parameter-estimation step estimates the error rate from a finite
sample, so the bound must hold with a confidence level rather than in expectation,
and there is a minimum number of rounds below which no key can be extracted. This
is a modification of section 2's accounting, not of the channel model.

**Decoy states.** The mitigation for section 1.3. Needs the two- or
three-intensity gain equations and a lower bound on `Y_1`. It is deliberately
absent rather than sketched, because writing a decoy bound from memory and
checking it only against its own limits is exactly the failure mode this
repository avoids elsewhere.

## 4. What this can and cannot be used for

**Can:** retrace and visualise the PNS accounting; vary `mu`, `eta`, `e_det` and
`p_dark` and watch which quantity moves while which does not; and see concretely
why a positive rate computed from the data is not yet a security statement.

**Cannot: find a new protocol-level gap.** The protocol is proven; searching the
idealised model for a break will not find one. The value of running attacks against
`bb84.py` is in retracing the proof, not in trying to falsify it — which is worth
stating plainly, because a simulation environment invites the opposite expectation.

**Cannot: speak to any deployed system.** The parameters here are representative,
not measured, and three of the four historical attack classes are absent entirely.

## 5. Files

| file | role |
|:---|:---|
| `python/riemann_framework/bb84_implementation.py` | source, detectors, PNS, the decoy-free bound |
| `python/tests/test_bb84_implementation.py` | 25 tests |
| `scripts/run_bb84_implementation_demo.py` | prints all five parts and writes the figure |
| `output/bb84_pns_attack.png` | information against observable, and the two rates |

## References

- Mayers, D. (1996). *Quantum key distribution and string oblivious transfer in noisy channels*.
- Shor, P. W. and Preskill, J. (2000). *Simple proof of security of the BB84 quantum key distribution protocol*.
- Brassard, G., Lütkenhaus, N., Mor, T. and Sanders, B. C. (2000). *Limitations on practical quantum cryptography*.
- Lütkenhaus, N. and Jahma, M. (2002). *Quantum key distribution with realistic states*.
- Hwang, W.-Y. (2003). *Quantum key distribution with high loss: toward global secure communication*.
- Lo, H.-K., Ma, X. and Chen, K. (2005). *Decoy state quantum key distribution*.
- Lydersen, L., Wiechers, C., Wittmann, C., Elser, D., Skaar, J. and Makarov, V. (2010). *Hacking commercial quantum cryptography systems by tailored bright illumination*.

## Disclaimer

This is not a security proof for or against any deployed system, and it does not
claim BB84 is broken. BB84 as a protocol is secure. What is modelled here is one
hardware assumption the protocol does not cover, together with the accounting that
shows why the protocol layer cannot see it. Three of the four historical attack
classes are absent, and the decoy-state mitigation is named rather than
implemented.
