from __future__ import annotations
import streamlit as st

def cache_data(**kwargs):
    return st.cache_data(**kwargs)

def cache_resource(**kwargs):
    return st.cache_resource(**kwargs)
