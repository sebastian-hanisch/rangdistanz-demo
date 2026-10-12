"""Einheitentests der Abweichungs-Bauer und der Tabellen aus dem Turnier."""

import pytest

import rgd_measures as M
import rgd_perturb as P
import turnier_generator as T


def test_swap_adjacent_hand_instances_and_bounds():
    assert P.swap_adjacent((0, 1, 2, 3), 1) == (1, 0, 2, 3)
    assert P.swap_adjacent((0, 1, 2, 3), 2) == (0, 2, 1, 3)
    assert P.swap_adjacent((0, 1, 2, 3), 3) == (0, 1, 3, 2)
    for bad in (0, 4):
        with pytest.raises(ValueError):
            P.swap_adjacent((0, 1, 2, 3), bad)


def test_move_by_down_up_and_clamped():
    ref = (0, 1, 2, 3, 4)
    assert P.move_by(ref, 1, 2) == (1, 2, 0, 3, 4)       # Platz 1 rutscht um 2 ab
    assert P.move_by(ref, 4, -2) == (0, 3, 1, 2, 4)      # Platz 4 rückt um 2 vor
    assert P.move_by(ref, 4, 10) == (0, 1, 2, 4, 3)      # am unteren Rand begrenzt
    assert P.move_by(ref, 2, -10) == (1, 0, 2, 3, 4)     # am oberen Rand begrenzt
    assert P.move_by(ref, 3, 0) == ref
    with pytest.raises(ValueError):
        P.move_by(ref, 6, 1)


def test_move_by_changes_kendall_by_the_distance_moved():
    ref = tuple(range(8))
    for i in (1, 3, 6):
        for d in (1, 2, 4):
            moved = P.move_by(ref, i, d)
            target = min(7, i - 1 + d)
            assert M.kendall_distance(ref, moved) == target - (i - 1)


def test_reverse_lower_half():
    assert P.reverse_lower_half((0, 1, 2, 3, 4, 5)) == (0, 1, 2, 5, 4, 3)
    assert P.reverse_lower_half((0, 1, 2, 3, 4)) == (0, 1, 2, 4, 3)       # n // 2 = 2 Plätze
    assert P.reverse_lower_half((0, 1, 2)) == (0, 1, 2)                   # n // 2 = 1: nichts umzukehren
    assert P.reverse_lower_half((0, 1)) == (0, 1)


def test_random_adjacent_swaps_are_deterministic_permutations_with_parity():
    ref = tuple(range(10))
    for m in (0, 1, 2, 5, 9):
        out = P.random_adjacent_swaps(ref, m, T.SplitMix64(11))
        assert sorted(out) == list(ref)
        assert out == P.random_adjacent_swaps(ref, m, T.SplitMix64(11))
        K = M.kendall_distance(ref, out)
        assert K <= m and K % 2 == m % 2           # jeder Nachbartausch ändert K um genau 1
    assert P.random_adjacent_swaps(ref, 0, T.SplitMix64(1)) == ref
    assert len({P.random_adjacent_swaps(ref, 4, T.SplitMix64(s)) for s in range(30)}) > 5


def test_random_adjacent_swaps_reach_every_neighbour_pair_including_the_last():
    """Ein Tausch trifft jede der n-1 Stellen 0 .. n-2; die letzte (Plätze n-1 und n) darf nicht ausgelassen werden."""
    n = 6
    ref = tuple(range(n))
    hit = set()
    for s in range(200):
        out = P.random_adjacent_swaps(ref, 1, T.SplitMix64(s))
        hit.add(next(i for i in range(n - 1) if out[i] != ref[i]))
    assert hit == set(range(n - 1))


def test_table_order_sorts_by_score_and_breaks_ties_by_lot():
    score = [3.0, 1.0, 3.0, 0.0]
    seen = set()
    for s in range(40):
        order = P.table_order(score, T.SplitMix64(s))
        assert set(order[:2]) == {0, 2} and order[2] == 1 and order[3] == 3
        seen.add(order)
        assert order == P.table_order(score, T.SplitMix64(s))
    assert len(seen) == 2                          # beide Reihenfolgen der Gleichstehenden kommen vor


def test_truth_order_puts_the_strongest_first():
    assert P.truth_order(4) == (3, 2, 1, 0)


def test_tables_from_turnier_are_permutations_and_reproducible():
    truth, by_wins, by_rate, names = P.tables_from_turnier(8, 0.3, 3, "luecken", 0.5, 4242)
    for order in (truth, by_wins, by_rate):
        assert sorted(order) == list(range(8))
    assert len(names) == 8
    assert (truth, by_wins, by_rate) == P.tables_from_turnier(8, 0.3, 3, "luecken", 0.5, 4242)[:3]


def test_many_games_bring_the_table_close_to_the_truth_few_games_do_not():
    close = [M.kendall_tau(P.tables_from_turnier(8, 0.3, 200, "vollstaendig", 1.0, s)[1], P.truth_order(8)) for s in range(20)]
    noisy = [M.kendall_tau(P.tables_from_turnier(8, 0.3, 1, "vollstaendig", 1.0, s)[1], P.truth_order(8)) for s in range(20)]
    assert sum(close) / 20 > 0.95 > sum(noisy) / 20 + 0.2
