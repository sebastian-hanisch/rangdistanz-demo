"""Invariante der ausblendbaren Regler (DEMO-PLAYBOOK §3, KEPT-Muster): ein nicht gezeichneter Regler bekommt nie einen Wert in seinem
Widget-Zustand; sein zuletzt gewählter Wert wird gemerkt und kommt beim nächsten Zeichnen zurück. Dazu: gespeicherte Werte oberhalb einer neuen
Reglergrenze (n wird kleiner) dürfen nicht abstürzen."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = 180


def fresh():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def slider_keys(at):
    return {s.key for s in at.slider}


def test_sliders_are_only_drawn_for_their_art():
    at = fresh()
    assert at.selectbox(key="art_select").value == "tausch"
    assert slider_keys(at) >= {"i_slider"} and not {"d_slider", "m_slider", "k_slider"} & slider_keys(at)
    at.selectbox(key="art_select").select("verschiebung").run(timeout=TIMEOUT)
    assert {"i_slider", "d_slider"} <= slider_keys(at) and not {"m_slider", "k_slider"} & slider_keys(at)
    at.selectbox(key="art_select").select("zufall").run(timeout=TIMEOUT)
    assert "m_slider" in slider_keys(at) and not {"i_slider", "d_slider", "k_slider"} & slider_keys(at)
    at.selectbox(key="art_select").select("turnier").run(timeout=TIMEOUT)
    assert "k_slider" in slider_keys(at) and not {"i_slider", "d_slider", "m_slider"} & slider_keys(at)
    at.selectbox(key="art_select").select("untere_haelfte").run(timeout=TIMEOUT)
    assert not {"i_slider", "d_slider", "m_slider", "k_slider"} & slider_keys(at)
    assert not at.exception


def test_hidden_value_survives_switching_the_art_away_and_back():
    at = fresh()
    at.slider(key="i_slider").set_value(7).run(timeout=TIMEOUT)
    at.selectbox(key="art_select").select("turnier").run(timeout=TIMEOUT)
    assert "i_slider" not in at.session_state                    # nicht gezeichnet: kein Widget-Zustand
    at.slider(key="k_slider").set_value(9).run(timeout=TIMEOUT)
    at.selectbox(key="art_select").select("tausch").run(timeout=TIMEOUT)
    assert at.slider(key="i_slider").value == 7
    assert "k_slider" not in at.session_state
    at.selectbox(key="art_select").select("turnier").run(timeout=TIMEOUT)
    assert at.slider(key="k_slider").value == 9
    assert not at.exception


def test_preset_sets_the_hidden_slider_for_the_next_drawing():
    at = fresh()
    labels = {b.label: i for i, b in enumerate(at.button)}
    at.button[labels["Person rutscht ab"]].click().run(timeout=TIMEOUT)
    assert at.selectbox(key="art_select").value == "verschiebung"
    assert at.slider(key="d_slider").value == 5 and at.slider(key="i_slider").value == 1
    labels = {b.label: i for i, b in enumerate(at.button)}
    at.button[labels["Aus einem Turnier"]].click().run(timeout=TIMEOUT)
    assert at.selectbox(key="art_select").value == "turnier"
    assert at.slider(key="k_slider").value == 4
    assert "d_slider" not in at.session_state
    assert not at.exception


def test_a_smaller_n_pulls_stored_values_back_into_range_without_error():
    at = fresh()
    at.slider(key="n_slider").set_value(16).run(timeout=TIMEOUT)
    at.slider(key="i_slider").set_value(15).run(timeout=TIMEOUT)
    at.slider(key="topk_slider").set_value(8).run(timeout=TIMEOUT)
    at.slider(key="n_slider").set_value(4).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.slider(key="i_slider").value <= 3
    assert at.slider(key="topk_slider").value <= 2
    at.selectbox(key="art_select").select("verschiebung").run(timeout=TIMEOUT)
    assert not at.exception
