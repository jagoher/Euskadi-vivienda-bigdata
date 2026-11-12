
from pathlib import Path
import logging
import pdfplumber

logging.getLogger("pdfminer").setLevel(logging.ERROR)

ARCHIVO = Path(
    "data/raw/observatorio_vivienda/Euskadi-25T4.pdf"
)

PAGINAS = [29, 30, 35, 39, 40]

with pdfplumber.open(ARCHIVO) as pdf:

    for numero in PAGINAS:

        pagina = pdf.pages[numero - 1]

        print("\n" + "=" * 60)
        print(f"PÁGINA {numero}")
        print("=" * 60)

        texto = pagina.extract_text() or ""

        print(texto[:3500])

        tablas = pagina.extract_tables()

        print(f"\nTablas detectadas: {len(tablas)}")

        for i, tabla in enumerate(tablas, start=1):
            print(f"\nTABLA {i}")
            print(f"Filas: {len(tabla)}")

            for fila in tabla[:5]:
                print(fila)

print("\nINSPECCIÓN FINALIZADA")

