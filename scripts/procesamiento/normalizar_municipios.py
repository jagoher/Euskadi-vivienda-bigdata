
import pandas as pd
from pathlib import Path

# Equivalencias de nombres municipales
equivalencias = {
    "Arrasate": "Arrasate/Mondragón",
    "Donostia": "Donostia/San Sebastián",
    "Donostia / San Sebastián": "Donostia/San Sebastián",
}

carpeta = Path("data/processed")

archivos = {
    "EMAL": "emal_alquileres_vigentes_2025.csv",
    "INE": "ine_precios_vivienda_municipios.csv",
    "Registradores": "registradores_precios_municipios_2025.csv",
}

for fuente, archivo in archivos.items():

    df = pd.read_csv(
        carpeta / archivo,
        dtype={"codigo_ine": "string"}
    )

    # Conservar el nombre original
    df["municipio_original"] = df["municipio"]

    # Crear nombre normalizado
    df["municipio_normalizado"] = (
        df["municipio"].replace(equivalencias)
    )

    salida = carpeta / archivo.replace(
        ".csv", "_normalizado.csv"
    )

    df.to_csv(
        salida,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\n{fuente}")
    print("Archivo generado:", salida)
    print("Registros:", len(df))

    cambios = df[
        df["municipio_original"]
        != df["municipio_normalizado"]
    ]

    print("Nombres modificados:", len(cambios))

    if not cambios.empty:
        print(
            cambios[
                ["municipio_original", "municipio_normalizado"]
            ].drop_duplicates().to_string(index=False)
        )

print("\nNORMALIZACIÓN FINALIZADA")
