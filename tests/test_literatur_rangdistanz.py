"""Literatur-Referenzwerte zu Kendall-Distanz, Footrule und Spearman-ρ (ORACLE-PLAYBOOK §5.1). Einsicht jeweils am 2026-10-17.

Q1  Cornwell, C., McNew, N. (2024): Links and the Diaconis-Graham inequality. arXiv:2404.16755v1 (PDF-Volltext gelesen).
    - Abschnitt 1, Gleichung (1) (Diaconis, Graham 1977): I(π) + T(π) <= D(π) <= 2 I(π); I = Inversionen, D = Σ|π_i - i| (Footrule),
      T = n - (Zahl der Zyklen) (Cayley); Gleichheit D = 2I genau dann, wenn π kein Muster 321 enthält.
    - Abbildung 6, Bildunterschrift: π = 246198375 hat D = 24, I = 14; π' = 635721948 hat D = 26, I = 16; π'' = 974683215 hat D = 38,
      I = 28 (n = 9).
    Das Original von Diaconis, Graham (1977) wurde nicht eingesehen.
Q2  Ekhad, S. B., Zeilberger, D. (2021): An Experimental (yet fully rigorous!) Study of a certain "Measure Of Disarray" that 12-year
    Noga Alon Proved was always Even. arXiv:2109.14089v2 (PDF-Volltext gelesen), Abschnitt "Diaconis and Graham ... human ingenuity":
    Für gleichverteilte Permutationen der Länge n hat die Footrule den Mittelwert (n-1)(n+1)/3 und die Varianz (n+1)(2n^2+7)/45
    (zitiert nach Diaconis, Graham 1977); die Footrule ist stets gerade.
Q3  Wikipedia, "Kendall tau distance" (https://en.wikipedia.org/wiki/Kendall_tau_distance, über WebFetch eingesehen): Beispiel mit
    Rangfolgen A>B>C>D>E gegen C>D>A>B>E, vier entgegengesetzt geordnete Paare (A,C), (A,D), (B,C), (B,D), Distanz 4, normiert 0,4;
    zweites Beispiel A>B>C>D gegen B>D>A>C, Distanz 3. Beide Zählungen zusätzlich von Hand nachgezählt.
Q4  Wikipedia, "Kendall rank correlation coefficient" (https://en.wikipedia.org/wiki/Kendall_rank_correlation_coefficient, Abschnitt
    "Hypothesis test", über WebFetch eingesehen): τ = 1 - 2 (Zahl diskordanter Paare)/C(n,2) ohne Gleichstände; unter Unabhängigkeit
    Var[τ_A] = 2(2n+5)/(9n(n-1)).
Q5  Wikipedia, "Spearman's rank correlation coefficient" (https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient,
    über WebFetch eingesehen, Beispiel IQ gegen Fernsehstunden): IQ 106,100,86,101,99,103,97,113,112,110 und Stunden
    7,27,2,50,28,29,20,12,6,17; Σd² = 194, n = 10, ρ = -29/165 ≈ -0,1758. Rangtabelle von Hand nachgerechnet (stimmt).

Nicht eingesehen und deshalb ohne Test: Webber, Moffat, Zobel (2010) zum RBO (nur die Autorenseite, kein Volltext erreichbar),
Kendall (1938), Spearman (1904), Diaconis, Graham (1977) im Original.
"""

import itertools
from fractions import Fraction

import pytest

import rgd_measures as M


def inverse(p):
    inv = [0] * len(p)
    for i, v in enumerate(p):
        inv[v] = i
    return tuple(inv)


def to_order(one_line):
    """Permutation π in Einzeilenschreibweise (1-basiert) als Rangfolge: die Demo vergleicht `order` mit der Identität."""
    return tuple(v - 1 for v in one_line)


# --- Q1: Beispiele und Ungleichung -------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("pi, D, I", [
    ("246198375", 24, 14),
    ("635721948", 26, 16),
    ("974683215", 38, 28),
])
def test_footrule_and_inversions_of_the_permutations_in_figure_6_of_cornwell_mcnew(pi, D, I):
    order = to_order([int(c) for c in pi])
    identity = tuple(range(9))
    assert M.footrule(order, identity) == D
    assert M.kendall_distance(order, identity) == I
    assert M.footrule(identity, order) == D and M.kendall_distance(identity, order) == I


def count_cycles(p):
    seen, cycles = set(), 0
    for i in range(len(p)):
        if i not in seen:
            cycles += 1
            while i not in seen:
                seen.add(i)
                i = p[i]
    return cycles


def has_321(p):
    n = len(p)
    return any(p[i] > p[j] > p[k] for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n))


def test_diaconis_graham_inequalities_with_the_cayley_distance_for_all_permutations_up_to_n_7():
    """I + T <= D <= 2I mit T = n - Zyklen und der Gleichheitsfall D = 2I <=> kein Muster 321, exhaustiv für n = 1 bis 7."""
    for n in range(1, 8):
        identity = tuple(range(n))
        for p in itertools.permutations(range(n)):
            I = M.kendall_distance(p, identity)
            D = M.footrule(p, identity)
            T = n - count_cycles(p)
            assert I + T <= D <= 2 * I
            assert (D == 2 * I) == (not has_321(p))


# --- Q2: Mittelwert und Varianz der Footrule -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 7])
def test_footrule_mean_and_variance_over_all_permutations_match_diaconis_graham(n):
    identity = tuple(range(n))
    values = [M.footrule(p, identity) for p in itertools.permutations(range(n))]
    count = len(values)
    mean = Fraction(sum(values), count)
    var = Fraction(sum(v * v for v in values), count) - mean * mean
    assert mean == Fraction((n - 1) * (n + 1), 3)
    assert var == Fraction((n + 1) * (2 * n * n + 7), 45)
    assert all(v % 2 == 0 for v in values)


# --- Q3: Kendall-Distanz, Beispiele ----------------------------------------------------------------------------------------------------------

def test_kendall_tau_distance_examples_from_wikipedia():
    idx = {c: i for i, c in enumerate("ABCDE")}
    height = tuple(idx[c] for c in "ABCDE")                 # A>B>C>D>E
    weight = tuple(idx[c] for c in "CDABE")                 # C>D>A>B>E
    assert M.kendall_distance(height, weight) == 4
    assert M.kendall_distance(height, weight) / M.max_kendall(5) == pytest.approx(0.4)
    assert M.kendall_tau(height, weight) == pytest.approx(1 - 2 * 4 / 10)
    first = tuple(idx[c] for c in "ABCD")                   # A>B>C>D
    second = tuple(idx[c] for c in "BDAC")                  # B>D>A>C
    assert M.kendall_distance(first, second) == 3


# --- Q4: Varianz von τ unter Unabhängigkeit ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("n", [3, 4, 5, 6, 7])
def test_null_variance_of_kendall_tau_matches_the_formula(n):
    identity = tuple(range(n))
    taus = [Fraction(M.max_kendall(n) - 2 * M.kendall_distance(p, identity), M.max_kendall(n))
            for p in itertools.permutations(range(n))]
    mean = sum(taus) / len(taus)
    var = sum(t * t for t in taus) / len(taus) - mean * mean
    assert mean == 0
    assert var == Fraction(2 * (2 * n + 5), 9 * n * (n - 1))
    # und die Demo-τ stimmt mit 1 - 2K/C(n,2) überein
    p = tuple(reversed(identity))
    assert M.kendall_tau(p, identity) == -1.0


# --- Q5: Spearman-Beispiel ------------------------------------------------------------------------------------------------------------------

def test_spearman_rho_of_the_iq_television_example_from_wikipedia():
    iq = [106, 100, 86, 101, 99, 103, 97, 113, 112, 110]
    tv = [7, 27, 2, 50, 28, 29, 20, 12, 6, 17]
    people = range(10)
    by_iq = tuple(sorted(people, key=lambda i: iq[i]))      # aufsteigend: Rang 1 = kleinster Wert
    by_tv = tuple(sorted(people, key=lambda i: tv[i]))
    assert M.spearman_rho(by_iq, by_tv) == pytest.approx(-29 / 165)
    # Σd² = 194 aus der Tabelle der Quelle, unabhängig von der Demo ausgerechnet
    pos_iq = {p: r for r, p in enumerate(by_iq)}
    pos_tv = {p: r for r, p in enumerate(by_tv)}
    assert sum((pos_iq[p] - pos_tv[p]) ** 2 for p in people) == 194
    # dieselbe Korrelation, wenn beide Rangfolgen absteigend gebildet werden
    assert M.spearman_rho(tuple(reversed(by_iq)), tuple(reversed(by_tv))) == pytest.approx(-29 / 165)
