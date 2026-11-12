
from pathlib import Path
import pandas as pd
import pdfplumber
import re

# ============================================================
# 1. RUTAS
# ============================================================

archivo = Path(
    "data/raw/observatorio_vivienda/"
    "Informe-Comparacion-Precios_2025.pdf"
)

salida = Path(
    "data/processed/"
    "comparacion_precios_oferta_contratos_2025.csv"
)

# ============================================================
# 2. PÁGINAS Y ÁMBITOS GEOGRÁFICOS
# ============================================================

paginas = {
    5: ("Euskadi", "compraventa"),
    7: ("Araba/Álava", "compraventa"),
    9: ("Bizkaia", "compraventa"),
    11: ("Gipuzkoa", "compraventa"),
    13: ("Vitoria-Gasteiz", "compraventa"),
    15: ("Bilbao", "compraventa"),
    17: ("Donostia/San Sebastián", "compraventa"),

    23: ("Euskadi", "alquiler"),
    25: ("Araba/Álava", "alquiler"),
    27: ("Bizkaia", "alquiler"),
    29: ("Gipuzkoa", "alquiler"),
    31: ("Vitoria-Gasteiz", "alquiler"),
    33: ("Bilbao", "alquiler"),
    35: ("Donostia/San Sebastián", "alquiler"),
}

# ============================================================
# 3. FUNCIONES
# ============================================================

def convertir_numero(valor, mercado):

    if valor is None:
        return None

    texto = str(valor).strip()

    if mercado == "compraventa":
        texto = texto.replace(".", "")
    else:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return None


def identificar_indicador(texto, mercado):

    texto = re.sub(r"\s+", " ", texto.lower())

    if "idealista" in texto:
        return "Idealista", "oferta"

    if "fotocasa" in texto:
        return "Fotocasa", "oferta"

    if "pisos.com" in texto:
        return "Pisos.com", "oferta"

    if "mediana" in texto or (
        mercado == "compraventa" and "total" in texto
    ):
        return (
            "ECVI" if mercado == "compraventa" else "EMAL",
            "mediana"
        )

    if "usadas" in texto or "media" in texto:
        return (
            "ECVI" if mercado == "compraventa" else "EMAL",
            "media"
        )

    return None, None


def descripcion_indicador(fila):

    if fila["fuente"] == "ECVI":

        if fila["estadistico"] == "mediana":
            return (
                "Compraventa registrada - "
                "total viviendas - mediana"
            )

        return (
            "Compraventa registrada - "
            "viviendas usadas - media"
        )

    if fila["fuente"] == "EMAL":

        return (
            "Contratos alquiler registrados - "
            f"{fila['estadistico']}"
        )

    return (
        "Precio de oferta inmobiliaria - "
        f"{fila['fuente']}"
    )


# ============================================================
# 4. EXTRACCIÓN DE DATOS DEL PDF
# ============================================================

registros = []

with pdfplumber.open(archivo) as pdf:

    for numero, (ambito, mercado) in paginas.items():

        tablas = pdf.pages[numero - 1].extract_tables()

        for tabla in tablas:

            if not tabla or len(tabla) < 4:
                continue

            for fila in tabla[1:]:

                if len(fila) < 3:
                    continue

                indicador = str(fila[1] or "")

                fuente, estadistico = identificar_indicador(
                    indicador,
                    mercado
                )

                if fuente is None:
                    continue

                precio = convertir_numero(
                    fila[2],
                    mercado
                )

                if precio is None:
                    continue

                registros.append({
                    "ambito": ambito,
                    "mercado": mercado,
                    "fuente": fuente,
                    "estadistico": estadistico,
                    "precio_m2_eur": precio,
                    "periodo": "2025T4",
                    "pagina_pdf": numero,
                })


# ============================================================
# 5. CREACIÓN DEL DATAFRAME
# ============================================================

df = pd.DataFrame(registros)

# Añadir descripción metodológica
df["descripcion_indicador"] = df.apply(
    descripcion_indicador,
    axis=1
)

# ============================================================
# 6. VALIDACIONES
# ============================================================

print("\nVALIDACIÓN DE DATOS")
print("=" * 50)

print("Registros:", len(df))

print("Valores nulos:")
print(df.isnull().sum())

print(
    "Duplicados:",
    df.duplicated(
        subset=[
            "ambito",
            "mercado",
            "fuente",
            "estadistico",
            "periodo"
        ]
    ).sum()
)

print(
    "Precios no positivos:",
    (df["precio_m2_eur"] <= 0).sum()
)

print("\nRegistros por mercado:")
print(df.groupby("mercado").size())

print("\nRegistros por fuente:")
print(df.groupby("fuente").size())

# ============================================================
# 7. GUARDAR CSV
# ============================================================

salida.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nArchivo generado:", salida)

print("\nPrimeros registros:")
print(df.head(10).to_string(index=False))

print("\nPROCESAMIENTO FINALIZADO")
