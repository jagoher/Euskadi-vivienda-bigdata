from pathlib import Path
import shutil
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / 'data' / 'raw' / 'portales' / 'pisos_com'
NUEVO = CARPETA / '3_pisos_donostia_corregido.csv'
ALTERNATIVO = RAIZ / '3_pisos_donostia_corregido.csv'
DESTINO = CARPETA / '3_pisos_donostia.csv'
RESPALDO = CARPETA / '3_pisos_donostia_original_596_backup.csv'

origen = NUEVO if NUEVO.exists() else ALTERNATIVO
if not origen.exists():
    raise SystemExit('No se encuentra 3_pisos_donostia_corregido.csv en la raiz ni en data/raw/portales/pisos_com/')

CARPETA.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(origen, dtype={'id': 'string'})
requeridas = {'precio', 'm2', 'zona', 'descripcion'}
faltantes = requeridas - set(df.columns)
if faltantes:
    raise SystemExit(f'Faltan columnas necesarias: {sorted(faltantes)}')
if len(df) == 0:
    raise SystemExit('El CSV corregido esta vacio; no se reemplaza el original.')

if DESTINO.exists() and not RESPALDO.exists():
    shutil.copy2(DESTINO, RESPALDO)
    print(f'Copia de seguridad: {RESPALDO}')

# Copia el CSV corregido sin alterar sus filas ni inventar datos.
shutil.copy2(origen, DESTINO)
print(f'CSV definitivo: {DESTINO}')
print(f'Anuncios: {len(df)}')
print(f'Superficies nulas: {df["m2"].isna().sum()}')
print(f'Superficies menores de 10 m2: {(df["m2"] < 10).sum()}')
print('El archivo corregido se conserva como respaldo adicional; puedes archivarlo tras verificar el resultado.')
