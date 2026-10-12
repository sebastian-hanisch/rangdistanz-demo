"""Analyse, Szenario und Verdikte; Randfälle der Regler."""

import math

import pytest

import rgd_constants as C
import rgd_evaluation as ev
import rgd_measures as M
from rgd_scenario import Settings, clamp_settings, make_pair


def test_analyse_covers_every_art_at_the_slider_extremes():
    for art in C.ART_LABELS:
        for n in (C.N_MIN, C.N_MAX):
            for i, d, m, k in ((1, C.D_MIN, C.M_MIN, C.K_MIN), (C.N_MAX, C.D_MAX, C.M_MAX, C.K_MAX)):
                a = ev.analyse(Settings(n=n, art=art, i=i, d=d, m=m, k=k, topk=C.N_MAX, seed=5))
                assert sorted(a.pair.a) == sorted(a.pair.b) == list(range(n))
                assert 0 <= a.distances["Kendall"] <= 1 and 0 <= a.distances["Footrule"] <= 1


def test_clamp_settings_brings_values_into_range():
    s = clamp_settings(Settings(n=4, art="tausch", i=15, d=15, topk=9))
    assert s.i == 3 and s.d == 3 and s.topk == 2
    s = clamp_settings(Settings(n=4, art="verschiebung", i=15))
    assert s.i == 4
    assert clamp_settings(Settings(n=16, art="tausch", i=0)).i == 1


def test_moved_participants_are_exactly_those_whose_place_differs():
    p = make_pair(Settings(n=8, art="tausch", i=3))
    assert set(p.moved) == {2, 3}
    p = make_pair(Settings(n=8, art="untere_haelfte"))
    assert set(p.moved) == {4, 5, 6, 7}
    p = make_pair(Settings(n=8, art="verschiebung", i=2, d=3))
    assert set(p.moved) == {1, 2, 3, 4}


def test_turnier_art_compares_truth_with_the_table():
    p = make_pair(Settings(n=8, art="turnier", k=4, seed=9))
    assert p.a == tuple(range(7, -1, -1))
    assert p.label_a.startswith("Wahre Ordnung") and p.label_b == "Tabelle nach Siegen"


def test_unknown_art_raises():
    with pytest.raises(ValueError):
        make_pair(Settings(art="chaos"))


def test_identical_rankings_give_the_equal_verdict():
    """Zwei zufällige Nachbartausche an derselben Stelle heben sich auf; bei n = 4 gibt es dafür unter den Seeds genug Treffer."""
    equal = [s for s in range(300) if ev.analyse(Settings(n=4, art="zufall", m=2, seed=s)).values["kendall_distance"] == 0]
    assert len(equal) > 20
    level, text = ev.verdict_analysis(ev.analyse(Settings(n=4, art="zufall", m=2, seed=equal[0])))
    assert level == "info" and "gleich" in text and "Abstand 0" in text


def test_verdict_levels_depend_on_the_spread_between_measures():
    top = ev.analyse(Settings(n=12, art="tausch", i=1))
    assert ev.verdict_analysis(top)[0] == "warning" and "verschieden stark" in ev.verdict_analysis(top)[1]
    end = ev.analyse(Settings(n=12, art="tausch", i=11))
    level, text = ev.verdict_analysis(end)
    assert level == "info" and "ähnlich stark" in text
    half = ev.analyse(Settings(n=12, art="untere_haelfte"))
    assert ev.verdict_analysis(half)[0] == "warning"          # die Spitze steht still, 15 Paare sind falsch


def test_verdict_adjacent_names_the_ratio_and_the_crossing():
    rows = ev.sweep_adjacent()
    level, text = ev.verdict_adjacent(rows)
    assert level == "warning" and "32-Fache" in text and "3 | 4" in text


def test_sweep_adjacent_has_one_row_per_neighbour_pair_and_constant_k_and_f():
    rows = ev.sweep_adjacent(n=10)
    assert [r["i"] for r in rows] == list(range(1, 10))
    assert {r["K"] for r in rows} == {1} and {r["F"] for r in rows} == {2}


def test_sweep_disagreement_matrix_is_symmetric_and_in_range():
    res = ev.sweep_disagreement(seeds=C.SWEEP_SEEDS[:80])
    for x in res["measures"]:
        for y in res["measures"]:
            if x == y:
                assert res["matrix"][x][y] is None
            else:
                v = res["matrix"][x][y]
                assert math.isnan(v) or 0.0 <= v <= 1.0
                assert (math.isnan(v) and math.isnan(res["matrix"][y][x])) or v == res["matrix"][y][x]
    for m in res["measures"]:
        assert res["a_closer"][m] + res["b_closer"][m] + res["equal"][m] == pytest.approx(1.0)


def test_sweep_footrule_kendall_reversal_maxima():
    for r in ev.sweep_footrule_kendall(ns=(4, 6), count=50):
        assert r["reversal_K"] == M.max_kendall(r["n"]) and r["reversal_F"] == M.max_footrule(r["n"])
        assert r["holds"] and 1.0 <= r["min"] <= r["mean"] <= r["max"] <= 2.0


def test_sweep_games_improves_with_more_games():
    rows = ev.sweep_games(ks=(1, 40), seeds=C.SWEEP_SEEDS[:60])
    assert rows[1]["tau"] > rows[0]["tau"] and rows[1]["first"] > rows[0]["first"] and rows[1]["f_norm"] < rows[0]["f_norm"]


def test_decimal_comma_helpers():
    assert ev.de(0.5) == "0,50" and ev.de(3.14159, 3) == "3,142"
    assert ev.pct(0.405) in ("40", "41") and ev.pct1(0.0614) == "6,1"
