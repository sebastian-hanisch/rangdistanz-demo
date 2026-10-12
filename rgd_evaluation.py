"""Kennzahlen, Verdikt-Logik und Experimente (über die festen Instanzen SWEEP_SEEDS)."""

import math
from dataclasses import dataclass

import numpy as np

import rgd_constants as C
import rgd_measures as M
import rgd_perturb as P
import turnier_generator as T
from rgd_scenario import Pair, Settings, clamp_settings, make_pair

MEASURE_ORDER = ("Kendall", "Footrule", "RBO", "Top-k")


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    pair: Pair
    values: dict          # rohe Maße (Schlüssel wie rgd_measures.MEASURE_INFO)
    distances: dict       # normierte Abstände auf [0, 1] (0 = gleich)


def analyse(settings: Settings) -> Analysis:
    s = clamp_settings(settings)
    pair = make_pair(s)
    return Analysis(s, pair, M.measure_values(pair.a, pair.b, s.rbo_p, s.topk), M.normalised_distance(pair.a, pair.b, s.rbo_p, s.topk))


def de(x: float, digits: int = 2) -> str:
    """Zahl mit Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float) -> str:
    return f"{100 * x:.0f}"


def pct1(x: float) -> str:
    return f"{100 * x:.1f}".replace(".", ",")


def _mean(values) -> float:
    v = [x for x in values if not (isinstance(x, float) and math.isnan(x))]
    return float(sum(v) / len(v)) if v else float("nan")


# --- Experiment 1: ein Tausch benachbarter Plätze ---------------------------------------------------------------------------------------

def sweep_adjacent(n=C.EXP_N, p=C.EXP_P, k=C.EXP_TOPK) -> list[dict]:
    """Jeder der n-1 Tausche zweier Nachbarn gegen die Referenz. Deterministisch, keine Zufallszahlen."""
    ref = tuple(range(n))
    rows = []
    for i in range(1, n):
        b = P.swap_adjacent(ref, i)
        v = M.measure_values(ref, b, p, k)
        rows.append({"i": i, "K": v["kendall_distance"], "F": v["footrule"], "rbo": v["rbo"], "topk": v["topk"],
                     "rbo_dist": 1.0 - v["rbo"], "topk_dist": 1.0 - v["topk"],
                     "k_norm": v["kendall_distance"] / M.max_kendall(n), "f_norm": v["footrule"] / M.max_footrule(n)})
    return rows


# --- Experiment 2: zwei Maße, zwei Urteile -----------------------------------------------------------------------------------------------

def sweep_disagreement(n=C.EXP_N, p=C.EXP_P, k=C.EXP_TOPK, plan_p=C.EXP_PLAN_P, delta=C.EXP_DELTA, seeds=C.SWEEP_SEEDS) -> dict:
    """Zwei Tabellen aus demselben Turnier mit Lücken (A: nach Siegen, B: nach Siegquote), Wahrheit: die Stärke. Je Maß: welche liegt näher?"""
    closer = {m: [] for m in MEASURE_ORDER}
    for seed in seeds:
        truth, by_wins, by_rate, _ = P.tables_from_turnier(n, delta, 1, "luecken", plan_p, seed)
        da, db = M.normalised_distance(by_wins, truth, p, k), M.normalised_distance(by_rate, truth, p, k)
        for m in MEASURE_ORDER:
            closer[m].append(M.closer_to_truth(da[m], db[m]))
    matrix = {x: {y: (None if x == y else M.disagreement_share(closer[x], closer[y])) for y in MEASURE_ORDER} for x in MEASURE_ORDER}
    return {"measures": MEASURE_ORDER, "matrix": matrix,
            "a_closer": {m: float(np.mean(np.array(closer[m]) == 1)) for m in MEASURE_ORDER},
            "b_closer": {m: float(np.mean(np.array(closer[m]) == -1)) for m in MEASURE_ORDER},
            "equal": {m: float(np.mean(np.array(closer[m]) == 0)) for m in MEASURE_ORDER}, "runs": len(seeds)}


# --- Experiment 3: Kendall und Footrule -----------------------------------------------------------------------------------------------

def sweep_footrule_kendall(ns=C.EXP3_NS, count=C.EXP3_PERMUTATIONS, seed=7) -> list[dict]:
    """F/K über zufällige Permutationen; die Schranke K <= F <= 2K (Diaconis, Graham 1977) wird mitgeprüft."""
    rng = T.SplitMix64(seed)
    rows = []
    for n in ns:
        base = tuple(range(n))
        ratios, holds = [], True
        for _ in range(count):
            perm = tuple(int(i) for i in np.argsort(rng.uniform(n), kind="stable"))
            K, F = M.kendall_distance(base, perm), M.footrule(base, perm)
            holds &= (K <= F <= 2 * K)
            if K > 0:
                ratios.append(F / K)
        rev = tuple(range(n - 1, -1, -1))
        rows.append({"n": n, "min": min(ratios), "mean": float(np.mean(ratios)), "max": max(ratios), "holds": holds, "count": count,
                     "reversal_K": M.kendall_distance(base, rev), "reversal_F": M.footrule(base, rev)})
    return rows


# --- Experiment 4: was die Maße zusammen sagen -------------------------------------------------------------------------------------------

def sweep_games(ks=C.EXP4_KS, n=C.EXP4_N, p=C.EXP_P, topk=C.EXP_TOPK, delta=C.EXP_DELTA, seeds=C.SWEEP_SEEDS) -> list[dict]:
    rows = []
    for k in ks:
        tau, fn, rb, tk, first = [], [], [], [], []
        for seed in seeds:
            truth, by_wins, _rate, _ = P.tables_from_turnier(n, delta, k, "vollstaendig", 1.0, seed)
            tau.append(M.kendall_tau(by_wins, truth))
            fn.append(M.footrule(by_wins, truth) / M.max_footrule(n))
            rb.append(M.rbo(by_wins, truth, p))
            tk.append(M.topk_overlap(by_wins, truth, topk))
            first.append(float(by_wins[0] == truth[0]))
        rows.append({"k": k, "tau": _mean(tau), "f_norm": _mean(fn), "rbo": _mean(rb), "topk": _mean(tk), "first": _mean(first)})
    return rows


# --- Verdikte (live aus den Messwerten) ----------------------------------------------------------------------------------------------

def verdict_analysis(a: Analysis) -> tuple[str, str]:
    """Kernfrage der Primäransicht: Was sagt jedes Maß zu diesem Paar?"""
    K, F, n = a.values["kendall_distance"], a.values["footrule"], len(a.pair.a)
    d = a.distances
    if K == 0:
        return "info", "Die beiden Rangfolgen sind gleich: Alle Maße zeigen Abstand 0."
    text = (f"Kendall-Distanz **{K}** von höchstens {M.max_kendall(n)} Paaren ({pct(d['Kendall'])} %), Footrule **{F}** von höchstens "
            f"{M.max_footrule(n)} ({pct(d['Footrule'])} %); die rangbiasierte Überlappung liegt bei {de(a.values['rbo'])} "
            f"(Abstand {pct(d['RBO'])} %), die Top-{a.settings.topk}-Überlappung bei {de(a.values['topk'])}.")
    spread = max(d.values()) - min(d.values())
    if spread >= 0.1:
        return "warning", text + " Die Maße sehen diese Abweichung **verschieden stark**: Welches zählt, hängt von der Frage ab."
    return "info", text + " Hier sehen die Maße die Abweichung ähnlich stark."


def verdict_adjacent(rows) -> tuple[str, str]:
    n = len(rows) + 1
    ks, fs = {r["K"] for r in rows}, {r["F"] for r in rows}
    hi, lo = max(rows, key=lambda r: r["rbo_dist"]), min(rows, key=lambda r: r["rbo_dist"])
    ratio = hi["rbo_dist"] / lo["rbo_dist"]
    crossing = [r["i"] for r in rows if r["topk"] < 1.0]
    return "warning", (f"Alle {n - 1} Nachbartausche haben dieselbe Kendall-Distanz ({', '.join(map(str, sorted(ks)))}) und dieselbe Footrule "
                       f"({', '.join(map(str, sorted(fs)))}). Der Abstand 1 − RBO reicht von {de(lo['rbo_dist'], 3)} (Plätze {lo['i']} und {lo['i'] + 1}) "
                       f"bis {de(hi['rbo_dist'], 3)} (Plätze {hi['i']} und {hi['i'] + 1}): das {ratio:.0f}-Fache. Die Top-k-Überlappung bemerkt nur "
                       f"{'den Tausch über die Grenze ' + str(crossing[0]) + ' | ' + str(crossing[0] + 1) if len(crossing) == 1 else 'die Tausche über ihre Grenze'}.")


def verdict_disagreement(res) -> tuple[str, str]:
    m = res["matrix"]
    return "warning", (f"Bei zwei Tabellen aus demselben Turnier urteilen Kendall und Footrule in nur {pct1(m['Kendall']['Footrule'])} % der Fälle "
                       f"verschieden, welche näher an der Wahrheit liegt. Kendall und RBO urteilen in {pct1(m['Kendall']['RBO'])} % verschieden, "
                       f"Kendall und Top-k in {pct1(m['Kendall']['Top-k'])} % (je Paar von Maßen nur Fälle ohne Gleichstand, {res['runs']} Turniere).")


def verdict_footrule_kendall(rows) -> tuple[str, str]:
    all_hold = all(r["holds"] for r in rows)
    lo, hi = min(r["min"] for r in rows), max(r["max"] for r in rows)
    total = sum(r["count"] for r in rows)
    status = "gilt in allen" if all_hold else "gilt NICHT in allen"
    return ("info" if all_hold else "warning"), (f"K ≤ F ≤ 2K {status} {total} zufälligen Permutationen; F/K liegt zwischen {de(lo)} und {de(hi)}. "
                                                f"Die Footrule ist ein grobes, billiges Gegenstück zur Kendall-Distanz, aber nicht dasselbe Maß.")


def verdict_games(rows) -> tuple[str, str]:
    r = next((x for x in rows if x["k"] == 10), rows[-1])
    return "warning", (f"Mit {r['k']} Partien je Paar ist τ gegen die wahre Ordnung {de(r['tau'])} und die Top-3-Überlappung {de(r['topk'])}, "
                       f"aber der Stärkste steht nur in {pct1(r['first'])} % der Läufe auf Platz 1. Die Skalen der Maße sind verschieden: "
                       "Vergleichbar ist nur, welches von zwei Kandidaten ein Maß näher sieht, nicht der Zahlenwert über Maße hinweg.")
