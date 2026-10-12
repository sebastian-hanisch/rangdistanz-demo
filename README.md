# Zwei Rangfolgen vergleichen: Kendall, Footrule und die Spitze – Streamlit-Demo

Zweites Stück der **Ranking-Linie** (Konzepte-Demo), Nachfolger von `siegtabelle-demo`: Die Wurzel hat τ und „Platz des Stärksten“ benutzt, ohne zu
sagen, was sie messen. Dieses Stück ordnet das Vokabular für den **Abstand zweier Rangfolgen**, das alle weiteren Stücke verwenden. Es ist ein
Rangvergleichs-Labor mit live berechneten Maßen und vier Experimenten an Tabellen aus dem Turnier der Wurzel. Alles ist simuliert.

## Kernfrage

Wie weit liegen zwei Rangfolgen auseinander? Die Antwort hängt davon ab, was man zählen will: **Kendall** zählt Paare, die **Footrule** Plätze, die
**rangbiasierte Überlappung (RBO)** gewichtet die Spitze, die **Top-k-Überlappung** sieht nur die ersten k. **Kein Maß ist das richtige:** jedes
beantwortet eine andere Frage, und zwei Tabellen können für das eine Maß gleich weit von der Wahrheit liegen und für ein anderes sehr verschieden.

## Modell

- Eine Rangfolge ordnet n Teilnehmer, bester zuerst; beide Rangfolgen enthalten dieselben Teilnehmer.
- **Labor:** eine Referenz A und eine abweichende Rangfolge B, erzeugt durch zwei getauschte Nachbarn, eine abrutschende Person, die umgekehrte
  untere Hälfte, zufällige Nachbartausche oder die Tabelle nach Siegen eines simulierten Turniers (Generator der Wurzel, Version 1, wortgleich).
- **Maße:** Kendall-Distanz K und -τ, Spearman-Footrule F, Spearman-ρ, RBO (Fassung der Demo: abgeschnitten bei Tiefe n, auf [0, 1] normiert),
  Top-k-Überlappung. Alle Formeln stehen im 📐-Expander der App.
- **Skalen:** Die Prozentwerte der Demo haben alle dieselbe Spannweite (0 bis 100 %), aber verschiedene Skalen; ein Vergleich der Zahlenwerte über
  Maße hinweg ist nicht sinnvoll, nur die Reihenfolge von Kandidaten.

## Methodik

- **Experimente** über 500 feste Turniere (`SWEEP_SEEDS`, nie ein einzelner Seed), je mit einem live berechneten Verdikt; Experimente 1 und 2 mit
  12, Experiment 4 mit 8 Teilnehmern (feste Instanzen, unabhängig vom Regler).
- **Zufall:** gemeinsamer Generator `turnier_generator.py` mit SplitMix64-Strom (wortgleich mit `siegtabelle-demo`).
- **Tabelle im Experiment 2:** nach Siegen oder nach Siegquote, Gleichstand durch das Los.

## Befunde (gemessen, keine Behauptungen)

| Frage | Befund | Test |
|---|---|---|
| Ein Tausch zweier Nachbarn bei 12 Teilnehmern: was sagen die Maße? | **Alle 11 Tausche haben Kendall-Distanz 1 und Footrule 2.** Der RBO-Abstand (p = 0,9) reicht von 0,139 (Plätze 1 und 2) bis 0,004 (Plätze 11 und 12): das 32-Fache. Die Top-3-Überlappung bemerkt nur den Tausch über die Grenze 3 \| 4 (0,67). | `test_every_adjacent_swap_has_kendall_one_and_footrule_two`, `test_rbo_distance_of_the_top_and_bottom_swap_and_their_ratio`, `test_top3_overlap_notices_only_the_swap_across_the_boundary` |
| Zwei Tabellen aus demselben Turnier (Siege gegen Siegquote, Lücken): welche liegt näher an der Wahrheit? | Kendall und Footrule urteilen in 6,1 % der Fälle verschieden, Kendall und Top-3 in 14,3 %, Kendall und RBO in 19,9 % (je Paar nur Fälle ohne Gleichstand). Nach Kendall liegt die Siegquote in 70,4 % der Turniere näher, die Siegezahl in 22,4 %. | `test_disagreement_between_kendall_and_footrule_is_small_and_with_the_top_measures_larger`, `test_the_rate_table_is_closer_to_the_truth_in_most_runs` |
| Wie weit liegen Kendall und Footrule auseinander? | **K ≤ F ≤ 2K gilt in allen 8000 zufälligen Permutationen** (n = 4, 8, 12, 16). F/K liegt zwischen 1,09 und 2,00, im Mittel zwischen 1,42 (n = 16) und 1,77 (n = 4). Die vollständige Umkehr bei n = 12 hat K = 66 und F = 72. | `test_diaconis_graham_holds_in_all_8000_permutations`, `test_footrule_over_kendall_ranges_and_means`, `test_full_reversal_values_for_n_12` |
| τ gegen „Platz 1 stimmt“ (vollständiges Turnier, n = 8) | Mit einer Partie je Paar ist τ = 0,54 und Platz 1 stimmt in 42,6 % der Läufe; mit 10 Partien τ = 0,88, Top-3-Überlappung 0,925, aber Platz 1 nur in 76,4 %; mit 40 Partien τ = 0,98 und 93,2 %. | `test_measures_and_first_place_against_the_number_of_games`, `test_the_first_place_lags_the_global_measures_at_ten_games` |

## Befunde und Korrekturen gegenüber dem Plan

- **Kendall und Footrule urteilen häufiger verschieden als in der Vorab-Messreihe.** Die Phase 0 (2000 Turniere) fand 4,6 %, die Demo mit 500 festen
  Turnieren 6,1 %. Der Unterschied liegt im Stichprobenrauschen; die Reihenfolge Footrule < Top-k < RBO blieb.
- **E3 mit 8000 statt 20 000 Permutationen.** Die Demo rechnet 2000 je Größe; die Aussage K ≤ F ≤ 2K bleibt in allen gültig.
- **Tabellen im Experiment 2 mit Gleichstand durch das Los**, ohne den Direktvergleich der Wurzel: Hier geht es nur um die Abstandsmaße.
- **Gewichtetes Kendall-τ** (Vigna 2015) wurde, wie geplant, nicht umgesetzt; RBO trägt die Aussage „die Spitze zählt mehr“.

## Abgrenzung

- [Siegtabelle](https://sebastianhanisch-siegtabelle-demo.streamlit.app/) (Wurzel) benutzt τ und „Platz des Stärksten“ und verweist für alles
  Weitere auf dieses Stück; hier steht, was diese Maße zählen und wo sie sich unterscheiden.
- [Zentralität](https://sebastianhanisch-centrality-demo.streamlit.app/) (Graphen und Netzwerke) und
  [Zufällige Spannbäume](https://sebastianhanisch-random-spanning-tree-demo.streamlit.app/) benutzen Spearman-Rangkorrelationen als Werkzeug, um
  Verfahren zu vergleichen; Rangabstände sind dort nicht das Thema.

## Ehrliche Grenzen

- **Nur vollständige Rangfolgen über dieselben Teilnehmer.** Teillisten mit verschiedenen Elementen und Gleichstände brauchen eigene Varianten der
  Maße.
- **RBO-Parameter und Top-k sind Setzungen.** Die Experimente rechnen mit p = 0,9 und k = 3; das Urteil „welche Tabelle liegt näher“ kann bei
  anderen Werten anders ausfallen.
- **RBO ist die Fassung der Demo** (abgeschnitten bei Tiefe n, normiert), nicht die extrapolierte Fassung der Literatur für unbegrenzte Listen.
- **Alles simuliert:** Die Tabellen kommen aus dem Generator der Wurzel, die „wahre Ordnung“ ist eine Konstruktion.
- **Kein Maß wird empfohlen.** Das Stück liefert die Fragen, die man vorher beantworten muss: Zählt jedes Paar gleich? Zählt die Spitze mehr?

## Quellen

- Kendall, M. G. (1938): A new measure of rank correlation. *Biometrika* 30 (1/2), 81–93.
- Spearman, C. (1904): The proof and measurement of association between two things. *The American Journal of Psychology* 15, 72–101.
- Diaconis, P., Graham, R. L. (1977): Spearman's footrule as a measure of disarray. *Journal of the Royal Statistical Society, Series B* 39 (2), 262–268.
- Webber, W., Moffat, A., Zobel, J. (2010): A similarity measure for indefinite rankings. *ACM Transactions on Information Systems* 28 (4), 20:1–20:38.
  Zitat und Parameter nach der gängigen Darstellung; **das Original (ACM) wurde nicht eingesehen**, die Fassung der Demo ist als eigene
  Definition gekennzeichnet.
- Steele, G. L., Lea, D., Flood, C. H. (2014): Fast splittable pseudorandom number generators. *OOPSLA 2014*, 453–472. Konstanten nach Vigna,
  `splitmix64.c` (prng.di.unimi.it).

## Tests

91 Tests, rund 20 Sekunden: Einheiten gegen die von Hand gerechnete Mini-Instanz (`test_measures.py`, `test_perturb.py`), Generator
(`test_generator.py`, wortgleich mit der Wurzel), **Orakel** (`test_oracle_rangdistanz.py`: Kendall gegen `scipy` und Aufzählung, Footrule gegen den
Inversen-Weg und die Umkehr als Höchstwert, ρ gegen `scipy`, Diaconis-Graham erschöpfend für n = 4, RBO gegen exakte Bruchrechnung, Dreiecks-
ungleichung, Paritätsinvariante), Presets, ausblendbare Regler (`test_hidden_widget_state.py`), Analyse und Verdikte (`test_evaluation.py`), alle Zahlen
dieses README (`test_claims.py`) und AppTest-Rauchtests.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `turnier_generator.py` | gemeinsamer Generator (wortgleich in allen Repos der Linie) |
| `rgd_measures.py` | alle Maße als reine Funktionen |
| `rgd_perturb.py` | Abweichungen von der Referenz, Tabellen aus dem Turnier |
| `rgd_scenario.py` | Reglerwerte (`Settings`) und das Paar von Rangfolgen daraus |
| `rgd_evaluation.py` | Analyse, Experimente über die festen Instanzen, Verdikte |
| `rgd_presets.py`, `rgd_constants.py` | Permalink, Presets, ausblendbare Regler, Grenzen |
| `rgd_visualization.py`, `rgd_pdf_export.py` | Plotly-Abbildungen, PDF-Export |
| `tests/` | Einheiten-, Orakel-, Claims- und App-Tests |

## Bewusst nicht umgesetzt

- **Gewichtetes Kendall-τ** (`scipy.stats.weightedtau`): aufwendig zu prüfen; RBO trägt die Aussage „die Spitze zählt mehr“.
- **Teillisten und Gleichstände** in den Maßen.
- **Aggregation mehrerer Rangfolgen** (Borda, Copeland, Kemeny) und **Modelle für die Stärke** (Bradley-Terry, Elo): jeweils eigene Stücke der Linie.
- **Unsicherheit einer Rangfolge** (Rangintervalle): eigenes Stück der Linie.

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt` und `python -m pytest tests -q`.

Gebaut mit Streamlit, Plotly, numpy, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
