"""Eigenschaftstests (metamorph) der Rangabstände (ORACLE-PLAYBOOK §5.2).

Beziehungen, die für die Maße gelten müssen, an je 30 bis 40 Zufallsinstanzen (SplitMix64, fester Seed) plus Randfällen. Ergänzt
test_oracle_rangdistanz.py (dort: scipy, Aufzählung, Symmetrie/Dreieck für K und F, Parität von Nachbartauschen, Diaconis-Graham):

1. Gemeinsames Umnummerieren beider Rangfolgen ändert kein Maß (Maße kennen keine Namen).
2. Alle Maße sind symmetrisch, Identität gibt Distanz 0 bzw. Ähnlichkeit 1.
3. Dreiecksungleichung auch für den Spearman-Abstand sqrt(Σd²) (aus ρ) und die Top-k-Distanz; Parität: K(a,c) = K(a,b) + K(b,c) mod 2.
4. Eine Rangfolge umkehren: K(a, rev b) = Kmax - K(a, b), τ und ρ wechseln das Vorzeichen; Umkehr gegen sich selbst ist das Maximum.
5. RBO: geschlossene Form für einen Nachbartausch, fällt mit der Tiefe des Tausches, Grenzfälle p -> 0 und p -> 1, Schranken.
6. Top-k: k = n gibt 1, k = 1 prüft nur Platz 1, ordnungsunempfindlich innerhalb von Spitze und Rest.
7. Störungen: Nachbartausch K = 1 und F = 2, Verschiebung um d Plätze K = d und F = 2d, Umkehr der hinteren Hälfte, zufällige Tausche.
8. normalised_distance, closer_to_truth und disagreement_share: Schranken und Antisymmetrie.
9. Randfälle: n = 1, n = 2, ungleiche Teilnehmer.
"""

import math

import numpy as np
import pytest

import rgd_measures as M
import rgd_perturb as P
import turnier_generator as T

N_INST = 40


def perm(seed, n):
    return tuple(int(x) for x in T.SplitMix64(seed).permutation(n))


def pairs(base, count=N_INST, nmin=2, nmax=12):
    """(a, b, n) mit wechselndem n."""
    out = []
    for i in range(count):
        n = nmin + (i * 7 + base) % (nmax - nmin + 1)
        out.append((perm(base * 10_000 + 2 * i, n), perm(base * 10_000 + 2 * i + 1, n), n))
    return out


def all_measures(a, b, p=0.9, k=2):
    return M.measure_values(a, b, p, min(k, len(a)))


def relabel(order, mapping):
    return tuple(int(mapping[x]) for x in order)


def spearman_sq(a, b):
    """Σ d² aus ρ zurückgerechnet (unabhängig von footrule)."""
    n = len(a)
    return (1.0 - M.spearman_rho(a, b)) * n * (n * n - 1) / 6.0


# --- 1. Umnummerieren ---------------------------------------------------------------------------------------------------------------

def test_joint_relabeling_of_both_rankings_changes_no_measure():
    for idx, (a, b, n) in enumerate(pairs(1)):
        m = perm(500 + idx, n)
        v1 = all_measures(a, b)
        v2 = all_measures(relabel(a, m), relabel(b, m))
        assert v2["kendall_distance"] == v1["kendall_distance"]
        assert v2["footrule"] == v1["footrule"]
        for key in ("kendall_tau", "spearman_rho"):
            assert v2[key] == pytest.approx(v1[key]) or (math.isnan(v2[key]) and math.isnan(v1[key]))
        # RBO und Top-k zählen Überlappungen von Mengen: ebenfalls namensunabhängig
        assert v2["rbo"] == pytest.approx(v1["rbo"])
        assert v2["topk"] == pytest.approx(v1["topk"])


def test_relabeling_only_one_ranking_does_change_the_distance_in_general():
    """Gegenprobe: Der Test oben hätte sonst nichts geprüft (Namen sind nicht egal, wenn nur eine Seite umbenannt wird)."""
    changed = 0
    for idx, (a, b, n) in enumerate(pairs(2, nmin=4)):
        m = perm(900 + idx, n)
        changed += int(M.kendall_distance(relabel(a, m), b) != M.kendall_distance(a, b))
    assert changed >= 10


# --- 2. Symmetrie, Identität ---------------------------------------------------------------------------------------------------------

def test_every_measure_is_symmetric_and_identity_is_the_extreme():
    for a, b, n in pairs(3):
        v, w = all_measures(a, b), all_measures(b, a)
        for key in v:
            assert w[key] == pytest.approx(v[key])
        ident = all_measures(a, a)
        assert ident["kendall_distance"] == 0 and ident["footrule"] == 0
        assert ident["kendall_tau"] == pytest.approx(1.0) and ident["spearman_rho"] == pytest.approx(1.0)
        assert ident["rbo"] == pytest.approx(1.0) and ident["topk"] == 1.0
        # kein Maß liegt jenseits seiner Skala
        assert 0 <= v["kendall_distance"] <= M.max_kendall(n) and 0 <= v["footrule"] <= n * n // 2
        assert -1 - 1e-12 <= v["kendall_tau"] <= 1 + 1e-12 and -1 - 1e-12 <= v["spearman_rho"] <= 1 + 1e-12
        assert 0 <= v["rbo"] <= 1 + 1e-12 and 0 <= v["topk"] <= 1


# --- 3. Dreieck und Parität -------------------------------------------------------------------------------------------------------------

def test_triangle_inequality_for_spearman_distance_and_topk_distance_and_parity_of_kendall():
    for i in range(N_INST):
        n = 3 + i % 8
        a, b, c = perm(40_000 + 3 * i, n), perm(40_000 + 3 * i + 1, n), perm(40_000 + 3 * i + 2, n)
        d = lambda x, y: math.sqrt(max(spearman_sq(x, y), 0.0))
        assert d(a, c) <= d(a, b) + d(b, c) + 1e-9
        for k in (1, 2, n // 2 or 1, n):
            tk = lambda x, y: 1.0 - M.topk_overlap(x, y, k)
            assert tk(a, c) <= tk(a, b) + tk(b, c) + 1e-12
        assert (M.kendall_distance(a, c) - M.kendall_distance(a, b) - M.kendall_distance(b, c)) % 2 == 0
        assert M.footrule(a, b) % 2 == 0                                      # Footrule ist immer gerade


# --- 4. Umkehren ---------------------------------------------------------------------------------------------------------------------

def test_reversing_one_ranking_complements_kendall_and_flips_tau_and_rho():
    for a, b, n in pairs(5):
        rb = tuple(reversed(b))
        assert M.kendall_distance(a, rb) == M.max_kendall(n) - M.kendall_distance(a, b)
        if n >= 2:
            assert M.kendall_tau(a, rb) == pytest.approx(-M.kendall_tau(a, b))
            assert M.spearman_rho(a, rb) == pytest.approx(-M.spearman_rho(a, b))
        # gegen die eigene Umkehrung: Höchstwerte, unabhängig von der Rangfolge
        assert M.kendall_distance(a, tuple(reversed(a))) == n * (n - 1) // 2
        assert M.footrule(a, tuple(reversed(a))) == n * n // 2


# --- 5. RBO -------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("p", [0.3, 0.5, 0.9, 0.99])
def test_rbo_of_an_adjacent_swap_has_a_closed_form_and_falls_with_depth(p):
    """Tausch der Plätze i und i+1: nur die Tiefe d = i hat Überlappung (i-1)/i, alle anderen volle: 1 - RBO = p^(i-1) / (i Σ p^(d-1))."""
    for n in (2, 5, 12):
        a = tuple(range(n))
        den = sum(p ** (d - 1) for d in range(1, n + 1))
        previous = None
        for i in range(1, n):
            dist = 1.0 - M.rbo(a, P.swap_adjacent(a, i), p)
            assert dist == pytest.approx(p ** (i - 1) / (i * den), rel=1e-9, abs=1e-12)
            if previous is not None:
                assert dist < previous              # je weiter hinten, desto weniger zählt der Tausch
            previous = dist


def test_rbo_limits_for_p_to_zero_and_one_and_bounds():
    for a, b, n in pairs(6, nmin=3):
        # p -> 0: nur Tiefe 1 zählt: RBO = 1, wenn die Spitze gleich ist, sonst 0
        assert M.rbo(a, b, 1e-9) == pytest.approx(1.0 if a[0] == b[0] else 0.0, abs=1e-6)
        # p -> 1: Mittel der Überlappungen A_d über alle Tiefen (gleiches Gewicht)
        mean_a = np.mean([len(set(a[:d]) & set(b[:d])) / d for d in range(1, n + 1)])
        assert M.rbo(a, b, 1 - 1e-9) == pytest.approx(mean_a, abs=1e-6)
        for p in (0.1, 0.5, 0.9, 0.999):
            r = M.rbo(a, b, p)
            assert 0.0 <= r <= 1.0 + 1e-12
            assert M.rbo(a, b, p) == pytest.approx(M.rbo(b, a, p))
            assert r < 1.0 - 1e-12 if a != b else r == pytest.approx(1.0)


def test_rbo_weights_the_top_more_than_the_bottom_for_the_same_kendall_distance():
    """Gleich viele vertauschte Paare (K = 1), aber Spitze gegen Ende: der Tausch an der Spitze ist stets weiter entfernt."""
    for n in range(3, 13):
        a = tuple(range(n))
        for p in (0.5, 0.9):
            assert M.rbo(a, P.swap_adjacent(a, 1), p) < M.rbo(a, P.swap_adjacent(a, n - 1), p)


# --- 6. Top-k ----------------------------------------------------------------------------------------------------------------------------

def test_topk_overlap_special_cases_and_order_insensitivity():
    for idx, (a, b, n) in enumerate(pairs(7, nmin=3)):
        assert M.topk_overlap(a, b, n) == 1.0
        assert M.topk_overlap(a, b, 1) == (1.0 if a[0] == b[0] else 0.0)
        k = 1 + idx % (n - 1)
        # Reihenfolge innerhalb der Spitze und innerhalb des Rests ändert nichts
        shuffled = tuple(sorted(a[:k], key=lambda x: (x * 7) % 11)) + tuple(sorted(a[k:], key=lambda x: -x))
        assert M.topk_overlap(shuffled, b, k) == M.topk_overlap(a, b, k)
        assert M.topk_overlap(a, b, k) * k == pytest.approx(round(M.topk_overlap(a, b, k) * k))     # Vielfaches von 1/k


# --- 7. Störungen ------------------------------------------------------------------------------------------------------------------------

def test_perturbations_have_the_distance_they_construct():
    for n in (2, 3, 6, 9, 12):
        a = perm(60 + n, n)
        for i in range(1, n):
            b = P.swap_adjacent(a, i)
            assert M.kendall_distance(a, b) == 1 and M.footrule(a, b) == 2
        for i in range(1, n + 1):
            for d in range(-n, n + 1):
                b = P.move_by(a, i, d)
                effective = abs(max(0, min(n - 1, (i - 1) + d)) - (i - 1))     # gegen die Ränder begrenzte Verschiebung
                assert sorted(b) == sorted(a)
                assert M.kendall_distance(a, b) == effective
                assert M.footrule(a, b) == 2 * effective


def test_reversing_the_lower_half_is_an_involution_with_known_distances():
    for n in range(1, 15):
        a = perm(70 + n, n)
        b = P.reverse_lower_half(a)
        h = n // 2
        assert P.reverse_lower_half(b) == a
        if h >= 2:
            assert b[: n - h] == a[: n - h] and b[n - h:] == tuple(reversed(a[n - h:]))
            assert M.kendall_distance(a, b) == h * (h - 1) // 2
            assert M.footrule(a, b) == h * h // 2
        else:
            assert b == a


def test_random_adjacent_swaps_bound_the_distance_by_the_number_of_swaps():
    for i in range(N_INST):
        n = 2 + i % 10
        m = i % 9
        a = perm(80 + i, n)
        b = P.random_adjacent_swaps(a, m, T.SplitMix64(i))
        assert sorted(b) == sorted(a)
        k = M.kendall_distance(a, b)
        assert k <= m and (m - k) % 2 == 0
        assert M.footrule(a, b) <= 2 * m
        assert b == P.random_adjacent_swaps(a, m, T.SplitMix64(i))


# --- 8. Normierte Abstände, Entscheid ------------------------------------------------------------------------------------------------

def test_normalised_distances_are_bounded_and_consistent_with_the_raw_measures():
    for a, b, n in pairs(8, nmin=2):
        nd = M.normalised_distance(a, b, 0.9, min(2, n))
        assert all(0.0 <= v <= 1.0 + 1e-12 for v in nd.values())
        assert nd["Kendall"] == pytest.approx((1.0 - M.kendall_tau(a, b)) / 2.0)
        assert nd["Footrule"] == pytest.approx(M.footrule(a, b) / (n * n // 2))
        assert nd["Top-k"] == pytest.approx(1.0 - M.topk_overlap(a, b, min(2, n)))
        same = M.normalised_distance(a, a, 0.9, min(2, n))
        assert all(v == pytest.approx(0.0, abs=1e-12) for v in same.values())
        rev = M.normalised_distance(a, tuple(reversed(a)), 0.9, min(2, n))
        assert rev["Kendall"] == pytest.approx(1.0) and rev["Footrule"] == pytest.approx(1.0)


def test_closer_to_truth_and_disagreement_share_are_antisymmetric_and_symmetric():
    rnd = T.SplitMix64(11)
    for i in range(N_INST):
        da, db = (float(x) for x in np.round(rnd.uniform(2) * 5) / 5)
        assert M.closer_to_truth(da, db) == -M.closer_to_truth(db, da)
        assert M.closer_to_truth(da, da) == 0
    x = np.floor(rnd.uniform(60) * 3) - 1               # Werte -1, 0, 1
    y = np.floor(rnd.uniform(60) * 3) - 1
    assert M.disagreement_share(x, y) == pytest.approx(M.disagreement_share(y, x))
    assert M.disagreement_share(x, x) == 0.0 or math.isnan(M.disagreement_share(x, x))
    nonzero = x[x != 0]
    if len(nonzero):
        assert M.disagreement_share(nonzero, -nonzero) == 1.0
    assert math.isnan(M.disagreement_share([0, 0], [1, -1]))


# --- 9. Randfälle -----------------------------------------------------------------------------------------------------------------------

def test_single_and_two_participants():
    one = (0,)
    assert M.kendall_distance(one, one) == 0 and M.footrule(one, one) == 0
    assert math.isnan(M.kendall_tau(one, one)) and math.isnan(M.spearman_rho(one, one))
    assert M.rbo(one, one, 0.9) == pytest.approx(1.0) and M.topk_overlap(one, one, 1) == 1.0
    a, b = (0, 1), (1, 0)
    assert (M.kendall_distance(a, b), M.footrule(a, b)) == (1, 2)
    assert M.kendall_tau(a, b) == -1.0 and M.spearman_rho(a, b) == pytest.approx(-1.0)
    assert M.topk_overlap(a, b, 1) == 0.0 and M.topk_overlap(a, b, 2) == 1.0


def test_inputs_with_different_participants_or_invalid_parameters_are_rejected():
    with pytest.raises(ValueError):
        M.kendall_distance((0, 1, 2), (0, 1, 3))
    with pytest.raises(ValueError):
        M.footrule((0, 1, 2), (0, 1))
    with pytest.raises(ValueError):
        M.rbo((0, 1), (1, 0), 1.0)
    with pytest.raises(ValueError):
        M.rbo((0, 1), (1, 0), 0.0)
    with pytest.raises(ValueError):
        M.topk_overlap((0, 1), (1, 0), 0)
    with pytest.raises(ValueError):
        M.topk_overlap((0, 1), (1, 0), 3)
