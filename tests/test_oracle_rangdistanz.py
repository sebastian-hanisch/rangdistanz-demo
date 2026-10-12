"""Orakel-Tests rangdistanz-demo: Maße und angezeigte Kennzahlen gegen einen ANDEREN Rechenweg (DEMO-PLAYBOOK §12).

1. Kendall-Distanz gegen scipy.stats.kendalltau und gegen die Aufzählung aller Paare.
2. Footrule gegen die Summe über die Inversen (zweiter Rechenweg) und gegen die vollständige Umkehr als Höchstwert.
3. Spearman-ρ gegen scipy.stats.spearmanr.
4. Diaconis-Graham: K <= F <= 2K über alle Permutationen von n = 4 und viele Zufallspermutationen für n = 8.
5. RBO gegen eine unabhängige Fassung mit exakter Bruchrechnung und expliziten Mengen.
6. Top-k-Überlappung gegen den Mengenschnitt; Metrik-Eigenschaften (Symmetrie, Dreiecksungleichung) für K und F.
7. Paritätsinvariante: m Nachbartausche ergeben eine Kendall-Distanz mit der Parität von m.
"""

import itertools
import random
from fractions import Fraction

import pytest

import rgd_measures as M
import rgd_perturb as P
import turnier_generator as T


def random_order(n, rnd):
    o = list(range(n))
    rnd.shuffle(o)
    return tuple(o)


def brute_kendall(a, b):
    """Aufzählung aller Paare: je Paar zählt, ob a und b es verschieden ordnen."""
    pa = {x: j for j, x in enumerate(a)}
    pb = {x: j for j, x in enumerate(b)}
    return sum(1 for x, y in itertools.combinations(a, 2) if (pa[x] < pa[y]) != (pb[x] < pb[y]))


def inverse(order):
    inv = [0] * len(order)
    for place, x in enumerate(order):
        inv[x] = place
    return inv


# --- 1. Kendall -----------------------------------------------------------------------------------------------------------------------

def test_kendall_distance_matches_enumeration_and_scipy():
    stats = pytest.importorskip("scipy.stats")
    rnd = random.Random(2026)
    for _ in range(150):
        n = rnd.randint(2, 12)
        a, b = random_order(n, rnd), random_order(n, rnd)
        K = M.kendall_distance(a, b)
        assert K == brute_kendall(a, b)
        tau = stats.kendalltau(inverse(a), inverse(b)).statistic
        assert M.kendall_tau(a, b) == pytest.approx(tau, abs=1e-12)
        assert K == pytest.approx((1 - tau) * M.max_kendall(n) / 2)


# --- 2. Footrule ---------------------------------------------------------------------------------------------------------------------

def test_footrule_matches_the_inverse_sum_and_the_reversal_is_the_maximum():
    rnd = random.Random(7)
    for _ in range(150):
        n = rnd.randint(2, 12)
        a, b = random_order(n, rnd), random_order(n, rnd)
        ia, ib = inverse(a), inverse(b)
        assert M.footrule(a, b) == sum(abs(x - y) for x, y in zip(ia, ib))
        assert M.footrule(a, b) <= M.max_footrule(n)
    for n in range(2, 14):
        ident = tuple(range(n))
        assert M.footrule(ident, ident[::-1]) == M.max_footrule(n)


def test_max_footrule_is_attained_and_not_exceeded_by_exhaustive_search():
    for n in (3, 4, 5, 6):
        ident = tuple(range(n))
        best = max(M.footrule(ident, p) for p in itertools.permutations(range(n)))
        assert best == M.max_footrule(n)


# --- 3. Spearman ---------------------------------------------------------------------------------------------------------------------

def test_spearman_rho_matches_scipy():
    stats = pytest.importorskip("scipy.stats")
    rnd = random.Random(11)
    for _ in range(100):
        n = rnd.randint(3, 12)
        a, b = random_order(n, rnd), random_order(n, rnd)
        theirs = stats.spearmanr(inverse(a), inverse(b)).statistic
        assert M.spearman_rho(a, b) == pytest.approx(theirs, abs=1e-12)


# --- 4. Diaconis-Graham -----------------------------------------------------------------------------------------------------------

def test_diaconis_graham_inequality_exhaustive_for_n4_and_random_for_n8():
    base4 = tuple(range(4))
    for p in itertools.permutations(range(4)):
        K, F = M.kendall_distance(base4, p), M.footrule(base4, p)
        assert K <= F <= 2 * K
    rnd = random.Random(3)
    base8 = tuple(range(8))
    for _ in range(1000):
        p = random_order(8, rnd)
        K, F = M.kendall_distance(base8, p), M.footrule(base8, p)
        assert K <= F <= 2 * K


# --- 5. RBO ----------------------------------------------------------------------------------------------------------------------------

def exact_rbo(a, b, p):
    """Unabhängige Fassung: exakte Bruchrechnung, Überlappung je Tiefe aus Mengen."""
    p = Fraction(p).limit_denominator(1000)
    num = Fraction(0)
    den = Fraction(0)
    for d in range(1, len(a) + 1):
        overlap = len(set(a[:d]) & set(b[:d]))
        num += p ** (d - 1) * Fraction(overlap, d)
        den += p ** (d - 1)
    return float(num / den)


def test_rbo_matches_exact_fraction_arithmetic_and_the_hand_value(mini):
    a, b = mini
    assert exact_rbo(a, b, 0.5) == pytest.approx(19 / 45)
    rnd = random.Random(5)
    for _ in range(120):
        n = rnd.randint(2, 12)
        x, y = random_order(n, rnd), random_order(n, rnd)
        p = rnd.choice([0.5, 0.7, 0.9, 0.95])
        assert M.rbo(x, y, p) == pytest.approx(exact_rbo(x, y, p), abs=1e-12)


def test_rbo_is_one_for_identical_lists_and_lower_when_the_top_differs():
    ref = tuple(range(10))
    assert M.rbo(ref, ref, 0.9) == pytest.approx(1.0)
    swapped_top = (1, 0) + ref[2:]
    swapped_end = ref[:8] + (9, 8)
    assert M.rbo(ref, swapped_top, 0.9) < M.rbo(ref, swapped_end, 0.9) < 1.0


# --- 6. Top-k und Metrik-Eigenschaften -------------------------------------------------------------------------------------------

def test_topk_overlap_matches_set_intersection():
    rnd = random.Random(9)
    for _ in range(100):
        n = rnd.randint(2, 12)
        a, b = random_order(n, rnd), random_order(n, rnd)
        k = rnd.randint(1, n)
        assert M.topk_overlap(a, b, k) == len(set(a[:k]) & set(b[:k])) / k


def test_kendall_and_footrule_satisfy_the_triangle_inequality():
    rnd = random.Random(13)
    for _ in range(500):
        n = rnd.randint(2, 9)
        a, b, c = (random_order(n, rnd) for _ in range(3))
        assert M.kendall_distance(a, c) <= M.kendall_distance(a, b) + M.kendall_distance(b, c)
        assert M.footrule(a, c) <= M.footrule(a, b) + M.footrule(b, c)


# --- 7. Parität -----------------------------------------------------------------------------------------------------------------------

def test_adjacent_swaps_flip_the_parity_of_the_kendall_distance():
    ref = tuple(range(9))
    for seed in range(60):
        m = seed % 7
        out = P.random_adjacent_swaps(ref, m, T.SplitMix64(seed))
        assert M.kendall_distance(ref, out) % 2 == m % 2
