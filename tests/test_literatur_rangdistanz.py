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

Q6  Webber, W., Moffat, A., Zobel, J. (2010): A similarity measure for indefinite rankings. ACM TOIS 28 (4), Autorenfassung (PDF-Volltext,
    codalism.com/research/papers/wmz10_tois.pdf, gelesen am 2026-10-17). Abschnitt 4.1: Gl. (3) Agreement A_d = X_d/d, Gl. (7) RBO = (1-p) Σ p^(d-1) A_d;
    Abschnitt 4.2: Gl. (11) RBO_MIN, Gl. (13)-(18) Rest RBO_RES; Abschnitt 4.3: Gl. (21) Gewicht der ersten d Ränge, "p = 0.9 means that the first 10
    ranks have 86% of the weight"; Abschnitt 4.4: Basiswert 0,767 bei 7 identischen Ergebnissen und p = 0,9, Gl. (23) RBO_EXT.

Nicht eingesehen und deshalb ohne Test: Kendall (1938), Spearman (1904), Diaconis, Graham (1977) im Original.
"""

import itertools
import math
import random
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


# --- Q6: Webber, Moffat, Zobel (2010), RBO --------------------------------------------------------------------------------------------

def _rbo_min(X, p):
    """Gl. (11): RBO_MIN(S,T,p,k) = (1-p)/p * ( Σ_{d=1}^k (X_d - X_k) p^d / d  -  X_k ln(1-p) ); X_d = Überlappung bis Tiefe d."""
    k, Xk = len(X), X[-1]
    return (1 - p) / p * (sum((X[d - 1] - Xk) * p ** d / d for d in range(1, k + 1)) - Xk * math.log(1 - p))


def _rbo_res(X, p, tail=5000):
    """Gl. (13): Rest RBO_RES = (1-p) ( Σ_{d=k+1}^f 2(d-k)/d p^(d-1) + Σ_{d>f} (1 - X_k/d) p^(d-1) ), f = 2k - X_k (Summe bei `tail` abgebrochen)."""
    k, Xk = len(X), X[-1]
    f = 2 * k - Xk
    head = sum(2 * (d - k) / d * p ** (d - 1) for d in range(k + 1, f + 1))
    rest = sum((1 - Xk / d) * p ** (d - 1) for d in range(f + 1, tail))
    return (1 - p) * (head + rest)


def _rbo_ext(X, p):
    """Gl. (23): RBO_EXT = X_k/k p^k + (1-p)/p Σ_{d=1}^k (X_d/d) p^d."""
    k = len(X)
    return X[-1] / k * p ** k + (1 - p) / p * sum(X[d - 1] / d * p ** d for d in range(1, k + 1))


def _overlaps(a, b):
    return [len(set(a[:d]) & set(b[:d])) for d in range(1, len(a) + 1)]


def test_webber_moffat_zobel_numbers_for_the_prefix_bounds_and_rank_weights():
    """Q6, Abschnitt 4.2 bis 4.4 (Autorenfassung, PDF-Volltext von codalism.com/research/papers/wmz10_tois.pdf, Einsicht 2026-10-17):
    - Zehn Ergebnisse, p = 0,9: größter Rest 0,254 (Spanne 0,000 bis 0,254, präfixfremd), kleinster Rest 0,144 (Spanne 0,856 bis 1,000, gleiche Präfixe).
    - Zwei Suchmaschinen mit je 7 identischen Ergebnissen, p = 0,9: Basiswert (RBO_MIN) nur 0,767.
    - p = 0,9: die ersten 10 Ränge haben 86 % des Gewichts (Gl. 21); für die ersten 50 Ränge etwa dasselbe Gewicht braucht p = 0,98."""
    p = 0.9
    ident10 = list(range(1, 11))
    assert _rbo_min(ident10, p) == pytest.approx(0.856, abs=5e-4)
    assert _rbo_res(ident10, p) == pytest.approx(0.144, abs=5e-4)
    assert _rbo_min(ident10, p) + _rbo_res(ident10, p) == pytest.approx(1.0, abs=1e-9)
    disjoint10 = [0] * 10
    assert _rbo_min(disjoint10, p) == pytest.approx(0.0, abs=1e-12)
    assert _rbo_res(disjoint10, p) == pytest.approx(0.254, abs=5e-4)
    assert _rbo_min(list(range(1, 8)), p) == pytest.approx(0.767, abs=5e-4)

    def weight_of_prefix(d, q):                                  # Gl. (21)
        return 1 - q ** (d - 1) + (1 - q) / q * d * (math.log(1 / (1 - q)) - sum(q ** i / i for i in range(1, d)))

    assert weight_of_prefix(10, 0.9) == pytest.approx(0.86, abs=5e-3)
    assert weight_of_prefix(50, 0.98) == pytest.approx(0.86, abs=0.01)
    # das Gewicht der ersten d Ränge ist die Summe der Rangegewichte Gl. (19): (1-p)/p Σ_{i>=j} p^i / i
    q = 0.9
    ranks = [(1 - q) / q * sum(q ** i / i for i in range(j, 3000)) for j in range(1, 11)]
    assert sum(ranks) == pytest.approx(weight_of_prefix(10, q), abs=1e-9)


@pytest.mark.parametrize("p", [0.5, 0.8, 0.9, 0.95])
def test_demo_rbo_is_the_prefix_score_of_equation_7_divided_by_one_minus_p_to_the_n_and_respects_the_paper_bounds(p):
    """Q6, Gl. (7): RBO = (1-p) Σ p^(d-1) A_d mit A_d = X_d/d. Die Demo rechnet die Summe nur bis zur Tiefe n und teilt durch Σ_{d<=n} p^(d-1);
    das ist der Präfixwert RBO@n der Quelle geteilt durch (1-p) Σ_{d<=n} p^(d-1) = 1 - p^n, also eine eigene Normierung, keine der Quelle.
    Die Quelle sagt außerdem: RBO@k < RBO_MIN <= RBO_EXT <= RBO_MAX (Abschnitt 4.2 und 4.4)."""
    n = 10
    ref = tuple(range(n))
    r = random.Random(11)
    checked = 0
    for _ in range(40):
        other = list(range(n))
        r.shuffle(other)
        X = _overlaps(ref, other)
        prefix = (1 - p) * sum(p ** (d - 1) * X[d - 1] / d for d in range(1, n + 1))
        assert M.rbo(ref, tuple(other), p) * (1 - p ** n) == pytest.approx(prefix, abs=1e-12)
        lo = _rbo_min(X, p)
        assert prefix <= lo + 1e-12
        assert lo <= _rbo_ext(X, p) + 1e-12 <= lo + _rbo_res(X, p) + 1e-9
        checked += 1
    assert checked == 40
    assert M.rbo(ref, ref, p) == pytest.approx(1.0, abs=1e-12)
