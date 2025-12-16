from __future__ import annotations
import folium
import pandas as pd
from folium.plugins import MarkerCluster

def mapa_pontos_servicos(df_points: pd.DataFrame, center=(-15.793889, -47.882778), zoom=10) -> folium.Map:
    m = folium.Map(location=center, zoom_start=zoom, control_scale=True)
    cluster = MarkerCluster().add_to(m)
    for _, r in df_points.iterrows():
        popup = f"<b>{r['nome']}</b><br>{r['tipo']}<br>RS: {r.get('regiao_saude','-')}"
        folium.Marker(
            location=[float(r["lat"]), float(r["lon"])],
            popup=folium.Popup(popup, max_width=260),
            tooltip=f"{r['tipo']} - {r['nome']}",
        ).add_to(cluster)
    return m
