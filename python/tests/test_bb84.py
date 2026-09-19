# Riemann Framework
# Copyright (C) 2026 MILAN NIKOLIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Tests for the BB84 baseline and its two simulation backends.

The two backends do not share a random stream -- the looped version interleaves
`integers` and `random` per round while any vectorized version draws grouped by
kind -- so same-seed equality was never available. What is available, and what
these tests pin, are the two claims that matter:

  - exact logic equivalence on identical `RoundDraws`, which isolates the round
    logic from the generator;
  - statistical agreement on a common seed.
"""

import numpy as np
import pytest

from riemann_framework.bb84 import (
    DEFAULT_DETECTION_THRESHOLD,
    RoundDraws,
    draw_rounds,
    run_bb84,
    simulate_looped,
    simulate_vectorized,
)

NOISE_TYPES = ("none", "depolarizing")
ATTACK_TYPES = ("none", "intercept_resend", "partial_intercept")


# ============================================================
# Exact logic equivalence
# ============================================================

@pytest.mark.parametrize("noise_type", NOISE_TYPES)
@pytest.mark.parametrize("attack_type", ATTACK_TYPES)
def test_backends_agree_exactly_on_identical_draws(noise_type, attack_type):
    """Given the *same* random inputs, the two backends must agree round for round.

    This is the correctness pin for the vectorization. It is deliberately not a
    same-seed comparison: that would conflate the round logic with the generator,
    and the generator cannot match anyway.
    """
    rng = np.random.default_rng(42)
    draws = draw_rounds(rng, 3000, noise_type, attack_type)
    vectorized = simulate_vectorized(draws, noise_type, 0.3, attack_type, 0.4)
    looped = simulate_looped(draws, noise_type, 0.3, attack_type, 0.4)

    for i, name in enumerate(("bits", "bob_bits", "bases_match")):
        assert np.array_equal(vectorized[i], looped[i]), (
            f"{name} differ for {noise_type}/{attack_type}"
        )


@pytest.mark.parametrize("seed", [1, 7, 42, 2024])
def test_backends_agree_exactly_across_seeds(seed):
    rng = np.random.default_rng(seed)
    draws = draw_rounds(rng, 1500, "depolarizing", "partial_intercept")
    v = simulate_vectorized(draws, "depolarizing", 0.25, "partial_intercept", 0.5)
    l = simulate_looped(draws, "depolarizing", 0.25, "partial_intercept", 0.5)
    assert all(np.array_equal(a, b) for a, b in zip(v, l))


def test_ideal_channel_has_no_errors_in_either_backend():
    """Regression: the Z-basis encoding must depend on the bit.

    An earlier revision wrote the Z amplitude to slot 0 unconditionally, which
    encodes every Z round as bit 0 -- an ideal channel showing a 0.25 QBER. The
    bug survived the vectorized path being written because the looped reference
    was correct and nothing compared them.
    """
    for backend in ("numpy", "loop"):
        result = run_bb84(n_bits=5000, seed=42, backend=backend)
        assert result.ber == 0.0, f"{backend} gave BER {result.ber} on an ideal channel"
        assert result.detected is False


# ============================================================
# Statistical agreement
# ============================================================

@pytest.mark.parametrize("attack_type", ("none", "intercept_resend"))
@pytest.mark.parametrize("noise_type", NOISE_TYPES)
def test_backends_agree_statistically_on_a_common_seed(noise_type, attack_type):
    """Different streams, same distribution: the QBERs must agree within noise.

    At `n = 200_000` the binomial standard error on a QBER near 0.25 is about
    0.001, so a tolerance of 0.01 is generous and still catches a real divergence.
    """
    vectorized = run_bb84(n_bits=200_000, noise_type=noise_type, noise_param=0.3,
                          attack_type=attack_type, seed=42, backend="numpy")
    looped = run_bb84(n_bits=200_000, noise_type=noise_type, noise_param=0.3,
                      attack_type=attack_type, seed=42, backend="loop")
    assert vectorized.ber == pytest.approx(looped.ber, abs=0.01)
    assert vectorized.detection_rate == looped.detection_rate


@pytest.mark.parametrize("backend", ("numpy", "loop"))
def test_intercept_resend_drives_the_qber_to_about_a_quarter(backend):
    """The textbook figure, and both backends must produce it.

    Eve guesses the basis correctly half the time and is wrong the other half,
    where she randomises the bit; only the rounds where Alice's and Bob's bases
    agree are sifted, and within those she is wrong half the time -- hence 0.25.
    """
    result = run_bb84(n_bits=40_000, attack_type="intercept_resend", seed=42,
                      backend=backend)
    assert result.ber == pytest.approx(0.25, abs=0.01)
    assert result.detected is True


@pytest.mark.parametrize("backend", ("numpy", "loop"))
def test_sifting_discards_about_half_the_rounds(backend):
    result = run_bb84(n_bits=40_000, seed=42, backend=backend)
    assert result.sifting_discard_rate == pytest.approx(0.5, abs=0.01)
    assert result.sifted_length + result.raw_basis_mismatches == 40_000


@pytest.mark.parametrize("backend", ("numpy", "loop"))
def test_partial_intercept_scales_with_the_intercept_probability(backend):
    low = run_bb84(n_bits=40_000, attack_type="partial_intercept", attack_param=0.1,
                   seed=42, backend=backend)
    high = run_bb84(n_bits=40_000, attack_type="partial_intercept", attack_param=0.9,
                    seed=42, backend=backend)
    assert high.ber > low.ber
    assert high.detection_rate >= low.detection_rate


# ============================================================
# The draws bundle
# ============================================================

def test_draws_are_grouped_by_kind_and_shaped_as_documented():
    draws = draw_rounds(np.random.default_rng(0), 100, "depolarizing",
                        "partial_intercept")
    assert isinstance(draws, RoundDraws)
    assert draws.bits.shape == (100,)
    assert draws.basis_uniforms.shape == (100,)
    assert draws.bob_basis_uniforms.shape == (100,)
    assert draws.bob_measure_uniforms.shape == (100,)
    assert draws.noise_real is not None and draws.noise_real.shape == (100, 2)
    assert draws.partial_uniforms is not None and draws.partial_uniforms.shape == (100,)
    # Uniforms must lie in [0, 1): a `random()` contract the thresholds rely on.
    for name in ("basis_uniforms", "bob_basis_uniforms", "bob_measure_uniforms",
                 "noise_uniforms", "eve_basis_uniforms", "eve_measure_uniforms",
                 "partial_uniforms"):
        values = getattr(draws, name)
        assert values is not None, name
        assert values.min() >= 0.0 and values.max() < 1.0, name


def test_draws_omit_what_the_configuration_cannot_use():
    """Only the enabled branches draw, so a plain run carries no noise vectors."""
    plain = draw_rounds(np.random.default_rng(0), 50, "none", "none")
    assert plain.noise_uniforms is None
    assert plain.eve_basis_uniforms is None
    assert plain.partial_uniforms is None


# ============================================================
# Parameter validation
# ============================================================

def test_backend_must_be_known():
    with pytest.raises(ValueError, match="backend"):
        run_bb84(n_bits=100, backend="cuda")


@pytest.mark.parametrize("kwargs", [
    {"n_bits": 0},
    {"noise_type": "unknown"},
    {"attack_type": "unknown"},
    {"noise_type": "depolarizing", "noise_param": 1.5},
    {"attack_type": "partial_intercept", "attack_param": 1.5},
    {"detection_threshold": 1.5},
])
def test_run_bb84_rejects_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        run_bb84(**kwargs)


def test_threshold_is_reported_and_respected():
    strict = run_bb84(n_bits=20_000, attack_type="intercept_resend", seed=42,
                      detection_threshold=0.5)
    assert strict.detection_threshold == 0.5
    assert strict.detected is False
    assert strict.ber > DEFAULT_DETECTION_THRESHOLD
