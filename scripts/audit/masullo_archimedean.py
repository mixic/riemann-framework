"""Phase 2.1 / 2.3: the Archimedean integral of Masullo, Section 1.4.3 (= 1.8.4.3).

Claim under test, quoted (p. 29 and p. 54):

    "The integrals [ ... ] are bounded above by a common constant A > 0
     independent of z in K and independent of the specific phi."

Data from the draft that fix the model (Section 1.4.2, p. 28):

    phi_z(t) := t^{-z} for t > 1,  phi_z(t) := 0 for t in (0,1),  phi_z(1) = 1/2,
    phi_{h,eps,z}(t) := h(t) * (rho_eps * phi_z)(t),
    h a bump in D(R_{>0}) supported over (1,+inf), valued in [0,1], "below
    1_{(1,+inf)}, converging pointwise monotonically" to it,

and assumption (1) of Section 1.4, that phi is smooth and compactly supported,
which supplies a finite cutoff T in the t integral.

For |chi_v| = 1 the real-place term of the displayed formula is therefore

    I = int_1^T  h(t) * (rho_eps * phi_z)(t) * t^{-sigma-1/2} / (t-1)  dt ,
    z = sigma + i tau, since |t^{-z}| = t^{-sigma} and |t|^{1/2} dt/t = t^{-1/2} dt.

The kernel 1/(t-1) is not integrable at t = 1. Each admissible h vanishes on a
neighbourhood of 1 (support over (1,+inf)), so each integral is finite; but any
family h -> 1_{(1,+inf)} monotonically must move that neighbourhood to 0, and by
monotone convergence

    sup over the family of I  =  int_1^T t^{-sigma-1/2}/(t-1) dt  =  +inf.

So the bound can be uniform in z at fixed phi, and cannot be uniform in phi.
The tables below exhibit exactly that: (A) bounded in z, (B) log(1/delta) growth
along the family, (C) the complex-place term stays bounded, which locates the
defect in the real-place kernel rather than in the character or the place.

To avoid any modelling ambiguity the family used in (B) is the step family
h_delta = 1_{(1+delta, inf)}; smoothing it changes the integral by O(1) (the
boundary layer contributes at most int over a length-delta interval of a bounded
integrand) and cannot remove the log divergence.
"""

from __future__ import annotations

import json
from pathlib import Path

import mpmath as mp

OUT = Path(r"C:\Users\Milan\Projects\riemann-audit\out")
mp.mp.dps = 30

T_CUT = mp.mpf(10) ** 4  # compact support cutoff from assumption (1)


def real_place_step(sigma: float, delta: float, T: mp.mpf = T_CUT) -> float:
    """I for the step family h_delta = 1_{(1+delta, inf)}.

    I = int_{1+delta}^{T} t^{-sigma-1/2}/(t-1) dt.
    """
    f = lambda t: t ** (-sigma - 0.5) / (t - 1)
    return float(abs(mp.quad(f, [1 + delta, 1 + 2 * delta, 1 + 4 * delta, 2, 10, T])))


def real_place_full(sigma: float, T: mp.mpf = T_CUT) -> float:
    """The limiting integral int_1^T t^{-sigma-1/2}/(t-1) dt, which is +inf.

    Reported as a truncated surrogate to show the mechanism: the cutoff at the
    lower end is what a finite h supplies.
    """
    f = lambda t: t ** (-sigma - 0.5) / (t - 1)
    return float(abs(mp.quad(f, [1 + 1e-12, 1.001, 1.01, 1.1, 2, 10, T])))


def complex_place(sigma: float, delta: float, ntheta: int = 128) -> float:
    """The complex-place term, over the same step family.

    (1/2pi) int_{R>0} int_T  |phi(t e^{iw})| t^{1/2} / |1 - t e^{iw}|  2 dw dt/t,
    with |phi| = t^{-sigma} above the support threshold.  The singularity of
    1/|1 - t e^{iw}| at (t,w) = (1,0) is two-dimensional and integrable, so this
    term stays bounded as delta -> 0.
    """
    thetas = [2 * mp.pi * (k + 0.5) / ntheta for k in range(ntheta)]

    def inner(t: float) -> float:
        if t <= 1 + delta:
            return 0.0
        s = 0.0
        for w in thetas:
            dist = mp.sqrt((1 - t * mp.cos(w)) ** 2 + (t * mp.sin(w)) ** 2)
            s += 1 / dist
        return (s / ntheta) * t ** (-sigma) * t ** (-0.5) * 2

    return float(abs(mp.quad(inner, [1 + delta, 1 + 2 * delta, 2, 10, T_CUT])))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # (A) uniform in z at fixed phi: delta fixed, sigma varied, tau irrelevant to |I|.
    rows_a = []
    for sigma in (0.0, 0.25, 0.5, 1.0, 2.0, 5.0):
        rows_a.append(
            {
                "sigma": sigma,
                "tau": 0.0,
                "I": real_place_step(sigma, delta=0.25),
                "note": "tau enters only through |t^{i tau}| = 1, so |I| is tau-independent",
            }
        )

    # (B) uniform in phi at fixed z: the step family -> 1_{(1,inf)}
    rows_b = []
    for k in range(1, 17):
        delta = 2.0 ** -k
        val = real_place_step(1.0, delta)
        rows_b.append(
            {
                "delta": delta,
                "log2_1_over_delta": k,
                "I": val,
                "log(1/delta)": float(mp.log(1 / delta)),
                "I_minus_log": val - float(mp.log(1 / delta)),
            }
        )

    # (C) complex-place contrast
    rows_c = []
    for k in (1, 2, 4, 8, 12):
        delta = 2.0 ** -k
        rows_c.append({"delta": delta, "I_complex": complex_place(1.0, delta)})

    # (D) 2.3 randomised sweep over the family: the empirical sup a uniform A would bound.
    import random

    rng = random.Random(20261122)
    trials = []
    for _ in range(60):
        sigma = rng.uniform(0.0, 3.0)
        delta = 2.0 ** rng.uniform(-16, -1)
        trials.append({"sigma": sigma, "delta": delta, "I": real_place_step(sigma, delta)})
    worst = max(trials, key=lambda r: r["I"])

    result = {
        "claim": "1.4.3: a common A bounds the Archimedean integrals, independent of z and of phi",
        "A_uniform_in_z": rows_a,
        "A_sup": max(r["I"] for r in rows_a),
        "B_uniform_in_phi": rows_b,
        "B_slope_on_last_decade": (rows_b[-1]["I"] - rows_b[-5]["I"]) / (
            rows_b[-1]["log(1/delta)"] - rows_b[-5]["log(1/delta)"]
        ),
        "B_offset_spread": max(r["I_minus_log"] for r in rows_b) - min(r["I_minus_log"] for r in rows_b),
        "C_complex_place": rows_c,
        "C_spread": max(r["I_complex"] for r in rows_c) - min(r["I_complex"] for r in rows_c),
        "D_fuzz": {"trials": len(trials), "sup_I": worst["I"], "worst": worst},
        "diagnosis": (
            "Bounded in z at fixed phi (A). Along the very family h -> 1_{(1,inf)} that the draft "
            "defines, I = log(1/delta) + O(1) (B), so no A independent of phi exists. The complex-place "
            "term is bounded (C), so the defect is the real-place kernel t^{-1/2}/(t-1), whose "
            "non-integrability at t=1 the draft's 'simple estimates' do not address."
        ),
    }
    (OUT / "masullo_archimedean.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("A. fixed phi (delta=0.25), varying z:")
    for r in rows_a:
        print(f"   sigma={r['sigma']:<5}  |I|={r['I']:.6f}")
    print(f"   sup = {result['A_sup']:.6f}  (bounded)\n")

    print("B. fixed z (sigma=1), h_delta -> 1_{(1,inf)}:")
    print("     k   delta         |I|              log(1/delta)    |I|-log")
    for r in rows_b:
        print(
            f"   {r['log2_1_over_delta']:>3}   {r['delta']:.3e}   {r['I']:>14.6f}   "
            f"{r['log(1/delta)']:>10.6f}   {r['I_minus_log']:>8.4f}"
        )
    print(f"   slope d|I|/dlog(1/delta) over last decade = {result['B_slope_on_last_decade']:.4f}")
    print(f"   spread of |I| - log(1/delta) = {result['B_offset_spread']:.4f}\n")

    print("C. complex-place term, same delta grid:")
    for r in rows_c:
        print(f"   delta={r['delta']:.3e}  |I_c|={r['I_complex']:.6f}")
    print(f"   spread = {result['C_spread']:.4f}  (bounded)\n")

    print("D. fuzz:", result["D_fuzz"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
