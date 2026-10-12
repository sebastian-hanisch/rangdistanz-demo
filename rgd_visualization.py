"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import rgd_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_bump(pair):
    """Zwei Rangfolgen nebeneinander, je Teilnehmer eine Linie von seinem Platz in A zu seinem Platz in B; wer den Platz wechselt, ist rot."""
    n = len(pair.a)
    pos_a = {x: j + 1 for j, x in enumerate(pair.a)}
    pos_b = {x: j + 1 for j, x in enumerate(pair.b)}
    moved = set(pair.moved)
    fig = go.Figure()
    for x in pair.a:
        color = C.COLOR_MOVED if x in moved else C.COLOR_OTHER
        fig.add_trace(go.Scatter(x=[0, 1], y=[pos_a[x], pos_b[x]], mode="lines+markers", line=dict(color=color, width=3 if x in moved else 2),
                                 marker=dict(size=8, color=color), showlegend=False,
                                 hovertemplate=f"{pair.names[x]}: Platz {pos_a[x]} in A, Platz {pos_b[x]} in B<extra></extra>"))
    for x in pair.a:
        fig.add_annotation(x=0, y=pos_a[x], text=pair.names[x], xanchor="right", xshift=-10, showarrow=False)
        fig.add_annotation(x=1, y=pos_b[x], text=pair.names[x], xanchor="left", xshift=10, showarrow=False)
    fig.update_xaxes(range=[-0.25, 1.25], tickvals=[0, 1], ticktext=[pair.label_a, pair.label_b], side="top", showgrid=False, zeroline=False)
    fig.update_yaxes(range=[n + 0.5, 0.5], dtick=1, title_text="Platz", showgrid=False)
    return _base(fig, height=max(340, 30 * n + 110))


def build_adjacent(rows):
    xs = [f"{r['i']} | {r['i'] + 1}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["k_norm"] for r in rows], mode="lines+markers", name="Kendall K / Höchstwert",
                             line=dict(color=C.COLOR_KENDALL, width=3), hovertemplate="Tausch %{x}: K/Kmax = %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["f_norm"] for r in rows], mode="lines+markers", name="Footrule F / Höchstwert",
                             line=dict(color=C.COLOR_FOOTRULE, width=2, dash="dash"), hovertemplate="Tausch %{x}: F/Fmax = %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["rbo_dist"] for r in rows], mode="lines+markers", name="1 − RBO",
                             line=dict(color=C.COLOR_RBO, width=3), hovertemplate="Tausch %{x}: 1 − RBO = %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["topk_dist"] for r in rows], mode="lines+markers", name="1 − Top-k-Überlappung",
                             line=dict(color=C.COLOR_TOPK, width=2, dash="dot"), hovertemplate="Tausch %{x}: 1 − Top-k = %{y:.3f}<extra></extra>"))
    fig.update_xaxes(title_text="getauschte Plätze", type="category")
    fig.update_yaxes(title_text="Abstand auf [0, 1] (0 = gleich)", range=[0, max(0.2, max(r["rbo_dist"] for r in rows) * 1.2)])
    return _base(fig)


def build_disagreement(res):
    ms = list(res["measures"])
    z = [[(res["matrix"][y][x] if res["matrix"][y][x] is not None else None) for x in ms] for y in ms]
    text = [[("" if v is None else f"{100 * v:.1f} %".replace(".", ",")) for v in row] for row in z]
    fig = go.Figure(go.Heatmap(z=z, x=ms, y=ms, text=text, texttemplate="%{text}", zmin=0, zmax=0.3, colorscale="Blues", showscale=False,
                               hovertemplate="%{y} gegen %{x}: urteilen in %{text} der Fälle verschieden<extra></extra>", xgap=2, ygap=2))
    fig.update_xaxes(type="category")
    fig.update_yaxes(type="category", autorange="reversed")
    return _base(fig, height=360)


def build_footrule_kendall(rows):
    xs = [f"n = {r['n']}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["max"] - r["min"] for r in rows], base=[r["min"] for r in rows], marker_color=C.COLOR_OTHER, name="Spanne von F/K",
                         hovertemplate="%{x}: F/K von %{base:.2f} bis %{y:.2f} über das Minimum hinaus<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["mean"] for r in rows], mode="markers", marker=dict(size=12, color=C.COLOR_FOOTRULE), name="Mittelwert",
                             hovertemplate="%{x}: Mittel %{y:.2f}<extra></extra>"))
    fig.add_hline(y=1.0, line_dash="dash", line_color=C.COLOR_KENDALL, annotation_text="F = K (untere Schranke)", annotation_position="bottom right")
    fig.add_hline(y=2.0, line_dash="dash", line_color=C.COLOR_RBO, annotation_text="F = 2K (obere Schranke)", annotation_position="top right")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Footrule / Kendall-Distanz", range=[0.8, 2.2])
    return _base(fig)


def build_games(rows):
    xs = [str(r["k"]) for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[(1 + r["tau"]) / 2 for r in rows], mode="lines+markers", name="1 − K/Kmax (aus τ)",
                             line=dict(color=C.COLOR_KENDALL, width=3), hovertemplate="%{x} Partien: %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[1 - r["f_norm"] for r in rows], mode="lines+markers", name="1 − F/Fmax",
                             line=dict(color=C.COLOR_FOOTRULE, width=2, dash="dash"), hovertemplate="%{x} Partien: %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["rbo"] for r in rows], mode="lines+markers", name="RBO",
                             line=dict(color=C.COLOR_RBO, width=3), hovertemplate="%{x} Partien: %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["topk"] for r in rows], mode="lines+markers", name="Top-3-Überlappung",
                             line=dict(color=C.COLOR_TOPK, width=2, dash="dot"), hovertemplate="%{x} Partien: %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["first"] for r in rows], mode="lines+markers", name="Platz 1 stimmt",
                             line=dict(color="#333333", width=2), marker=dict(symbol="diamond", size=9),
                             hovertemplate="%{x} Partien: Platz 1 stimmt in %{y:.0%}<extra></extra>"))
    fig.update_xaxes(title_text="Partien je Paar", type="category")
    fig.update_yaxes(title_text="Ähnlichkeit auf [0, 1] (1 = gleich) bzw. Anteil der Läufe", range=[0, 1.02])
    return _base(fig, height=400)
