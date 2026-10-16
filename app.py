"""Zwei Rangfolgen vergleichen: Kendall, Footrule und die Spitze - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zweites Stück der Ranking-Linie: ein Rangvergleichs-Labor mit live berechneten Maßen und vier Experimenten an Tabellen aus dem Turnier der Wurzel.
Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import rgd_constants as C
import rgd_evaluation as ev
import rgd_measures as M
from rgd_pdf_export import build_pdf
from rgd_presets import (
    apply_preset,
    bounds,
    clamp_state,
    current_value,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    remember,
    seed_widget,
    sync_query_params,
)
from rgd_scenario import Settings
from rgd_visualization import build_adjacent, build_bump, build_disagreement, build_footrule_kendall, build_games

st.set_page_config(page_title="Zwei Rangfolgen vergleichen – Sebastian Hanisch", layout="wide")

SHOW = {"success": st.success, "info": st.info, "warning": st.warning}


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _adjacent():
    return ev.sweep_adjacent()


@st.cache_data(show_spinner="Experiment rechnet über 500 feste Turniere …")
def _disagreement():
    return ev.sweep_disagreement()


@st.cache_data(show_spinner=False)
def _footrule_kendall():
    return ev.sweep_footrule_kendall()


@st.cache_data(show_spinner="Experiment rechnet über 500 feste Turniere …")
def _games():
    return ev.sweep_games()


def verdict(level, text):
    SHOW[level](text)


st.title("📏 Zwei Rangfolgen vergleichen: Kendall, Footrule und die Spitze")
st.markdown(
    """
Wie weit liegen zwei Rangfolgen auseinander? Diese Demo ist das **zweite Stück der Ranking-Linie** und ordnet das **Vokabular für den Abstand
zweier Rangfolgen**, das alle weiteren Stücke verwenden. Die Antwort hängt davon ab, **was man zählen will**: **Kendall** zählt Paare, die
**Footrule** Plätze, die **rangbiasierte Überlappung** gewichtet die Spitze, die **Top-k-Überlappung** sieht nur die ersten k. Kein Maß ist das
richtige; jedes beantwortet eine andere Frage.

Weiter unten: vier **🔬 Experimente** mit Verdikt, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So messen Sie den Abstand zweier Rangfolgen", expanded=True):
    st.markdown(
        """
1. **Zwei Rangfolgen über dieselben Teilnehmer:** eine Referenz A und eine abweichende B (hier erzeugt durch einen festen Eingriff oder durch die
   Tabelle eines simulierten Turniers).
2. **Paare zählen (Kendall):** Wie viele Paare ordnen A und B entgegengesetzt? Jedes Paar zählt gleich, gleich ob ganz oben oder ganz unten.
3. **Plätze zählen (Footrule):** Um wie viele Plätze liegt jeder Teilnehmer daneben, summiert? Ein weiter Sprung zählt mehr als ein Tausch.
4. **Die Spitze gewichten (RBO, Top-k):** Wie stark überlappen die obersten Plätze? Was dahinter steht, zählt wenig oder gar nicht.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Rangfolgen**")
    n = st.slider("Teilnehmer n", *bounds("n_slider"), key="n_slider", help="Wie viele Teilnehmer in beiden Rangfolgen stehen.")
    art = st.selectbox("Wie weicht B von A ab?", list(C.ART_LABELS), format_func=C.ART_LABELS.get, key="art_select")
    if art in ("tausch", "verschiebung"):
        i_hi = n - 1 if art == "tausch" else n
        clamp_state("i_slider", i_hi)
        seed_widget("i_slider", i_hi)
        i = st.slider("Platz" if art == "verschiebung" else "Obere der beiden getauschten Plätze", 1, i_hi, key="i_slider",
                      help="Welcher Platz der Referenz betroffen ist (1 = Spitze).")
        remember("i_slider", i)
    if art == "verschiebung":
        clamp_state("d_slider", n - 1)
        seed_widget("d_slider", n - 1)
        d = st.slider("Um wie viele Plätze rutscht die Person ab?", 1, n - 1, key="d_slider",
                      help="An den Rändern begrenzt: Wer ganz unten ankommt, rutscht nicht weiter.")
        remember("d_slider", d)
    if art == "zufall":
        seed_widget("m_slider")
        m = st.slider("Zahl der Nachbartausche", *bounds("m_slider"), key="m_slider", help="Wie viele Tausche benachbarter Plätze an zufälligen Stellen.")
        remember("m_slider", m)
    if art == "turnier":
        seed_widget("k_slider")
        k = st.slider("Partien je Paar im Turnier", *bounds("k_slider"), key="k_slider",
                      help="Wie oft jedes Paar im simulierten, vollständigen Turnier spielt. Mehr Partien, näher an der wahren Ordnung.")
        remember("k_slider", k)
    st.markdown("**Parameter der Maße**")
    rbo_p = st.slider("RBO-Parameter p", C.RBO_P_MIN, C.RBO_P_MAX, step=C.RBO_P_STEP, key="rbo_p_slider",
                      help="Wie schnell das Gewicht mit der Tiefe fällt. Klein: fast nur die Spitze zählt. Nah an 1: auch tiefe Plätze.")
    clamp_state("topk_slider", max(1, n // 2))
    topk = st.slider("Top-k", 1, max(2, n // 2), key="topk_slider", help="Wie viele oberste Plätze die Top-k-Überlappung betrachtet.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1,
                           help="Wirkt bei zufälligen Nachbartauschen und bei der Tabelle aus einem Turnier.")
    st.button("🎲 Neuen Zufall würfeln", width="stretch", on_click=randomize_seed)

values = {key: int(current_value(key)) for key in ("i_slider", "d_slider", "m_slider", "k_slider")}
sync_query_params({"n_slider": int(n), "art_select": art, "i_slider": values["i_slider"], "d_slider": values["d_slider"], "m_slider": values["m_slider"],
                   "k_slider": values["k_slider"], "rbo_p_slider": round(float(rbo_p), 2), "topk_slider": int(topk), "seed_input": int(seed)})

settings = Settings(int(n), art, values["i_slider"], values["d_slider"], values["m_slider"], values["k_slider"], round(float(rbo_p), 2), int(topk), int(seed))
a = _analysis(settings)
pair = a.pair

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Die beiden Rangfolgen")
st.plotly_chart(build_bump(pair), width="stretch", key="bump_chart")
st.caption("Je Teilnehmer eine Linie von seinem Platz in A zu seinem Platz in B; rot sind die, die den Platz wechseln.")

st.markdown("## 📐 Die Maße")
rows = []
for key, (name, scale, direction, meaning) in M.MEASURE_INFO.items():
    v = a.values[key]
    rows.append({"Maß": name, "Wert": v if isinstance(v, int) else round(float(v), 3), "Skala": scale, "Richtung": direction, "Was es zählt": meaning})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
dist = a.distances
c1, c2, c3, c4 = st.columns(4)
c1.metric("Kendall: Abstand", f"{ev.pct(dist['Kendall'])} %", delta=f"K = {a.values['kendall_distance']}", delta_color="off",
          help="Kendall-Distanz geteilt durch den Höchstwert n(n-1)/2.")
c2.metric("Footrule: Abstand", f"{ev.pct(dist['Footrule'])} %", delta=f"F = {a.values['footrule']}", delta_color="off",
          help="Footrule geteilt durch den Höchstwert floor(n²/2).")
c3.metric("RBO: Abstand", f"{ev.pct(dist['RBO'])} %", delta=f"p = {ev.de(settings.rbo_p)}", delta_color="off", help="1 minus rangbiasierte Überlappung.")
c4.metric(f"Top-{settings.topk}: Abstand", f"{ev.pct(dist['Top-k'])} %", delta=f"Überlappung {ev.de(a.values['topk'])}", delta_color="off",
          help="1 minus Anteil gemeinsamer Teilnehmer unter den ersten k.")
st.caption("Die Prozentwerte haben dieselbe Spannweite (0 bis 100 %), aber verschiedene Skalen: 20 % bei einem Maß heißt nicht dasselbe wie 20 % bei einem anderen.")
st.download_button("📄 PDF des aktuellen Vergleichs", data=build_pdf(a), file_name="rangvergleich.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Sehen alle Maße diese Abweichung gleich stark?")
verdict(*ev.verdict_analysis(a))

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Gleiche Distanz, andere Spitze")
st.caption("12 Teilnehmer (feste Instanz, unabhängig vom Regler), RBO-Parameter 0,9, Top-3. Jeder der 11 Tausche zweier Nachbarn gegen die Referenz.")
rows1 = _adjacent()
st.plotly_chart(build_adjacent(rows1), width="stretch", key="exp1_chart")
verdict(*ev.verdict_adjacent(rows1))

st.subheader("🔬 Experiment 2: Zwei Maße, zwei Urteile")
st.caption("12 Teilnehmer (feste Instanz), 500 simulierte Turniere mit zufälligen Lücken (jedes Paar spielt mit Wahrscheinlichkeit 0,5, einmal). "
           "Tabelle A nach Siegen, Tabelle B nach Siegquote, Wahrheit: die Generator-Stärke. Der Wert in Zeile x und Spalte y: Anteil der Turniere, "
           "in denen die Maße x und y verschieden urteilen, welche Tabelle näher liegt.")
res2 = _disagreement()
st.plotly_chart(build_disagreement(res2), width="stretch", key="exp2_chart")
verdict(*ev.verdict_disagreement(res2))
st.caption("Anteil der Turniere mit gleichem Abstand (kein Urteil): "
           + ", ".join(f"{m} {ev.pct(res2['equal'][m])} %" for m in res2["measures"]) + ".")

st.subheader("🔬 Experiment 3: Wie weit liegen Kendall und Footrule auseinander?")
st.caption("2000 zufällige Permutationen je Größe n gegen die Identität; Verhältnis Footrule / Kendall-Distanz.")
rows3 = _footrule_kendall()
st.plotly_chart(build_footrule_kendall(rows3), width="stretch", key="exp3_chart")
verdict(*ev.verdict_footrule_kendall(rows3))
st.dataframe(pd.DataFrame([{"n": r["n"], "F/K kleinster": round(r["min"], 2), "F/K Mittel": round(r["mean"], 2), "F/K größter": round(r["max"], 2),
                            "Umkehr: K": r["reversal_K"], "Umkehr: F": r["reversal_F"]} for r in rows3]), hide_index=True, width="stretch")

st.subheader("🔬 Experiment 4: Was die Maße zusammen sagen")
st.caption("8 Teilnehmer (wie Experiment 1 der Wurzel), vollständiges Turnier, Mittel über 500 feste Turniere. Alle Maße auf „1 = gleich“ umgerechnet, damit "
           "die Kurven in einem Bild stehen; die Zahlenwerte bleiben verschieden skaliert.")
rows4 = _games()
st.plotly_chart(build_games(rows4), width="stretch", key="exp4_chart")
verdict(*ev.verdict_games(rows4))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Beide Rangfolgen enthalten dieselben Teilnehmer** | Teillisten (Top-k mit verschiedenen Elementen) und Gleichstände brauchen eigene Varianten der Maße; die Demo rechnet nur mit vollständigen Rangfolgen. | – |
| **Ein Maß genügt** | Kendall, Footrule und die Überlappung der Spitze urteilen in 6 bis 20 % der Tabellenpaare verschieden (Experiment 2). Die Wahl entscheidet. | – |
| **Der Parameter ist unkritisch** | Das Urteil von RBO und Top-k hängt von p bzw. k ab; die Experimente rechnen mit p = 0,9 und k = 3, nicht über alle Werte. | – |
| **Die Rangfolgen kommen aus einem Turnier** | Alles ist simuliert (Generator der Wurzel); die „wahre Ordnung“ ist eine Konstruktion, kein Messwert. | – |
| **Eine Rangfolge ist das Ziel** | Aus mehreren Rangfolgen eine zu machen (und was dabei „nah“ heißt) ist eine eigene Aufgabe. | Borda, Copeland, Kemeny |
| **Der Abstand genügt** | Er sagt nicht, wie sicher eine Rangfolge ist. | Rangintervalle und Shrinkage |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Rangfolgen.** Eine Rangfolge $a$ ordnet $n$ Teilnehmer; $a(i)$ ist der Platz von Teilnehmer $i$ (1 = Spitze).

**Kendall-Distanz.** $K(a,b) = \#\{\{i,j\} : (a(i)-a(j))\,(b(i)-b(j)) < 0\}$, höchstens $\binom{n}{2}$; $\tau = 1 - 2K / \binom{n}{2}$.

**Footrule.** $F(a,b) = \sum_i |a(i) - b(i)|$, höchstens $\lfloor n^2/2 \rfloor$ (die vollständige Umkehr).

**Spearman-$\rho$.** $\rho = 1 - 6 \sum_i (a(i)-b(i))^2 / (n(n^2-1))$.

**Beziehung (Diaconis, Graham 1977).** $K \le F \le 2K$ für alle Paare von Permutationen; $F/K$ liegt also zwischen 1 und 2.

**Top-$k$-Überlappung.** $|A_k \cap B_k| / k$ mit den ersten $k$ Teilnehmern $A_k$, $B_k$.

**RBO (Fassung dieser Demo).** Mit $A_d = |a_{1:d} \cap b_{1:d}|/d$ ist $\mathrm{RBO} = \sum_{d=1}^{n} p^{d-1} A_d \,/\, \sum_{d=1}^{n} p^{d-1}$
(abgeschnitten bei Tiefe $n$ und auf $[0,1]$ normiert; die extrapolierte Fassung der Literatur gehört zu unbegrenzten Listen).

**Literatur.**
- Kendall, M. G. (1938): A new measure of rank correlation. *Biometrika* 30 (1/2), 81–93.
- Spearman, C. (1904): The proof and measurement of association between two things. *The American Journal of Psychology* 15, 72–101.
- Diaconis, P., Graham, R. L. (1977): Spearman's footrule as a measure of disarray. *Journal of the Royal Statistical Society, Series B* 39 (2), 262–268.
- Webber, W., Moffat, A., Zobel, J. (2010): A similarity measure for indefinite rankings. *ACM Transactions on Information Systems* 28 (4), 20:1–20:38.
  Die Gewichte $p^{d-1}$ und die Überlappung je Tiefe nach der gängigen Darstellung dieser Arbeit; das Original (ACM) wurde nicht eingesehen.
- Steele, G. L., Lea, D., Flood, C. H. (2014): Fast splittable pseudorandom number generators. *OOPSLA 2014*, 453–472 (Zufallsstrom des Generators).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ranking: von der Siegtabelle bis Learning to Rank](https://sebastianhanisch.net/konzepte-ranking.html)."
)
