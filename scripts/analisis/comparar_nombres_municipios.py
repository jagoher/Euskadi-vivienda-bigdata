
from pathlib import Path
import pandas as pd
import unicodedata
import re

carpeta = Path("data/processed")

archivos = {
    "Eustat": "alquiler_municipios_eustat.csv",
    "EMAL": "emal_alquileres_vigentes_2025.csv",
    "INE": "ine_precios_vivienda_municipios.csv",
    "Registradores": "registradores_precios_municipios_2025.csv",
}


def normalizar(texto):
    texto = str(texto).strip().lower()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto


municipios = {}

for fuente, archivo in archivos.items():

    df = pd.read_csv(
        carpeta / archivo,
        dtype={"codigo_ine": "string"}
    )

    municipios[fuente] = {
        normalizar(nombre): nombre
        for nombre in df["municipio"].dropna().unique()
    }


referencia = set(municipios["Eustat"])

print("\nCOMPARACIÓN DE MUNICIPIOS")
print("=" * 55)

for fuente in ["EMAL", "INE", "Registradores"]:

    actuales = set(municipios[fuente])

    coincidentes = actuales & referencia
    diferentes = actuales - referencia

    print(f"\nFUENTE: {fuente}")
    print("Municipios:", len(actuales))
    print("Coincidencias con Eustat:", len(coincidentes))
    print("Sin coincidencia:", len(diferentes))

    for nombre in sorted(diferentes):
        print("  -", municipios[fuente][nombre])


print("\nANÁLISIS FINALIZADO")
