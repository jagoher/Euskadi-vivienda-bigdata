
from pathlib import Path

import pandas as pd
import pytest


RUTA_CSV = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "processed"
    / "indicadores_vivienda_juvenil_euskadi.csv"
)


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(RUTA_CSV, dtype={"codigo_ine": str})


def test_total_municipios(df):
    """El catálogo debe contener los 252 municipios de Euskadi."""
    assert len(df) == 252


def test_codigos_ine_unicos(df):
    """Cada municipio debe tener un código INE único."""
    assert df["codigo_ine"].notna().all()
    assert not df["codigo_ine"].duplicated().any()


def test_columnas_obligatorias(df):
    """Comprobar que existen las columnas principales."""
    columnas = [
        "codigo_ine",
        "municipio_ine",
        "provincia",
        "eustat_alquiler_medio_2024",
        "salario_neto_mensual",
        "esfuerzo_alquiler_pct",
        "supera_30_pct",
        "tiene_alquiler",
        "tiene_compra",
    ]
    assert set(columnas).issubset(df.columns)


def test_esfuerzo_alquiler_no_negativo(df):
    """El esfuerzo de alquiler no puede ser negativo."""
    valores = df["esfuerzo_alquiler_pct"].dropna()
    assert (valores >= 0).all()


def test_calculo_esfuerzo_alquiler(df):
    """Verificar el cálculo del esfuerzo con tolerancia de redondeo."""
    datos = df.dropna(
        subset=[
            "eustat_alquiler_medio_2024",
            "salario_neto_mensual",
            "esfuerzo_alquiler_pct",
        ]
    )

    assert not datos.empty
    assert (datos["salario_neto_mensual"] > 0).all()

    calculado = (
        datos["eustat_alquiler_medio_2024"]
        / datos["salario_neto_mensual"]
        * 100
    )

    assert (
        (calculado - datos["esfuerzo_alquiler_pct"]).abs() <= 0.02
    ).all()


def test_cobertura_compraventa(df):
    """Comprobar la cobertura de las dos fuentes."""
    assert df["ine_precio_medio_2025"].notna().sum() == 20
    assert df["registradores_precio_medio_2025"].notna().sum() == 15


def test_precios_compra_positivos(df):
    """Los precios disponibles deben ser positivos."""
    columnas = [
        "ine_precio_medio_2025",
        "registradores_precio_medio_2025",
    ]

    for columna in columnas:
        valores = df[columna].dropna()
        assert not valores.empty
        assert (valores > 0).all()


def test_anos_salario_compra_positivos(df):
    """Los años de salario calculados deben ser positivos."""
    columnas = [
        "anos_salario_compra_ine",
        "anos_salario_compra_registradores",
    ]

    for columna in columnas:
        valores = df[columna].dropna()
        assert not valores.empty
        assert (valores > 0).all()


def test_coherencia_precio_y_anos(df):
    """Cada precio disponible debe tener su indicador de años."""
    parejas = [
        ("ine_precio_medio_2025", "anos_salario_compra_ine"),
        (
            "registradores_precio_medio_2025",
            "anos_salario_compra_registradores",
        ),
    ]

    for precio, anos in parejas:
        assert df[precio].notna().equals(df[anos].notna())
