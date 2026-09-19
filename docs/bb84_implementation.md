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

This article documents `bb84_implementation.py`, which models photon-number
splitting together with the source and detector physics it needs, and implements
the decoy-state mitigation with bounds taken from the literature. The other three
are named below with what each would require, and are **not** implemented.

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

## 2.1 Decoy states, and the lower bound taken from a source

The gap in section 2 is that `Q_1` is not determined by the data at one intensity.
Decoy states close it by measuring the gain at a second, weaker intensity where the
multi-photon contribution is much smaller. The bounds implemented are the
**vacuum + weak decoy** case of Ma, Qi, Zhao and Lo (2005):

```text
Y_1 >= mu/(mu nu - nu^2) [ Q_nu e^nu - (nu^2/mu^2) Q_mu e^mu
                           - ((mu^2 - nu^2)/mu^2) Y_0 ]
e_1 <= (E_nu Q_nu e^nu - e_0 Y_0) / (nu Y_1^L)
```

**They were read off the source, not recalled**, and two independent checks were
applied.

*First, the transcription.* Ma et al. also give a general two-decoy expression in
`(nu, nu_1)`. Setting `nu_1 = 0` — the vacuum — must reproduce the vacuum + weak
form above, and
`test_the_vacuum_weak_bound_agrees_with_the_general_two_decoy_formula` evaluates
both independently and asserts they agree to `1e-12`. The two expressions are
algebraically identical, which is why the implemented form is attributable rather
than remembered.

*Second, validity against the model.* A lower bound's only real test is that it
holds. Because this is a simulation, the true `Y_1` and `e_1` are known, so
`decoy_state_report` checks `Y_1^L <= Y_1` and `e_1^U >= e_1` and reports
`bounds_are_valid`. Swept over 510 parameter sets — `mu`, `nu`, `eta` and `p_dark`
— there are **zero violations**. A mis-transcribed exponent fails this
immediately.

The bound is also tight, and tightens as the decoy weakens, which is the published
reason for choosing weak decoys (the correction is quadratic in `nu`):

| `mu` | `nu` | `Y_1^L` | true `Y_1` | tightness | `e_1^U` | true `e_1` | decoy rate | decoy-free | worst case |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| 0.5 | 0.05 | 0.098649 | 0.100002 | 0.987 | 0.01064 | 0.01001 | **+0.011398** | +0.011648 | −0.002289 |
| 0.5 | 0.10 | 0.097255 | 0.100002 | 0.972 | 0.01132 | 0.01001 | **+0.011139** | +0.011648 | −0.002289 |
| 0.5 | 0.20 | 0.094335 | 0.100002 | 0.943 | 0.01283 | 0.01001 | **+0.010599** | +0.011648 | −0.002289 |
| 1.0 | 0.10 | 0.093445 | 0.100002 | 0.934 | 0.01178 | 0.01001 | **+0.011137** | +0.012444 | −0.004463 |

Read the last three columns together, because that is the finding. What decoys buy
is **not a bigger number but a valid one**: the decoy rate sits about 2% below the
decoy-free figure, which was larger only because it assumed a single-photon
fraction nobody had measured, and it is far above the worst case the data permit.

### 2.2 A bug this increment found

`Y_1^L` goes **negative** when single-photon events are suppressed — reproduced by
driving `Q_nu` toward `Y_0` while leaving `Q_mu` alone, which is exactly Eve's
blocking. That is not a degenerate input; it is the signal decoy states exist to
detect. An earlier revision of `decoy_state_report` let `upper_bound_e1` raise
`ValueError` in that case, so the detection tool died on the very thing it was
built to catch. It now reports a vacuous bound (`bound_is_vacuous`) and a
non-positive rate. `upper_bound_e1` still refuses on a standalone call, where
there genuinely is no finite bound to return;
`test_the_analysis_never_raises_over_its_whole_input_domain` sweeps the domain to
keep it that way.

## 2.3 Finite keys: the error rate is estimated, not known

Everything in section 2 assumes infinitely many rounds. In practice the error rate
comes from a finite test sample, so the value a rate calculation may *use* is an
upper confidence bound. Hoeffding's inequality gives it: for `k` independent
Bernoulli trials,

```text
P(true p > p_hat + delta) <= exp(-2 k delta^2),   delta = sqrt(ln(1/epsilon) / (2k)).
```

The slack falls as `1/sqrt(k)`, so finite-key effects are a small-sample problem
rather than a uniform rate penalty, and they bite hardest when the observed error
rate is already near the threshold where the rate vanishes — a *distance* penalty,
not a rate penalty.

| pulses `N` | test sample `k` | `delta` | `E_mu^U` | finite rate | asymptotic |
|:---|:---|:---|:---|:---|:---|
| 1e6 | 2438 | 0.068719 | 0.078739 | **+0.002178** | +0.011139 |
| 1e8 | 243862 | 0.006871 | 0.016891 | **+0.009932** | +0.011139 |
| 1e10 | 24386238 | 0.000687 | 0.010707 | **+0.011011** | +0.011139 |
| 1e12 | 2438623897 | 0.000069 | 0.010089 | **+0.011126** | +0.011139 |

Bisecting on the sign change gives a **minimum of `5.606e5` pulses** at these
parameters, below which no finite-key security claim can be made however good the
channel — and a worse channel raises that floor, which
`test_a_worse_channel_needs_more_rounds` pins.

**What is deliberately not attempted:** the full composable finite-key
`epsilon`-bookkeeping. The rate above is the asymptotic expression with a corrected
error rate, and `epsilon` governs only the parameter-estimation step; the
privacy-amplification and error-correction overheads are not accounted for in a
composable framework. Saying so is the point — a finite-key claim assembled from
plausible-looking terms is exactly the kind of thing this repository does not do.

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

Both accounting gaps are now closed: decoy states in section 2.1 and finite-key
statistics in section 2.3. What remains is detector physics.

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
| `python/tests/test_bb84_implementation.py` | 45 tests |
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
