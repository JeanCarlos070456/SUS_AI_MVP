import pandas as pd
from data.metrics import add_incidencia

def test_incidencia():
    df = pd.DataFrame({"casos":[10], "pop":[100000]})
    out = add_incidencia(df)
    assert round(float(out.loc[0, "incidencia_100k"]), 2) == 10.0
