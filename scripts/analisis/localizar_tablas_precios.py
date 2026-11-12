
from pathlib import Path
import pdfplumber

archivo = Path(
    "data/raw/observatorio_vivienda/"
    "Informe-Comparacion-Precios_2025.pdf"
)

with pdfplumber.open(archivo) as pdf:

    for numero in range(5, 41):

        pagina = pdf.pages[numero - 1]
        texto = pagina.extract_text() or ""

        tablas = pagina.extract_tables()

        tablas_utiles = [
            tabla for tabla in tablas
            if len(tabla) >= 4
            and any(
                "Precio / m2" in str(fila)
                or "Precio / m²" in str(fila)
                for fila in tabla[:3]
            )
        ]

        if tablas_utiles:
            print(
                f"Página {numero}: "
                f"{len(tablas_utiles)} tabla(s) de precios"
            )

            for tabla in tablas_utiles:
                for fila in tabla[:3]:
                    print(" ", fila)

print("\nBÚSQUEDA FINALIZADA")
