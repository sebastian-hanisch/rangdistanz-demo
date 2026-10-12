"""Abweichungen von einer Referenz-Rangfolge und Tabellen aus dem Turnier der Wurzel. Zufall nur über einen übergebenen SplitMix64."""

import numpy as np

import turnier_generator as T


def swap_adjacent(order, i: int) -> tuple:
    """Tauscht die Teilnehmer auf den Plätzen i und i+1 (i zählt ab 1)."""
    o = list(order)
    if not 1 <= i <= len(o) - 1:
        raise ValueError(f"i = {i} liegt außerhalb von 1 bis {len(o) - 1}")
    o[i - 1], o[i] = o[i], o[i - 1]
    return tuple(o)


def move_by(order, i: int, d: int) -> tuple:
    """Der Teilnehmer auf Platz i (ab 1) rutscht um d Plätze nach hinten (d > 0) oder rückt nach vorn (d < 0); an den Rändern begrenzt."""
    o = list(order)
    if not 1 <= i <= len(o):
        raise ValueError(f"i = {i} liegt außerhalb von 1 bis {len(o)}")
    target = max(0, min(len(o) - 1, (i - 1) + d))
    person = o.pop(i - 1)
    o.insert(target, person)
    return tuple(o)


def reverse_lower_half(order) -> tuple:
    """Kehrt die hintere Hälfte (die letzten n // 2 Plätze) um."""
    o = list(order)
    h = len(o) // 2
    if h < 2:
        return tuple(o)
    return tuple(o[: len(o) - h] + o[len(o) - h:][::-1])


def random_adjacent_swaps(order, m: int, rng: T.SplitMix64) -> tuple:
    """m Tausche benachbarter Plätze an zufälligen Stellen (derselbe Platz kann mehrfach vorkommen)."""
    o = list(order)
    n = len(o)
    if n < 2:
        return tuple(o)
    for u in rng.uniform(m):
        i = int(u * (n - 1))        # 0 .. n-2
        o[i], o[i + 1] = o[i + 1], o[i]
    return tuple(o)


def table_order(score, rng: T.SplitMix64) -> tuple:
    """Tabelle: nach Wertung absteigend, Gleichstand entscheidet das Los (hier genügt das Los: es geht um die Abstandsmaße)."""
    score = np.asarray(score, dtype=float)
    lots = rng.uniform(len(score))
    return tuple(int(i) for i in sorted(range(len(score)), key=lambda i: (-score[i], lots[i])))


def truth_order(n: int) -> tuple:
    """Wahre Ordnung des Generators: Index n-1 ist der Stärkste."""
    return tuple(range(n - 1, -1, -1))


def tables_from_turnier(n: int, delta: float, k: int, plan: str, p: float, seed: int):
    """Ein Turnier der Wurzel (Generator Version 1): Tabelle nach Siegen und Tabelle nach Siegquote, dazu die wahre Ordnung.
    Rückgabe (wahr, nach_siegen, nach_quote, namen)."""
    t = T.build_turnier(n, delta, k, plan, 1, p, 0.0, "ausgewogen", seed)
    wins = t.wins.sum(axis=1).astype(float)
    games = t.games.sum(axis=1).astype(float)
    rate = np.divide(wins, games, out=np.zeros_like(wins), where=games > 0)
    rng = T.SplitMix64(seed ^ 0x5EED5EED)
    return truth_order(n), table_order(wins, rng), table_order(rate, rng), t.names
