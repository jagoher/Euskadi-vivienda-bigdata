
from pathlib import Path
import pandas as pd
import pdfplumber

csv = Path(
    "data/processed/"
    "comparacion_precios_oferta_contratos_2025.csv"
)

pdf = Path(
    "data/raw/observatorio_vivienda/"
    "Informe-Comparacion-Precios_2025.pdf"
)

df = pd.read_csv(csv)

errores = []

with pdfplumber.open(pdf) as documento:

    for _, registro in df.iterrows():

        pagina = documento.pages[int(registro["pagina_pdf"]) - 1]

        tablas = pagina.extract_tables()

        valores_pdf = []

        for tabla in tablas:
            for fila in tabla:

                if len(fila) < 3 or fila[2] is None:
                    continue

                texto = str(fila[2]).strip()

                try:
                    if registro["mercado"] == "compraventa":
                        valor = float(texto.replace(".", ""))
                    else:
                        valor = float(texto.replace(",", "."))

                    valores_pdf.append(valor)

                except ValueError:
                    continue

        if registro["precio_m2_eur"] not in valores_pdf:

            errores.append({
                "ambito": registro["ambito"],
                "mercado": registro["mercado"],
                "fuente": registro["fuente"],
                "precio_csv": registro["precio_m2_eur"],
                "pagina_pdf": registro["pagina_pdf"],
            })

print("Registros comprobados:", len(df))
print("Precios no encontrados en su página:", len(errores))

if errores:
    print(pd.DataFrame(errores).to_string(index=False))
else:
    print("Todos los precios aparecen en sus páginas de origen.")
