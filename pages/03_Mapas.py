from __future__ import annotations
import streamlit as st
from streamlit_folium import st_folium
from ui.layout import header
from ui.sidebar import get_filters
from data.pipeline import load_points_dataset
from viz.mapas import mapa_pontos_servicos

header()
filters = get_filters()
pts = load_points_dataset(filters)

m = mapa_pontos_servicos(pts)
st_folium(m, width=None, height=600)
