
import json
from pathlib import Path

# Directorio principal del proyecto
BASE = Path(__file__).resolve().parents[2]
DATOS = BASE / "data" / "mongodb"


def leer_json(nombre):
    with open(DATOS / nombre, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def main():
    catalogo = leer_json("catalogo_municipios_euskadi_2026.json")
    viviendas = leer_json("vivienda_euskadi_municipios_integrado.json")
    indicadores = leer_json("indicadores_vivienda_juvenil_euskadi.json")

    viviendas_por_ine = {
        fila["codigo_ine"]: fila for fila in viviendas
    }

    indicadores_por_ine = {
        fila["codigo_ine"]: fila for fila in indicadores
    }

    municipios = []

    for fila in catalogo:
        codigo = fila["codigo_ine"]

        vivienda = viviendas_por_ine[codigo].copy()
        indicador = indicadores_por_ine[codigo].copy()

        # Evitar repetir los campos de identificación
        for campo in ("codigo_ine", "municipio_ine", "provincia"):
            vivienda.pop(campo, None)
            indicador.pop(campo, None)

        documento = {
            "_id": codigo,
            "nombre": fila["municipio_ine"],
            "provincia": fila["provincia"],
            "territorio_id": codigo[:2],
            "vivienda": vivienda,
            "indicadores": indicador
        }

        municipios.append(documento)

    salida = DATOS / "municipios_mongodb.json"

    with open(salida, "w", encoding="utf-8") as archivo:
        json.dump(municipios, archivo, ensure_ascii=False, indent=2)

    print("Documentos generados:", len(municipios))
    print("IDs únicos:", len({m["_id"] for m in municipios}))
    print("Archivo generado:", salida)

    print("\nEjemplo del primer municipio:")
    print(json.dumps(municipios[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
