"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; jedes Preset zeigt, was seine Beschreibung verspricht."""

import dataclasses

import rgd_constants as C
import rgd_evaluation as ev
import rgd_presets as P
from rgd_scenario import Settings


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_widget_bounds():
    for name, p in C.PRESETS.items():
        assert C.N_MIN <= p["n"] <= C.N_MAX, name
        assert p["art"] in C.ART_LABELS, name
        i_hi = p["n"] - 1 if p["art"] == "tausch" else p["n"]
        assert 1 <= p["i"] <= i_hi, name
        assert C.D_MIN <= p["d"] <= min(C.D_MAX, p["n"] - 1), name
        assert C.M_MIN <= p["m"] <= C.M_MAX and C.K_MIN <= p["k"] <= C.K_MAX, name
        assert C.RBO_P_MIN <= p["rbo_p"] <= C.RBO_P_MAX, name
        assert 1 <= p["topk"] <= p["n"] // 2, name
        assert 0 <= p["seed"] <= C.SEED_MAX, name


def test_default_preset_equals_the_default_settings():
    assert Settings(**C.PRESETS["Tausch oben"]) == Settings()


def test_setting_specs_cover_every_preset_key_and_settings_fields_and_url_params_are_unique():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    assert set(P.PRESET_KEYS) == {f.name for f in dataclasses.fields(Settings)}
    params = [spec.url_param for spec in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


def test_kept_keys_are_exactly_the_hideable_sliders():
    assert set(P.KEPT_KEYS) == {"i_slider", "d_slider", "m_slider", "k_slider"}


def test_each_preset_tells_its_story():
    def a(name):
        return ev.analyse(Settings(**C.PRESETS[name]))

    top, end = a("Tausch oben"), a("Tausch unten")
    assert top.values["kendall_distance"] == end.values["kendall_distance"] == 1
    assert top.values["footrule"] == end.values["footrule"] == 2
    assert top.distances["RBO"] > 10 * end.distances["RBO"]
    fall = a("Person rutscht ab")
    assert fall.values["kendall_distance"] == 5 and fall.values["footrule"] == 10
    half = a("Untere Hälfte")
    assert half.values["topk"] == 1.0 and half.values["kendall_distance"] == 15      # 6 Plätze umgekehrt: C(6,2) Paare
    table = a("Aus einem Turnier")
    assert 0 < table.values["kendall_distance"] < 66
