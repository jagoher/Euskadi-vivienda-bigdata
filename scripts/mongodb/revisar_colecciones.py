
from collections import Counter
from datetime import date, datetime

from pymongo.errors import PyMongoError

from database import conectar, cerrar_conexion
from config import COLLECTIONS


def campos_documento(documento, prefijo=""):
    """Devuelve las rutas de los campos de un documento."""
    campos = set()

    for clave, valor in documento.items():
        ruta = f"{prefijo}.{clave}" if prefijo else clave
        campos.add(ruta)

        if isinstance(valor, dict):
            campos.update(campos_documento(valor, ruta))

        elif isinstance(valor, list):
            for elemento in valor:
                if isinstance(elemento, dict):
                    campos.update(
                        campos_documento(elemento, ruta)
                    )

    return campos


def revisar_coleccion(db, nombre):
    coleccion = db[nombre]
    documentos = list(coleccion.find({}))

    print(f"\n{'=' * 55}")
    print(f"COLECCION: {nombre}")
    print(f"{'=' * 55}")
    print("Total documentos:", len(documentos))

    if not documentos:
        return

    contador_campos = Counter()
    tipos = {}
    valores_territoriales = set()
    anos = set()

    for doc in documentos:
        rutas = campos_documento(doc)
        contador_campos.update(rutas)

        for campo, valor in doc.items():
            tipos.setdefault(campo, set()).add(
                type(valor).__name__
            )

        # Posibles claves territoriales
        for campo in (
            "territorio_id",
            "municipio_id",
            "provincia"
        ):
            valor = doc.get(campo)
            if isinstance(valor, (str, int)):
                valores_territoriales.add(
                    (campo, str(valor))
                )

        # Años en campos principales y subdocumentos
        def buscar_anos(obj):
            if isinstance(obj, dict):
                for clave, valor in obj.items():
                    if clave.lower() in (
                        "anyo",
                        "anio",
                        "año",
                        "year"
                    ):
                        if isinstance(valor, int) and not isinstance(valor, bool):
                            anos.add(valor)
                    elif clave.lower().startswith("anyo_"):
                        if isinstance(valor, int) and not isinstance(valor, bool):
                            anos.add(valor)

                    if isinstance(valor, (dict, list)):
                        buscar_anos(valor)

            elif isinstance(obj, list):
                for elemento in obj:
                    buscar_anos(elemento)

        buscar_anos(doc)

    print("\nCAMPOS Y COBERTURA:")
    for campo, cantidad in sorted(contador_campos.items()):
        porcentaje = cantidad / len(documentos) * 100
        print(f"  {campo}: {cantidad}/{len(documentos)} ({porcentaje:.1f}%)")

    print("\nTIPOS DE CAMPOS PRINCIPALES:")
    for campo, conjunto in sorted(tipos.items()):
        print(f"  {campo}: {', '.join(sorted(conjunto))}")

    print("\nANOS DETECTADOS:")
    print(sorted(anos) if anos else "Sin anos detectados")

    print("\nREFERENCIAS TERRITORIALES (muestra):")
    for campo, valor in sorted(valores_territoriales)[:15]:
        print(f"  {campo}: {valor}")


def revisar_relacion_anuncios(db):
    print("\n=== RELACION ANUNCIOS - MUNICIPIOS ===")

    if not {"anuncios", "municipios"}.issubset(
        set(db.list_collection_names())
    ):
        print("Faltan colecciones para comprobar la relacion.")
        return

    municipios = {
        doc["_id"]
        for doc in db["municipios"].find({}, {"_id": 1})
    }

    total = 0
    validos = 0
    sin_referencia = 0
    inexistentes = Counter()

    for anuncio in db["anuncios"].find(
        {}, {"municipio_id": 1}
    ):
        total += 1
        codigo = anuncio.get("municipio_id")

        if codigo is None:
            sin_referencia += 1
        elif codigo in municipios:
            validos += 1
        else:
            inexistentes[str(codigo)] += 1

    print("Total anuncios:", total)
    print("Referencias validas:", validos)
    print("Sin municipio_id:", sin_referencia)
    print("Referencias inexistentes:", sum(inexistentes.values()))

    for codigo, cantidad in inexistentes.most_common(10):
        print(f"  Codigo {codigo}: {cantidad} anuncios")


def main():
    db = None

    try:
        db = conectar()

        if db is None:
            print("ERROR: No se pudo conectar a MongoDB.")
            return

        print("Base de datos:", db.name)

        existentes = set(db.list_collection_names())

        for nombre in (
            "municipios",
            "anuncios",
            "mercado_alquiler",
            "salarios",
            "economia_juvenil"
        ):
            if nombre in existentes:
                revisar_coleccion(db, nombre)
            else:
                print(f"\nColeccion no encontrada: {nombre}")

        revisar_relacion_anuncios(db)

    except PyMongoError as e:
        print("ERROR MongoDB:", e)

    finally:
        cerrar_conexion()


if __name__ == "__main__":
    main()
