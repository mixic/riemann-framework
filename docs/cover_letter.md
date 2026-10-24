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

# Cover letter (template, unsent)

Dear Editor,

We submit the manuscript *Desymmetrization of Quantum Spectra: A Bayesian Sector-Count
Diagnostic with Measured Coverage* for consideration in [Journal].

**The problem.** Spacing statistics are the standard diagnostic for quantum chaos. When a
Hamiltonian commutes with an involution, its spectrum is a union of independent sectors,
and a spacing statistic measured on the full spectrum is measured on a superposition. At
three or more unresolved sectors the mean gap ratio `⟨r⟩` falls inside the Poisson window
`[0.36, 0.41]`: a researcher who measures `0.39` and concludes "integrable" is wrong, and
the standard test gives no indication. The failure is silent.

**The contribution.** We present a diagnostic that (i) verifies the symmetries, (ii)
splits the spectrum into joint sectors, (iii) flags a contaminated full spectrum, and
(iv) estimates the number of unresolved sectors as a posterior with a measured coverage.

The mean `⟨r⟩` cannot be inverted. The sequence of `≈240` gap ratios can be. A
first-order Markov model fitted on simulated superpositions yields a posterior over
`{1, …, 6, ≥6/poisson}`. At a nominal 95% interval the measured coverage is `1.00`,
`0.93`, `0.87`, `0.98`, `0.97` at `1, 2, 3, 4, 6` sectors and `0.78` for a Poisson
spectrum. The single-sector case is decisive (`p = 0.98`, interval `1..1`, correct 95% of
the time); the two-sector case is defensible as a set (`2..5`) but not as a point. From
three sectors upward the count is not recoverable — the posterior reports `≥3`, and `3`
through `6` are indistinguishable. Two-sector GOE and GUE are indistinguishable in the
full spectrum, so a class test on a contaminated spectrum is uninformative rather than
noisy.

**What is new.** The phenomenon is standard quantum-chaos practice (Giraud et al., Phys.
Rev. X **12**, 011006 (2022)). What is local is the measured table, the entry points, the
posterior's measured resolution, and the recorded limits. The diagnostic is calibrated on
a measured table, its false-positive rate is stated (`4` of `40` pure single-sector GOE
spectra fall below the flag), and its limits are reported rather than hidden.

**The dynamical counterpart.** The multi-copy imaginary-time circuits are built on the
double-bracket flow `dρ/dβ = [[ρ, H], ρ]`. We implement the flow and measure what it
preserves: the spectrum of `ρ` (drift `3e-12` over `β = 15`), the trace, and — when the
state commutes with the involution — the sector populations (`< 1e-8`). We also find what
the sources' description does not cover: a state that does not commute is driven into a
single sector, so the flow *selects* a sector rather than preserving one. In neither case
does it touch the Hamiltonian, so it cannot repair a contaminated spectrum.

**What the manuscript does not claim.** It is about a diagnostic for quantum spectra. It
is not about the Riemann hypothesis, makes no claim about zero locations or the Euler
product, and makes no claim beyond the measured data.

**Code and formal verification.** The code and formal verification are available at
[URL]. The Lean theorems `commute_doubleBracketIncrement` and `commute_euler_step` are
`sorry`-free and depend only on `propext`.

We confirm that this manuscript has not been published elsewhere and is not under
consideration by another journal.

Sincerely,

[Name]
[Affiliation]
[Email]
