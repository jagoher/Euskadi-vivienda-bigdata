
from pathlib import Path
from collections import Counter
from hashlib import sha256
import os
import sys
import time

from dotenv import load_dotenv
from hdfs import InsecureClient


# ============================================================
# 1. CONFIGURACION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

CARPETA_LOCAL = BASE_DIR / "data" / "raw"

HDFS_URL = os.getenv("HDFS_ADDRESS_CLUSTER")
HDFS_USER = os.getenv("HDFS_USER", "iabd-user6")

HDFS_BASE = os.getenv(
    "HDFS_BASE",
    "/user/iabd-user6/euskadi_vivienda"
)

CARPETA_HDFS = HDFS_BASE.rstrip("/") + "/raw"

TAMANO_BLOQUE = 1024 * 1024  # 1 MiB


# ============================================================
# 2. CALCULAR SHA-256 LOCAL
# ============================================================

def hash_local(ruta):
    """Calcula el SHA-256 de un archivo local."""

    digest = sha256()

    with open(ruta, "rb") as archivo:

        while True:

            bloque = archivo.read(TAMANO_BLOQUE)

            if not bloque:
                break

            digest.update(bloque)

    return digest.hexdigest()


# ============================================================
# 3. CALCULAR SHA-256 HDFS
# ============================================================

def hash_hdfs(cliente, ruta):
    """Calcula el SHA-256 leyendo el archivo desde HDFS."""

    digest = sha256()

    with cliente.read(ruta) as archivo:

        while True:

            bloque = archivo.read(TAMANO_BLOQUE)

            if not bloque:
                break

            digest.update(bloque)

    return digest.hexdigest()


# ============================================================
# 4. INVENTARIO DE ARCHIVOS LOCALES
# ============================================================

def inventario_local():
    """Obtiene todos los archivos originales de data/raw."""

    inventario = {}

    for ruta in CARPETA_LOCAL.rglob("*"):

        if ruta.is_file():

            relativa = ruta.relative_to(
                CARPETA_LOCAL
            ).as_posix()

            inventario[relativa] = ruta

    return inventario


# ============================================================
# 5. INVENTARIO DE ARCHIVOS HDFS
# ============================================================

def inventario_hdfs(cliente):
    """
    Recorre recursivamente HDFS y obtiene los archivos.

    Se utiliza status=False para que cliente.walk()
    devuelva nombres de directorios y archivos
    como cadenas de texto.
    """

    inventario = {}

    for directorio, _, archivos in cliente.walk(
        CARPETA_HDFS,
        status=False
    ):

        for nombre in archivos:

            ruta_completa = (
                directorio.rstrip("/") + "/" + nombre
            )

            relativa = ruta_completa[
                len(CARPETA_HDFS.rstrip("/")) + 1:
            ]

            estado = cliente.status(ruta_completa)

            inventario[relativa] = {
                "ruta": ruta_completa,
                "tamano": estado["length"]
            }

    return inventario


# ============================================================
# 6. PROGRAMA PRINCIPAL
# ============================================================

def main():

    inicio = time.time()

    print("=" * 65)
    print("AUDITORIA DE INTEGRIDAD - DATA/RAW VS HDFS")
    print("=" * 65)

    print(f"Origen local: {CARPETA_LOCAL}")
    print(f"Destino HDFS: {CARPETA_HDFS}")
    print(f"Usuario HDFS: {HDFS_USER}")

    # --------------------------------------------------------
    # VALIDACIONES INICIALES
    # --------------------------------------------------------

    if not CARPETA_LOCAL.is_dir():

        print("\nERROR: No existe la carpeta local data/raw")
        sys.exit(1)

    if not HDFS_URL:

        print("\nERROR: Falta HDFS_ADDRESS_CLUSTER en .env")
        sys.exit(1)

    try:

        cliente = InsecureClient(
            HDFS_URL,
            user=HDFS_USER
        )

        estado_directorio = cliente.status(
            CARPETA_HDFS,
            strict=False
        )

        if estado_directorio is None:

            print("\nERROR: No existe la carpeta raw en HDFS")
            sys.exit(1)

        print("\nConectado correctamente a HDFS.")

        # ----------------------------------------------------
        # INVENTARIOS
        # ----------------------------------------------------

        locales = inventario_local()
        remotos = inventario_hdfs(cliente)

        rutas_locales = set(locales.keys())
        rutas_remotas = set(remotos.keys())

        comunes = sorted(
            rutas_locales & rutas_remotas
        )

        faltantes = sorted(
            rutas_locales - rutas_remotas
        )

        adicionales = sorted(
            rutas_remotas - rutas_locales
        )

        print("\n" + "-" * 65)
        print("INVENTARIO")
        print("-" * 65)

        print(f"Archivos locales: {len(locales)}")
        print(f"Archivos en HDFS: {len(remotos)}")
        print(f"Archivos comunes: {len(comunes)}")
        print(f"Faltantes en HDFS: {len(faltantes)}")
        print(f"Adicionales en HDFS: {len(adicionales)}")

        # ----------------------------------------------------
        # COMPARACION DE ARCHIVOS
        # ----------------------------------------------------

        correctos = 0

        errores_tamano = []
        errores_hash = []
        errores_lectura = []

        print("\n" + "-" * 65)
        print("COMPROBACION SHA-256")
        print("-" * 65)

        for numero, relativa in enumerate(
            comunes,
            start=1
        ):

            ruta_local = locales[relativa]
            datos_hdfs = remotos[relativa]

            try:

                # Comprobar tamanos

                tamano_local = ruta_local.stat().st_size
                tamano_hdfs = datos_hdfs["tamano"]

                if tamano_local != tamano_hdfs:

                    errores_tamano.append(relativa)

                    print(
                        f"[{numero}/{len(comunes)}] "
                        f"ERROR TAMANO: {relativa}"
                    )

                    print(
                        f"  Local: {tamano_local} bytes"
                    )

                    print(
                        f"  HDFS:  {tamano_hdfs} bytes"
                    )

                    continue

                # Calcular hashes

                sha_local = hash_local(ruta_local)

                sha_remoto = hash_hdfs(
                    cliente,
                    datos_hdfs["ruta"]
                )

                # Comparar hashes

                if sha_local == sha_remoto:

                    correctos += 1

                    print(
                        f"[{numero}/{len(comunes)}] "
                        f"OK: {relativa}"
                    )

                else:

                    errores_hash.append(relativa)

                    print(
                        f"[{numero}/{len(comunes)}] "
                        f"ERROR SHA-256: {relativa}"
                    )

                    print(f"  Local: {sha_local}")
                    print(f"  HDFS:  {sha_remoto}")

            except Exception as error:

                errores_lectura.append(relativa)

                print(
                    f"[{numero}/{len(comunes)}] "
                    f"ERROR LECTURA: {relativa}"
                )

                print(f"  Detalle: {error}")

        # ----------------------------------------------------
        # ARCHIVOS FALTANTES
        # ----------------------------------------------------

        if faltantes:

            print("\nARCHIVOS FALTANTES EN HDFS:")

            for ruta in faltantes:
                print(f"  - {ruta}")

        # ----------------------------------------------------
        # ARCHIVOS ADICIONALES
        # ----------------------------------------------------

        if adicionales:

            print("\nARCHIVOS ADICIONALES EN HDFS:")

            for ruta in adicionales:
                print(f"  - {ruta}")

        # ----------------------------------------------------
        # RESUMEN POR CARPETA
        # ----------------------------------------------------

        print("\n" + "-" * 65)
        print("RESUMEN POR CARPETA")
        print("-" * 65)

        conteo_local = Counter(
            ruta.split("/")[0]
            for ruta in rutas_locales
        )

        conteo_hdfs = Counter(
            ruta.split("/")[0]
            for ruta in rutas_remotas
        )

        carpetas = sorted(
            set(conteo_local) | set(conteo_hdfs)
        )

        for carpeta in carpetas:

            print(
                f"{carpeta:28} "
                f"Local: {conteo_local[carpeta]:3} | "
                f"HDFS: {conteo_hdfs[carpeta]:3}"
            )

        # ----------------------------------------------------
        # RESULTADO FINAL
        # ----------------------------------------------------

        tiempo = time.time() - inicio

        total_errores = (
            len(faltantes)
            + len(adicionales)
            + len(errores_tamano)
            + len(errores_hash)
            + len(errores_lectura)
        )

        print("\n" + "=" * 65)
        print("RESULTADO FINAL")
        print("=" * 65)

        print(f"Archivos locales: {len(locales)}")
        print(f"Archivos HDFS: {len(remotos)}")
        print(f"Archivos identicos: {correctos}")
        print(f"Faltantes: {len(faltantes)}")
        print(f"Adicionales: {len(adicionales)}")
        print(f"Errores de tamano: {len(errores_tamano)}")
        print(f"Errores SHA-256: {len(errores_hash)}")
        print(f"Errores de lectura: {len(errores_lectura)}")
        print(f"Tiempo: {tiempo:.2f} segundos")

        if (
            total_errores == 0
            and correctos == len(locales)
            and len(locales) == len(remotos)
        ):

            print("\n" + "=" * 65)
            print("AUDITORIA SUPERADA")
            print("TODOS LOS ARCHIVOS SON IDENTICOS")
            print("INTEGRIDAD SHA-256 VERIFICADA")
            print("=" * 65)

        else:

            print("\n" + "=" * 65)
            print("AUDITORIA NO SUPERADA")
            print("Se han detectado diferencias.")
            print("=" * 65)

            sys.exit(1)

    except Exception as error:

        print(f"\nERROR GENERAL: {error}")
        sys.exit(1)


# ============================================================
# 7. EJECUCION
# ============================================================

if __name__ == "__main__":
    main()
