
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
ARCHIVO = BASE / "data" / "mongodb" / "municipios_mongodb.json"

with open(ARCHIVO, encoding="utf-8") as f:
    municipios = json.load(f)

print("=== VALIDACION MUNICIPIOS ===")

# 1. Identificadores
ids = [m["_id"] for m in municipios]

print("Total documentos:", len(municipios))
print("IDs unicos:", len(set(ids)))
print("IDs duplicados:", len(ids) - len(set(ids)))

# 2. Codigos INE
ine_invalidos = [
    m["_id"] for m in municipios
    if not isinstance(m["_id"], str)
    or len(m["_id"]) != 5
    or not m["_id"].isdigit()
]

print("Codigos INE invalidos:", len(ine_invalidos))

# 3. Valores negativos
negativos = []

for m in municipios:
    indicadores = m["indicadores"]

    for campo in ("salario_neto_mensual", "esfuerzo_alquiler_pct"):
        valor = indicadores.get(campo)
        if isinstance(valor, (int, float)) and valor < 0:
            negativos.append((m["_id"], campo))

    alquiler = m["vivienda"].get("eustat_alquiler_medio_2024")
    if isinstance(alquiler, (int, float)) and alquiler < 0:
        negativos.append((m["_id"], "alquiler"))

print("Valores negativos:", len(negativos))

# 4. Coherencia del esfuerzo
incoherencias = []

for m in municipios:
    alquiler = m["vivienda"].get("eustat_alquiler_medio_2024")
    salario = m["indicadores"].get("salario_neto_mensual")
    esfuerzo = m["indicadores"].get("esfuerzo_alquiler_pct")

    if alquiler is not None and salario is not None and salario > 0:
        calculado = round(alquiler / salario * 100, 2)

        if esfuerzo is None or abs(calculado - esfuerzo) > 0.02:
            incoherencias.append(m["_id"])

print("Esfuerzos incoherentes:", len(incoherencias))

print("\n=== FIN VALIDACION ===")
