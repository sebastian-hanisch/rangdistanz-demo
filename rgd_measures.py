"""Maße für den Abstand zweier Rangfolgen (nur numpy/Standardbibliothek). Eine Rangfolge ist eine Liste der Teilnehmerindizes, bester zuerst;
beide Rangfolgen enthalten dieselben Teilnehmer. Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b)."""

import math

import numpy as np

# Anzeige-Text je Maß: (Schlüssel, Name, Skala, Richtung, was es zählt)
MEASURE_INFO = {
    "kendall_distance": ("Kendall-Distanz K", "0 bis n(n-1)/2", "niedriger = ähnlicher", "Zahl der Paare, die beide Rangfolgen entgegengesetzt ordnen; jedes Paar zählt gleich"),
    "kendall_tau": ("Kendall-τ", "-1 bis 1", "höher = ähnlicher", "dasselbe als Korrelation: 1 − 2K / (n(n-1)/2)"),
    "footrule": ("Spearman-Footrule F", "0 bis n²/2 (abgerundet)", "niedriger = ähnlicher", "Summe der Platzunterschiede über alle Teilnehmer; ein weiter Sprung zählt mehr"),
    "spearman_rho": ("Spearman-ρ", "-1 bis 1", "höher = ähnlicher", "Korrelation der Plätze; große Sprünge zählen quadratisch"),
    "rbo": ("RBO (rangbiasierte Überlappung)", "0 bis 1", "höher = ähnlicher", "gewichtetes Mittel der Überlappung der obersten d Plätze; die Spitze zählt mehr"),
    "topk": ("Top-k-Überlappung", "0 bis 1", "höher = ähnlicher", "Anteil gemeinsamer Teilnehmer unter den ersten k; ignoriert alles dahinter"),
}


def check_pair(a, b):
    """Beide Rangfolgen müssen dieselben Teilnehmer enthalten."""
    if len(a) != len(b) or sorted(a) != sorted(b):
        raise ValueError("die beiden Rangfolgen enthalten nicht dieselben Teilnehmer")


def positions(order) -> np.ndarray:
    """order[j] = Teilnehmer auf Platz j  ->  pos[i] = Platz von Teilnehmer i (0 = bester)."""
    order = np.asarray(order, dtype=int)
    pos = np.empty(len(order), dtype=int)
    pos[order] = np.arange(len(order))
    return pos


def max_kendall(n: int) -> int:
    return n * (n - 1) // 2


def max_footrule(n: int) -> int:
    """Größte Footrule zweier Rangfolgen von n Teilnehmern: die vollständige Umkehr, floor(n²/2)."""
    return n * n // 2


def kendall_distance(a, b) -> int:
    """Zahl der Paare {i, j}, die a und b entgegengesetzt ordnen."""
    check_pair(a, b)
    pa, pb = positions(a), positions(b)
    iu = np.triu_indices(len(pa), 1)
    return int((np.sign(pa[iu[0]] - pa[iu[1]]) != np.sign(pb[iu[0]] - pb[iu[1]])).sum())


def kendall_tau(a, b) -> float:
    """τ = 1 - 2K / (n(n-1)/2); ohne Paare (n < 2) nan."""
    n = len(a)
    if n < 2:
        return float("nan")
    return 1.0 - 2.0 * kendall_distance(a, b) / max_kendall(n)


def footrule(a, b) -> int:
    """Summe der Platzunterschiede |pos_a(i) - pos_b(i)| über alle Teilnehmer."""
    check_pair(a, b)
    return int(np.abs(positions(a) - positions(b)).sum())


def spearman_rho(a, b) -> float:
    """ρ = 1 - 6 Σ d² / (n (n² - 1)); ohne Paare (n < 2) nan."""
    check_pair(a, b)
    n = len(a)
    if n < 2:
        return float("nan")
    d = positions(a) - positions(b)
    return 1.0 - 6.0 * float((d * d).sum()) / (n * (n * n - 1))


def topk_overlap(a, b, k: int) -> float:
    """Anteil der gemeinsamen Teilnehmer unter den ersten k beider Rangfolgen."""
    check_pair(a, b)
    if not 1 <= k <= len(a):
        raise ValueError(f"k = {k} liegt außerhalb von 1 bis {len(a)}")
    return len(set(list(a)[:k]) & set(list(b)[:k])) / k


def rbo(a, b, p: float) -> float:
    """Rangbiasierte Überlappung nach Webber, Moffat, Zobel (2010) in der Fassung dieser Demo: Mittel der Überlappungen A_d der obersten d
    Plätze mit Gewichten p^(d-1), abgeschnitten bei Tiefe n und auf [0, 1] normiert (alle Teilnehmer stehen in beiden Listen)."""
    check_pair(a, b)
    if not 0.0 < p < 1.0:
        raise ValueError("p muss zwischen 0 und 1 liegen")
    a, b = list(a), list(b)
    seen_a, seen_b = set(), set()
    num = den = 0.0
    for d in range(1, len(a) + 1):
        seen_a.add(a[d - 1])
        seen_b.add(b[d - 1])
        weight = p ** (d - 1)
        num += weight * len(seen_a & seen_b) / d
        den += weight
    return num / den if den else float("nan")


def measure_values(a, b, p: float, k: int) -> dict:
    """Alle Maße für ein Paar von Rangfolgen."""
    return {
        "kendall_distance": kendall_distance(a, b),
        "kendall_tau": kendall_tau(a, b),
        "footrule": footrule(a, b),
        "spearman_rho": spearman_rho(a, b),
        "rbo": rbo(a, b, p),
        "topk": topk_overlap(a, b, k),
    }


def normalised_distance(a, b, p: float, k: int) -> dict:
    """Vergleichbare Abstände auf [0, 1] (0 = gleich): K/Kmax, F/Fmax, 1 - RBO, 1 - Top-k. Die Skalen bleiben verschiedene Skalen: nur für die
    Anzeige gleicher Spannweite, nicht als Aussage, dass 0,2 bei einem Maß dasselbe heißt wie 0,2 bei einem anderen."""
    n = len(a)
    return {
        "Kendall": kendall_distance(a, b) / max_kendall(n) if n > 1 else 0.0,
        "Footrule": footrule(a, b) / max_footrule(n) if n > 1 else 0.0,
        "RBO": 1.0 - rbo(a, b, p),
        "Top-k": 1.0 - topk_overlap(a, b, k),
    }


def disagreement_share(closer_x, closer_y) -> float:
    """Anteil der Fälle, in denen zwei Maße verschieden entscheiden, welche Rangfolge näher liegt (+1: A näher, -1: B näher, 0: gleich);
    Fälle mit Gleichstand in einem der beiden Maße zählen nicht. Ohne zählbaren Fall: nan."""
    x, y = np.asarray(closer_x), np.asarray(closer_y)
    both = (x != 0) & (y != 0)
    if not both.any():
        return float("nan")
    return float((x[both] != y[both]).mean())


def closer_to_truth(distance_a: float, distance_b: float) -> int:
    """+1: A näher an der Wahrheit, -1: B näher, 0: gleich weit."""
    if math.isclose(distance_a, distance_b, rel_tol=0.0, abs_tol=1e-12):
        return 0
    return 1 if distance_a < distance_b else -1
