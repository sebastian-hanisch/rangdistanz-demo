"""Szenario: Reglerwerte (Settings) und das daraus erzeugte Paar von Rangfolgen (Referenz A, Vergleich B)."""

from dataclasses import dataclass

import rgd_constants as C
import rgd_perturb as P
import turnier_generator as T


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    art: str = "tausch"
    i: int = C.DEFAULT_I
    d: int = C.DEFAULT_D
    m: int = C.DEFAULT_M
    k: int = C.DEFAULT_K
    rbo_p: float = C.DEFAULT_RBO_P
    topk: int = C.DEFAULT_TOPK
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Pair:
    a: tuple          # Referenz-Rangfolge (Teilnehmerindizes, bester zuerst)
    b: tuple          # Vergleichs-Rangfolge
    names: tuple      # Anzeigename je Teilnehmerindex
    moved: tuple      # Teilnehmer, deren Platz sich zwischen A und B unterscheidet
    label_a: str
    label_b: str


def clamp_settings(s: Settings) -> Settings:
    """Bringt die platzabhängigen Werte in den für n gültigen Bereich (die Regler tun dasselbe)."""
    n = s.n
    i_hi = n - 1 if s.art == "tausch" else n
    return Settings(n, s.art, max(1, min(s.i, i_hi)), max(C.D_MIN, min(s.d, n - 1)), s.m, s.k, s.rbo_p, max(1, min(s.topk, max(1, n // 2))), s.seed)


def make_pair(settings: Settings) -> Pair:
    """Deterministisch aus den Reglerwerten: gleiche Eingabe, gleiche Rangfolgen."""
    s = clamp_settings(settings)
    n = s.n
    if s.art == "turnier":
        truth, by_wins, _rate, names = P.tables_from_turnier(n, C.EXP_DELTA, s.k, "vollstaendig", 1.0, s.seed)
        a, b, label_a, label_b = truth, by_wins, "Wahre Ordnung (Generator-Stärke)", "Tabelle nach Siegen"
    else:
        names = tuple(T.LABELS[:n])
        a = tuple(range(n))
        label_a = "Referenz"
        if s.art == "tausch":
            b, label_b = P.swap_adjacent(a, s.i), f"Plätze {s.i} und {s.i + 1} getauscht"
        elif s.art == "verschiebung":
            b, label_b = P.move_by(a, s.i, s.d), f"Platz {s.i} rutscht um {s.d} Plätze ab"
        elif s.art == "untere_haelfte":
            b, label_b = P.reverse_lower_half(a), "Untere Hälfte umgekehrt"
        elif s.art == "zufall":
            b, label_b = P.random_adjacent_swaps(a, s.m, T.SplitMix64(s.seed)), f"{s.m} zufällige Nachbartausche"
        else:
            raise ValueError(f"unbekannte Art: {s.art}")
    pos_a = {x: j for j, x in enumerate(a)}
    moved = tuple(x for j, x in enumerate(b) if pos_a[x] != j)
    return Pair(a, b, names, moved, label_a, label_b)
