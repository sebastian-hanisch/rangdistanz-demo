"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 4, 16, 12
I_MIN, DEFAULT_I = 1, 1                 # Platz (ab 1); die obere Grenze ist n - 1 bzw. n und wird in der App berechnet
D_MIN, D_MAX, DEFAULT_D = 1, 15, 3      # um wie viele Plätze eine Person rutscht
M_MIN, M_MAX, DEFAULT_M = 1, 20, 3      # Zahl zufälliger Nachbartausche
K_MIN, K_MAX, DEFAULT_K = 1, 10, 4      # Partien je Paar (nur Art "Tabelle aus einem Turnier")
TOPK_MIN, DEFAULT_TOPK = 1, 3           # obere Grenze n // 2, in der App berechnet
RBO_P_MIN, RBO_P_MAX, RBO_P_STEP, DEFAULT_RBO_P = 0.5, 0.99, 0.01, 0.9
SEED_MAX, DEFAULT_SEED = 999999, 35

ART_LABELS = {
    "tausch": "Zwei Nachbarn tauschen",
    "verschiebung": "Person rutscht ab",
    "untere_haelfte": "Untere Hälfte umkehren",
    "zufall": "Zufällige Nachbartausche",
    "turnier": "Tabelle aus einem Turnier",
}

# Feste Instanzen für alle Experimente: nie ein einzelner Seed als Befund.
SWEEP_SEEDS = tuple(range(100000, 100500))
EXP_N = 12                 # Experimente 1 und 2: feste Instanz mit 12 Teilnehmern
EXP_P = 0.9                # RBO-Parameter der Experimente
EXP_TOPK = 3
EXP_DELTA = 0.3
EXP_PLAN_P = 0.5           # Experiment 2: zufällige Lücken, jedes Paar mit Wahrscheinlichkeit 0,5, eine Partie
EXP3_NS = (4, 8, 12, 16)
EXP3_PERMUTATIONS = 2000
EXP4_N = 8                 # Experiment 4: n = 8 wie Experiment 1 der Wurzel
EXP4_KS = (1, 2, 4, 10, 40)

COLOR_A = "#4c78a8"
COLOR_B = "#2F6B65"
COLOR_MOVED = "#c0392b"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_KENDALL = "#4c78a8"
COLOR_FOOTRULE = "#8e6bb0"
COLOR_RBO = "#c0392b"
COLOR_TOPK = "#2F6B65"

PRESETS = {
    "Tausch oben": {"n": DEFAULT_N, "art": "tausch", "i": 1, "d": DEFAULT_D, "m": DEFAULT_M, "k": DEFAULT_K,
                                              "rbo_p": DEFAULT_RBO_P, "topk": DEFAULT_TOPK, "seed": DEFAULT_SEED},
    "Tausch unten": {"n": DEFAULT_N, "art": "tausch", "i": 11, "d": DEFAULT_D, "m": DEFAULT_M, "k": DEFAULT_K,
                       "rbo_p": DEFAULT_RBO_P, "topk": DEFAULT_TOPK, "seed": DEFAULT_SEED},
    "Person rutscht ab": {"n": DEFAULT_N, "art": "verschiebung", "i": 1, "d": 5, "m": DEFAULT_M, "k": DEFAULT_K,
                               "rbo_p": DEFAULT_RBO_P, "topk": DEFAULT_TOPK, "seed": DEFAULT_SEED},
    "Untere Hälfte": {"n": DEFAULT_N, "art": "untere_haelfte", "i": 1, "d": DEFAULT_D, "m": DEFAULT_M, "k": DEFAULT_K,
                                "rbo_p": DEFAULT_RBO_P, "topk": DEFAULT_TOPK, "seed": DEFAULT_SEED},
    "Aus einem Turnier": {"n": DEFAULT_N, "art": "turnier", "i": 1, "d": DEFAULT_D, "m": DEFAULT_M, "k": 4,
                                  "rbo_p": DEFAULT_RBO_P, "topk": DEFAULT_TOPK, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Tausch oben": "Plätze 1 und 2 tauschen: Kendall-Distanz 1 und Footrule 2, aber ein deutlicher Abstand für die rangbiasierte Überlappung.",
    "Tausch unten": "Plätze 11 und 12 tauschen: dieselbe Kendall-Distanz und Footrule, aber kaum ein Unterschied für die rangbiasierte Überlappung.",
    "Person rutscht ab": "Der Beste fällt um fünf Plätze: Kendall-Distanz 5, Footrule 10, die Überlappung der Spitze sinkt auf zwei Drittel.",
    "Untere Hälfte": "Die Plätze 7 bis 12 stehen verkehrt herum: viele Paare falsch, die Spitze aber unberührt.",
    "Aus einem Turnier": "Wahre Ordnung gegen die Tabelle nach Siegen eines simulierten Turniers (4 Partien je Paar, Generator der Wurzel).",
}
