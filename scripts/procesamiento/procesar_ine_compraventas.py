
import json
from pathlib import Path
import pandas as pd

ORIGEN = Path(
    "data/raw/ine_api/datos_euskadi_total_viviendas.json"
)

DESTINO = Path(
    "data/processed/ine_compraventas_euskadi.csv"
)

with open(ORIGEN, encoding="utf-8") as f:
    datos = json.load(f)

territorios = {
    "País Vasco": "Euskadi",
    "Araba/Álava": "Álava",
    "Bizkaia": "Bizkaia",
    "Gipuzkoa": "Gipuzkoa"
}

indicadores = {
    "General": "compraventas_total",
    "Vivienda nueva": "compraventas_nueva",
    "Vivienda segunda mano": "compraventas_segunda_mano",
    "Vivienda libre": "compraventas_libre",
    "Vivienda protegida": "compraventas_protegida"
}

registros = []

for serie in datos:
    nombre = serie["Nombre"].strip()
    partes = [p.strip() for p in nombre.split(".")]

    territorio = territorios.get(partes[0])
    indicador = indicadores.get(partes[1])

    if territorio is None or indicador is None:
        raise ValueError(f"Serie no reconocida: {nombre}")

    for dato in serie.get("Data", []):
        mes = dato["T3_Periodo"].replace("M", "")
        periodo = f"{dato['Anyo']}M{mes}"

        registros.append({
            "territorio": territorio,
            "periodo": periodo,
            "indicador": indicador,
            "valor": dato.get("Valor"),
            "estado": dato.get("T3_TipoDato")
        })

df = pd.DataFrame(registros)

# Verificar duplicados
claves = ["territorio", "periodo", "indicador"]

if df.duplicated(subset=claves).any():
    raise ValueError("Hay registros duplicados")

# Convertir los indicadores en columnas
resultado = df.pivot(
    index=["territorio", "periodo"],
    columns="indicador",
    values="valor"
).reset_index()

resultado.columns.name = None

# Conservar el estado de los datos
estados = df.groupby(
    ["territorio", "periodo"]
)["estado"].agg(
    lambda x: ", ".join(sorted(x.dropna().unique()))
).reset_index()

resultado = resultado.merge(
    estados,
    on=["territorio", "periodo"],
    how="left",
    validate="one_to_one"
)

resultado = resultado.sort_values(
    ["territorio", "periodo"]
)

DESTINO.parent.mkdir(parents=True, exist_ok=True)

resultado.to_csv(
    DESTINO,
    index=False,
    encoding="utf-8-sig"
)

print("Archivo generado:", DESTINO)
print("Registros:", len(resultado))
print("Territorios:", resultado["territorio"].nunique())
print("Periodos:", resultado["periodo"].nunique())

print("\nVALORES NULOS:")
print(resultado.isna().sum().to_string())

print("\nESTADO DE LOS DATOS:")
print(resultado["estado"].value_counts().to_string())

print("\nPRIMERAS FILAS:")
print(resultado.head().to_string(index=False))

print("\nPROCESAMIENTO FINALIZADO")
