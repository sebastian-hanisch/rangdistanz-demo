"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """Referenz A = (0, 1, 2, 3), Vergleich B = (1, 0, 3, 2): die Paare {0,1} und {2,3} sind getauscht.
    Handrechnung: K = 2, τ = 1 - 2*2/6 = 1/3, F = 1+1+1+1 = 4 (Höchstwert 8, also 0,5), ρ = 1 - 6*4/(4*15) = 0,6,
    Top-2-Überlappung = 1, Top-1-Überlappung = 0, RBO (p = 0,5): A_1 = 0, A_2 = 1, A_3 = 2/3, A_4 = 1;
    Summe der gewichteten A_d = 0 + 0,5 + 0,25*2/3 + 0,125 = 19/24, Summe der Gewichte = 15/8, also RBO = 19/45."""
    return (0, 1, 2, 3), (1, 0, 3, 2)
