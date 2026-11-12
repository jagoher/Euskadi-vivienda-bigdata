
import pandas as pd
import unicodedata
from pathlib import Path

# ==========================================
# 1. CARGAR DATOS
# ==========================================

carpeta = Path("data/processed")

ine = pd.read_csv(
    carpeta / "catalogo_municipios_euskadi_2026.csv",
    dtype={"codigo_ine": str}
)

eustat = pd.read_csv(
    carpeta / "alquiler_municipios_eustat.csv"
)


# Equivalencias entre Eustat e INE 2026
equivalencias = {
    "Arrankudiaga": "Arrankudiaga-Zollo",
    "Donostia / San Sebastián": "Donostia/San Sebastián",
    "Munitibar -Arbatzegi Gerrikaitz-": "Munitibar-Arbatzegi Gerrikaitz",
    "Ribera Baja/Erribera Beitia": "Ribera Baja/Erriberabeitia",
    "Urduña-Orduña": "Urduña/Orduña",
}

# Conservar los nombres originales de Eustat
eustat["municipio_original"] = eustat["municipio"]

# Aplicar las equivalencias
eustat["municipio"] = eustat["municipio"].replace(equivalencias)



# ==========================================
# 2. NORMALIZAR NOMBRES
# ==========================================

def normalizar(nombre):
    nombre = str(nombre).strip().lower()

    nombre = unicodedata.normalize("NFKD", nombre)

    nombre = "".join(
        c for c in nombre
        if not unicodedata.combining(c)
    )

    nombre = " ".join(nombre.split())

    return nombre


ine["nombre_comparacion"] = (
    ine["municipio_ine"].apply(normalizar)
)

eustat["nombre_comparacion"] = (
    eustat["municipio"].apply(normalizar)
)

# ==========================================
# 3. COMPARAR MUNICIPIOS
# ==========================================

coincidencias = set(ine["nombre_comparacion"]) & set(
    eustat["nombre_comparacion"]
)

solo_ine = ine[
    ~ine["nombre_comparacion"].isin(coincidencias)
]

solo_eustat = eustat[
    ~eustat["nombre_comparacion"].isin(coincidencias)
]

print("\nCOMPARACIÓN EUSTAT - INE")
print("=" * 50)

print("Municipios INE:", len(ine))
print("Municipios Eustat:", len(eustat))
print("Coincidencias:", len(coincidencias))

print("\nNOMBRES SOLO EN INE")
print(
    solo_ine["municipio_ine"].to_string(index=False)
)

print("\nNOMBRES SOLO EN EUSTAT")
print(
    solo_eustat["municipio"].to_string(index=False)
)

print("\nCOMPARACIÓN FINALIZADA")
