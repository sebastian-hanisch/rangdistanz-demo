"""Einheitentests der Maße gegen die von Hand gerechnete Mini-Instanz (conftest.py)."""

import math

import pytest

import rgd_measures as M


def test_mini_instance_hand_values(mini):
    a, b = mini
    assert M.kendall_distance(a, b) == 2
    assert M.kendall_tau(a, b) == pytest.approx(1 / 3)
    assert M.footrule(a, b) == 4
    assert M.footrule(a, b) / M.max_footrule(4) == pytest.approx(0.5)
    assert M.spearman_rho(a, b) == pytest.approx(0.6)
    assert M.topk_overlap(a, b, 2) == 1.0
    assert M.topk_overlap(a, b, 1) == 0.0
    assert M.rbo(a, b, 0.5) == pytest.approx(19 / 45)


def test_identical_rankings_are_at_distance_zero():
    a = (3, 1, 0, 2)
    assert M.kendall_distance(a, a) == 0 and M.footrule(a, a) == 0
    assert M.kendall_tau(a, a) == 1.0 and M.spearman_rho(a, a) == 1.0
    assert M.rbo(a, a, 0.9) == pytest.approx(1.0) and M.topk_overlap(a, a, 2) == 1.0


def test_full_reversal_reaches_the_maxima_for_even_and_odd_n():
    for n in (2, 3, 4, 5, 8, 11):
        a, b = tuple(range(n)), tuple(range(n - 1, -1, -1))
        assert M.kendall_distance(a, b) == M.max_kendall(n)
        assert M.footrule(a, b) == M.max_footrule(n)
        assert M.kendall_tau(a, b) == pytest.approx(-1.0)
        assert M.spearman_rho(a, b) == pytest.approx(-1.0)


def test_max_footrule_is_floor_of_half_n_squared():
    assert [M.max_footrule(n) for n in (2, 3, 4, 5, 6)] == [2, 4, 8, 12, 18]


def test_pair_must_contain_the_same_participants():
    with pytest.raises(ValueError):
        M.kendall_distance((0, 1, 2), (0, 1))
    with pytest.raises(ValueError):
        M.footrule((0, 1, 2), (0, 1, 3))
    with pytest.raises(ValueError):
        M.rbo((0, 1), (0, 2), 0.5)


def test_parameter_bounds_are_enforced():
    with pytest.raises(ValueError):
        M.topk_overlap((0, 1, 2), (0, 1, 2), 0)
    with pytest.raises(ValueError):
        M.topk_overlap((0, 1, 2), (0, 1, 2), 4)
    for p in (0.0, 1.0, -0.2, 1.5):
        with pytest.raises(ValueError):
            M.rbo((0, 1), (0, 1), p)


def test_measures_are_symmetric_in_their_arguments():
    a, b = (0, 3, 1, 4, 2), (2, 0, 4, 1, 3)
    assert M.kendall_distance(a, b) == M.kendall_distance(b, a)
    assert M.footrule(a, b) == M.footrule(b, a)
    assert M.spearman_rho(a, b) == pytest.approx(M.spearman_rho(b, a))
    assert M.topk_overlap(a, b, 3) == M.topk_overlap(b, a, 3)
    assert M.rbo(a, b, 0.8) == pytest.approx(M.rbo(b, a, 0.8))


def test_single_participant_has_no_pairs():
    assert math.isnan(M.kendall_tau((0,), (0,))) and math.isnan(M.spearman_rho((0,), (0,)))
    assert M.kendall_distance((0,), (0,)) == 0


def test_a_swap_at_the_top_weighs_more_for_rbo_than_a_swap_at_the_bottom_but_equal_for_kendall_and_footrule():
    ref = tuple(range(12))
    top = (1, 0) + tuple(range(2, 12))
    bottom = tuple(range(10)) + (11, 10)
    assert M.kendall_distance(ref, top) == M.kendall_distance(ref, bottom) == 1
    assert M.footrule(ref, top) == M.footrule(ref, bottom) == 2
    assert 1 - M.rbo(ref, top, 0.9) > 20 * (1 - M.rbo(ref, bottom, 0.9))


def test_rbo_depends_on_p_and_a_small_p_concentrates_on_the_top():
    ref = tuple(range(12))
    tail = tuple(range(10)) + (11, 10)         # nur das Ende weicht ab
    assert 1 - M.rbo(ref, tail, 0.5) < 1 - M.rbo(ref, tail, 0.99)


def test_measure_values_and_normalised_distance_on_the_mini_instance(mini):
    a, b = mini
    v = M.measure_values(a, b, 0.5, 2)
    assert set(v) == set(M.MEASURE_INFO)
    assert v["kendall_distance"] == 2 and v["footrule"] == 4
    d = M.normalised_distance(a, b, 0.5, 2)
    assert d["Kendall"] == pytest.approx(2 / 6) and d["Footrule"] == pytest.approx(0.5)
    assert d["RBO"] == pytest.approx(1 - 19 / 45) and d["Top-k"] == pytest.approx(0.0)


def test_normalised_distance_edge_cases_n1_and_n2():
    one = M.normalised_distance((0,), (0,), 0.9, 1)
    assert one["Kendall"] == 0.0 and one["Footrule"] == 0.0
    two = M.normalised_distance((0, 1), (1, 0), 0.9, 1)
    assert two["Kendall"] == 1.0 and two["Footrule"] == 1.0     # n = 2: ein Paar, vollständig umgekehrt
    assert two["Top-k"] == 1.0 and two["RBO"] == pytest.approx(1 - M.rbo((0, 1), (1, 0), 0.9))


def test_rbo_is_unchanged_when_the_weights_are_rescaled_by_a_constant():
    """Die Normierung kürzt einen gemeinsamen Faktor: das Maß hängt nur vom Verhältnis der Gewichte ab (p), nicht von deren Skala."""
    a, b = (0, 1, 2, 3, 4), (1, 0, 3, 2, 4)
    p = 0.7
    num = sum(p ** d * len(set(a[: d + 1]) & set(b[: d + 1])) / (d + 1) for d in range(5))     # Gewichte p^d statt p^(d-1)
    den = sum(p ** d for d in range(5))
    assert M.rbo(a, b, p) == pytest.approx(num / den)


def test_disagreement_share_hand_instance():
    x = [1, 1, -1, 0, 1]
    y = [1, -1, -1, 1, 0]
    # beide ungleich null: Index 0 (gleich), 1 (verschieden), 2 (gleich) -> 1/3; Index 3 und 4 zählen nicht
    assert M.disagreement_share(x, y) == pytest.approx(1 / 3)
    assert math.isnan(M.disagreement_share([0, 0], [1, -1]))


def test_closer_to_truth_sign_convention():
    assert M.closer_to_truth(2, 3) == 1      # A näher
    assert M.closer_to_truth(3, 2) == -1     # B näher
    assert M.closer_to_truth(2, 2) == 0
    assert M.closer_to_truth(0.1 + 0.2, 0.3) == 0    # Rundungsrauschen zählt nicht als Unterschied
