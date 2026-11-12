
from pathlib import Path
import logging
import pdfplumber

logging.getLogger("pdfminer").setLevel(logging.ERROR)

archivo = Path(
    "data/raw/observatorio_vivienda/"
    "Informe-Comparacion-Precios_2025.pdf"
)

paginas = [3, 4, 11, 23, 25, 41, 42, 43, 45]

with pdfplumber.open(archivo) as pdf:

    for numero in paginas:

        pagina = pdf.pages[numero - 1]

        print("\n" + "=" * 60)
        print(f"PÁGINA {numero}")
        print("=" * 60)

        texto = pagina.extract_text() or ""

        print(texto[:2500])

        tablas = pagina.extract_tables()

        print(f"\nTablas detectadas: {len(tablas)}")

        for i, tabla in enumerate(tablas, start=1):

            print(f"\nTABLA {i}")

            for fila in tabla[:5]:
                print(fila)

print("\nINSPECCIÓN FINALIZADA")
