
from pathlib import Path
import pandas as pd

# ==========================================
# 1. RUTAS
# ==========================================

ORIGEN = Path(
    "data/raw/observatorio_juventud/iovj-empleo-economico.json"
)

DESTINO = Path(
    "data/processed/economia_juvenil_euskadi.csv"
)

# ==========================================
# 2. CARGAR DATOS
# ==========================================

df = pd.read_json(ORIGEN)

print("Registros originales del JSON:", len(df))

# ==========================================
# 3. SELECCIONAR INDICADORES ECONOMICOS
# ==========================================

indicadores = {
    "Disponibilidad económica mensual superior a 600 euros": (
        "disponibilidad_superior_600",
        "porcentaje"
    ),
    "Renta personal media anual de jóvenes de 25 a 29 años": (
        "renta_personal_anual_25_29",
        "euros_anuales"
    )
}

registros = []

for texto, (codigo, unidad) in indicadores.items():

    seleccion = df[
        df["Indicador"].str.contains(
            texto,
            regex=False,
            na=False
        )
    ].copy()

    print(f"{codigo}: {len(seleccion)} registros")

    for _, fila in seleccion.iterrows():

        categoria = fila["Categoria1Valor"]

        if categoria == "Total":
            categoria = "Euskadi"

        registros.append({
            "anyo": fila["Periodo"],
            "indicador": codigo,
            "categoria": categoria,
            "valor": fila["Valor"],
            "unidad": unidad
        })

# ==========================================
# 4. CREAR DATAFRAME
# ==========================================

resultado = pd.DataFrame(registros)

resultado["anyo"] = pd.to_numeric(
    resultado["anyo"],
    errors="raise"
).astype(int)

resultado["valor"] = pd.to_numeric(
    resultado["valor"],
    errors="coerce"
)

print("\nRegistros seleccionados:", len(resultado))

# ==========================================
# 5. COMPROBAR DUPLICADOS
# ==========================================

claves = [
    "anyo",
    "indicador",
    "categoria"
]

# Comprobar si una misma clave tiene
# valores diferentes, incluyendo nulos

conflictos = (
    resultado.groupby(
        claves,
        dropna=False
    )["valor"]
    .nunique(dropna=False)
)

if (conflictos > 1).any():
    print("\nCONFLICTOS DETECTADOS:")
    print(conflictos[conflictos > 1])

    raise ValueError(
        "Existen registros con valores diferentes "
        "para el mismo año, indicador y categoría"
    )

# Contar duplicados
duplicados = resultado.duplicated(
    subset=claves,
    keep="first"
).sum()

print("Duplicados detectados:", duplicados)

# Eliminar únicamente registros repetidos
resultado = resultado.drop_duplicates(
    subset=claves,
    keep="first"
).copy()

print("Duplicados eliminados:", duplicados)

# ==========================================
# 6. ORDENAR DATOS
# ==========================================

resultado = resultado.sort_values(
    [
        "indicador",
        "anyo",
        "categoria"
    ]
).reset_index(drop=True)

# ==========================================
# 7. GUARDAR CSV
# ==========================================

DESTINO.parent.mkdir(
    parents=True,
    exist_ok=True
)

resultado.to_csv(
    DESTINO,
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 8. VALIDACION FINAL
# ==========================================

print("\n===================================")
print("RESULTADO DEL PROCESAMIENTO")
print("===================================")

print("Archivo generado:", DESTINO)
print("Registros finales:", len(resultado))

print("\nREGISTROS POR INDICADOR:")
print(
    resultado["indicador"]
    .value_counts()
    .to_string()
)

print("\nVALORES NULOS:")
print(
    resultado.isna()
    .sum()
    .to_string()
)

print("\nPERIODOS POR INDICADOR:")
print(
    resultado.groupby("indicador")["anyo"]
    .agg(["min", "max", "nunique"])
    .to_string()
)

# ==========================================
# 9. MOSTRAR ULTIMOS DATOS
# ==========================================

print("\n===================================")
print("ULTIMOS DATOS DISPONIBLES")
print("===================================")

for indicador, grupo in resultado.groupby("indicador"):

    ultimo_anyo = grupo["anyo"].max()

    print(f"\nINDICADOR: {indicador}")
    print(f"AÑO: {ultimo_anyo}")

    print(
        grupo[
            grupo["anyo"] == ultimo_anyo
        ].to_string(index=False)
    )

print("\n===================================")
print("PROCESAMIENTO FINALIZADO")
print("===================================")
