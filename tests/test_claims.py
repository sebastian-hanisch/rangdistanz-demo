"""JEDE Zahl und Aussage aus App-Texten und README wird hier nachgerechnet (über die festen Instanzen SWEEP_SEEDS, nie ein einzelner Seed).
Der Generator hängt nur von Seed und Position ab (SplitMix64), die Zahlen sind plattformunabhängig; Schwellen trotzdem mit Abstand zur Messung."""

import pytest

import rgd_constants as C
import rgd_evaluation as ev


@pytest.fixture(scope="module")
def adjacent():
    return {r["i"]: r for r in ev.sweep_adjacent()}


@pytest.fixture(scope="module")
def disagreement():
    return ev.sweep_disagreement()


@pytest.fixture(scope="module")
def footrule_kendall():
    return {r["n"]: r for r in ev.sweep_footrule_kendall()}


@pytest.fixture(scope="module")
def games():
    return {r["k"]: r for r in ev.sweep_games()}


# --- Experiment 1 ------------------------------------------------------------------------------------------------------------------------

def test_every_adjacent_swap_has_kendall_one_and_footrule_two(adjacent):
    assert len(adjacent) == 11
    assert {r["K"] for r in adjacent.values()} == {1} and {r["F"] for r in adjacent.values()} == {2}


def test_rbo_distance_of_the_top_and_bottom_swap_and_their_ratio(adjacent):
    assert adjacent[1]["rbo_dist"] == pytest.approx(0.139, abs=0.0005)       # 1 - 0,8606
    assert adjacent[11]["rbo_dist"] == pytest.approx(0.0044, abs=0.0002)     # 1 - 0,9956
    assert adjacent[1]["rbo_dist"] / adjacent[11]["rbo_dist"] == pytest.approx(32, abs=1)


def test_top3_overlap_notices_only_the_swap_across_the_boundary(adjacent):
    assert [i for i, r in adjacent.items() if r["topk"] < 1.0] == [3]
    assert adjacent[3]["topk"] == pytest.approx(2 / 3)


# --- Experiment 2 ------------------------------------------------------------------------------------------------------------------------

def test_disagreement_between_kendall_and_footrule_is_small_and_with_the_top_measures_larger(disagreement):
    m = disagreement["matrix"]
    assert m["Kendall"]["Footrule"] == pytest.approx(0.061, abs=0.003)
    assert m["Kendall"]["RBO"] == pytest.approx(0.199, abs=0.003)
    assert m["Kendall"]["Top-k"] == pytest.approx(0.143, abs=0.003)
    assert m["Kendall"]["Footrule"] < m["Kendall"]["Top-k"] < m["Kendall"]["RBO"]


def test_the_rate_table_is_closer_to_the_truth_in_most_runs(disagreement):
    assert disagreement["b_closer"]["Kendall"] == pytest.approx(0.704, abs=0.003)
    assert disagreement["a_closer"]["Kendall"] == pytest.approx(0.224, abs=0.003)
    assert disagreement["equal"]["Top-k"] > 0.4                               # Top-3 ist grob: oft gleich weit
    assert disagreement["runs"] == len(C.SWEEP_SEEDS) == 500


# --- Experiment 3 ------------------------------------------------------------------------------------------------------------------------

def test_diaconis_graham_holds_in_all_8000_permutations(footrule_kendall):
    assert all(r["holds"] for r in footrule_kendall.values())
    assert sum(r["count"] for r in footrule_kendall.values()) == 8000


def test_footrule_over_kendall_ranges_and_means(footrule_kendall):
    assert min(r["min"] for r in footrule_kendall.values()) == pytest.approx(1.09, abs=0.005)
    assert max(r["max"] for r in footrule_kendall.values()) == pytest.approx(2.0, abs=1e-9)
    for n, mean in ((4, 1.77), (8, 1.53), (12, 1.46), (16, 1.42)):
        assert footrule_kendall[n]["mean"] == pytest.approx(mean, abs=0.01), n


def test_full_reversal_values_for_n_12(footrule_kendall):
    assert footrule_kendall[12]["reversal_K"] == 66 and footrule_kendall[12]["reversal_F"] == 72


# --- Experiment 4 ------------------------------------------------------------------------------------------------------------------------

def test_measures_and_first_place_against_the_number_of_games(games):
    assert games[1]["tau"] == pytest.approx(0.54, abs=0.006) and games[1]["first"] == pytest.approx(0.426, abs=0.001)
    assert games[10]["tau"] == pytest.approx(0.88, abs=0.006) and games[10]["topk"] == pytest.approx(0.925, abs=0.001)
    assert games[10]["first"] == pytest.approx(0.764, abs=0.001)
    assert games[40]["tau"] == pytest.approx(0.98, abs=0.006) and games[40]["first"] == pytest.approx(0.932, abs=0.001)


def test_the_first_place_lags_the_global_measures_at_ten_games(games):
    assert games[10]["first"] < games[10]["topk"] < 1.0
    assert (1 + games[10]["tau"]) / 2 > games[10]["first"]


# --- Texte -------------------------------------------------------------------------------------------------------------------------------

def test_verdicts_quote_the_measured_values(adjacent, disagreement, footrule_kendall, games):
    level, text = ev.verdict_adjacent(list(adjacent.values()))
    assert "32-Fache" in text and "0,139" in text and "0,004" in text and "3 | 4" in text
    level, text = ev.verdict_disagreement(disagreement)
    assert ev.pct1(disagreement["matrix"]["Kendall"]["Footrule"]) in text and ev.pct1(disagreement["matrix"]["Kendall"]["RBO"]) in text
    level, text = ev.verdict_footrule_kendall(list(footrule_kendall.values()))
    assert level == "info" and "gilt in allen 8000" in text
    level, text = ev.verdict_games(list(games.values()))
    assert ev.pct1(games[10]["first"]) in text and ev.de(games[10]["tau"]) in text
