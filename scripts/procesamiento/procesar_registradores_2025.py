
from pathlib import Path
import pandas as pd

# ============================================================
# PRECIOS MEDIOS DE VIVIENDA
# Fuente: Colegio de Registradores
# Página 40 - Informe 2025T4
# ============================================================

precios_vivienda = {
    "Donostia/San Sebastián": 515731,
    "Zarautz": 490698,
    "Sopela": 443764,
    "Hondarribia": 442904,
    "Getxo": 428202,
    "Berango": 400738,
    "Gorliz": 374908,
    "Plentzia": 371419,
    "Mungia": 366510,
    "Astigarraga": 342716,
    "Urduliz": 335099,
    "Leioa": 327380,
    "Oiartzun": 323258,
    "Orio": 323210,
    "Sondika": 313580,
}

# ============================================================
# PRECIOS POR METRO CUADRADO
# Página 30 - Informe 2025T4
# ============================================================

precios_m2 = {
    "Zarautz": 6210,
    "Donostia/San Sebastián": 6107,
    "Hondarribia": 5410,
    "Orio": 4483,
    "Astigarraga": 4351,
    "Getxo": 4336,
    "Berango": 4332,
    "Sopela": 4326,
    "Lekeitio": 3985,
    "Urduliz": 3939,
    "Plentzia": 3933,
    "Gorliz": 3883,
    "Lasarte-Oria": 3872,
    "Oiartzun": 3862,
    "Bakio": 3859,
}

# ============================================================
# UNIFICAR MUNICIPIOS
# ============================================================

municipios = sorted(
    set(precios_vivienda) | set(precios_m2)
)

registros = []

for municipio in municipios:

    registros.append({
        "municipio": municipio,
        "precio_medio_vivienda_eur":
            precios_vivienda.get(municipio),
        "precio_m2_eur":
            precios_m2.get(municipio),
        "anyo": 2025,
        "periodo": "Interanual a 2025T4",
        "fuente": "Colegio de Registradores",
        "pagina_precio_vivienda":
            40 if municipio in precios_vivienda else None,
        "pagina_precio_m2":
            30 if municipio in precios_m2 else None,
    })

df = pd.DataFrame(registros)

# Tipos de datos que permiten valores ausentes
df["precio_medio_vivienda_eur"] = (
    df["precio_medio_vivienda_eur"].astype("Int64")
)

df["precio_m2_eur"] = (
    df["precio_m2_eur"].astype("Int64")
)

# ============================================================
# GUARDAR CSV
# ============================================================

salida = Path(
    "data/processed/"
    "registradores_precios_municipios_2025.csv"
)

salida.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# RESULTADOS
# ============================================================

print("\nARCHIVO GENERADO:", salida)

print("\nMunicipios totales:", len(df))

print(
    "Con precio medio de vivienda:",
    df["precio_medio_vivienda_eur"].notna().sum()
)

print(
    "Con precio por m2:",
    df["precio_m2_eur"].notna().sum()
)

print(
    "Con ambos indicadores:",
    df[
        ["precio_medio_vivienda_eur", "precio_m2_eur"]
    ].notna().all(axis=1).sum()
)

print("\nDATOS:")
print(df.to_string(index=False))

print("\nPROCESAMIENTO FINALIZADO")
