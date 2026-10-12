"""PDF-Export der aktuellen Konfiguration und Maßtabelle (fpdf2, Kernschrift: nur Zeichen aus Latin-1, daher „Tau“ statt τ)."""

from fpdf import FPDF

import rgd_constants as C
import rgd_evaluation as ev
import rgd_measures as M


def _latin(text: str) -> str:
    for old, new in (("–", "-"), ("—", "-"), ("τ", "Tau"), ("ρ", "rho"), ("≥", ">="), ("≤", "<="), ("→", "->"), ("**", ""), ("€", "EUR"),
                     ("²", "^2"), ("−", "-")):
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: ev.Analysis) -> bytes:
    s, pair = a.settings, a.pair
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(0, 8, _latin("Zwei Rangfolgen vergleichen: Kendall, Footrule und die Spitze"))
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(2)
    pdf.multi_cell(0, 5.5, _latin(
        f"Teilnehmer: {s.n}, Abweichung: {C.ART_LABELS[s.art]} ({pair.label_b}), RBO-Parameter p: {ev.de(s.rbo_p)}, Top-k: {s.topk}, Seed: {s.seed}."))
    pdf.ln(2)
    level, text = ev.verdict_analysis(a)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Kernaussage", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5.5, _latin(text))
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Mass im Vergleich", new_x="LMARGIN", new_y="NEXT")
    n = len(pair.a)
    for key, (name, scale, direction, meaning) in M.MEASURE_INFO.items():
        value = a.values[key]
        shown = str(value) if isinstance(value, int) else ev.de(value, 3)
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(0, 5, _latin(f"{name}: {shown}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 4.5, _latin(f"Skala {scale}, {direction}. {meaning}."), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4.5, _latin(
        f"Rangfolgen von {n} Teilnehmern, simuliert bzw. durch eine feste Abweichung erzeugt. Die Skalen der Mass sind verschieden; Werte "
        "verschiedener Mass sind nicht vergleichbar. Quelle: Demo von Sebastian Hanisch, sebastianhanisch.net."))
    return bytes(pdf.output())
