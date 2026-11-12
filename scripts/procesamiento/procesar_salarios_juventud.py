
from pathlib import Path
import pandas as pd

# ==========================================
# 1. RUTAS
# ==========================================

ORIGEN = Path(
    "data/raw/observatorio_juventud/iovj-empleo-economico.json"
)

DESTINO = Path(
    "data/processed/salarios_juveniles_euskadi.csv"
)

# ==========================================
# 2. CARGAR DATOS
# ==========================================

df = pd.read_json(ORIGEN)

# ==========================================
# 3. FILTRAR INDICADOR SALARIAL
# ==========================================

df = df[
    df["Indicador"]
    == "Salario mensual neto medio, según sexo, grupos de edad y TTHH"
].copy()

# ==========================================
# 4. NORMALIZAR COLUMNAS
# ==========================================

df = df.rename(columns={
    "Periodo": "anyo",
    "Categoria1Valor": "categoria",
    "Valor": "salario_neto_mensual"
})

df["anyo"] = pd.to_numeric(
    df["anyo"], errors="raise"
).astype(int)

df["salario_neto_mensual"] = pd.to_numeric(
    df["salario_neto_mensual"], errors="coerce"
)

# ==========================================
# 5. CLASIFICAR CATEGORIAS
# ==========================================

territorios = {
    "Total": "Euskadi",
    "Bizkaia": "Bizkaia",
    "Gipuzkoa": "Gipuzkoa",
    "Álava": "Álava"
}

edades = ["18-29 años", "30-34 años"]
sexos = ["Mujeres", "Hombres"]

def clasificar(categoria):
    if categoria in territorios:
        return "territorio"
    if categoria in edades:
        return "edad"
    if categoria in sexos:
        return "sexo"
    return "desconocido"

df["dimension"] = df["categoria"].apply(clasificar)

df["categoria"] = df["categoria"].replace(territorios)

if (df["dimension"] == "desconocido").any():
    raise ValueError("Hay categorías sin clasificar")

# ==========================================
# 6. SELECCIONAR COLUMNAS
# ==========================================

resultado = df[
    [
        "anyo",
        "dimension",
        "categoria",
        "salario_neto_mensual"
    ]
].sort_values(
    ["anyo", "dimension", "categoria"]
)

if resultado.duplicated(
    subset=["anyo", "dimension", "categoria"]
).any():
    raise ValueError("Hay registros duplicados")

# ==========================================
# 7. GUARDAR
# ==========================================

DESTINO.parent.mkdir(parents=True, exist_ok=True)

resultado.to_csv(
    DESTINO,
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 8. RESUMEN
# ==========================================

print("Archivo generado:", DESTINO)
print("Registros:", len(resultado))
print("Años:", resultado["anyo"].nunique())

print("\nVALORES NULOS:")
print(resultado.isna().sum().to_string())

print("\nSALARIOS 2024:")
print(
    resultado[resultado["anyo"] == 2024]
    .to_string(index=False)
)

print("\nPROCESAMIENTO FINALIZADO")
