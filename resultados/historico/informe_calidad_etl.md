# Informe de calidad del ETL

## Proyecto EUSKADI_VIVIENDA_BIGDATA

Fecha de generacion: 2026-11-04

## 1. Objetivo

Integrar datos oficiales, datos obtenidos mediante API y anuncios inmobiliarios para analizar la accesibilidad a la vivienda de la poblacion joven en Euskadi.

## 2. Fuentes y datasets procesados

| dataset               | archivo                                       |   filas |   columnas |   celdas_nulas |   filas_duplicadas |
|:----------------------|:----------------------------------------------|--------:|-----------:|---------------:|-------------------:|
| Catalogo municipios   | catalogo_municipios_euskadi_2026.csv          |     252 |          3 |              0 |                  0 |
| Vivienda oficial      | vivienda_euskadi_municipios_integrado.csv     |     252 |         22 |           2412 |                  0 |
| Anuncios clasificados | compraventa_euskadi_clasificado_v3.csv        |    2952 |         29 |           3187 |                  0 |
| Salarios juveniles    | salarios_juveniles_euskadi.csv                |     120 |          4 |              0 |                  0 |
| Alquiler API          | alquiler_euskadi_provincias.csv               |      33 |          5 |              7 |                  0 |
| Economia juvenil      | economia_juvenil_euskadi.csv                  |     148 |          5 |              0 |                  0 |
| Esfuerzo alquiler     | esfuerzo_alquiler_juvenil_municipios_2024.csv |     252 |          7 |            279 |                  0 |
| Accesibilidad compra  | accesibilidad_compra_juvenil_municipios.csv   |     252 |          8 |            938 |                  0 |
| Indicadores finales   | indicadores_vivienda_juvenil_euskadi.csv      |     252 |         16 |           1217 |                  0 |

## 3. Validaciones por dataset

### Catalogo municipios

- Archivo: `catalogo_municipios_euskadi_2026.csv`
- Registros: 252
- Columnas: 3
- Celdas nulas: 0
- Filas completamente duplicadas: 0
- Codigos INE unicos: 252


### Vivienda oficial

- Archivo: `vivienda_euskadi_municipios_integrado.csv`
- Registros: 252
- Columnas: 22
- Celdas nulas: 2412
- Filas completamente duplicadas: 0
- Codigos INE unicos: 252


### Anuncios clasificados

- Archivo: `compraventa_euskadi_clasificado_v3.csv`
- Registros: 2952
- Columnas: 29
- Celdas nulas: 3187
- Filas completamente duplicadas: 0
- IDs de anuncio unicos: 2952


### Salarios juveniles

- Archivo: `salarios_juveniles_euskadi.csv`
- Registros: 120
- Columnas: 4
- Celdas nulas: 0
- Filas completamente duplicadas: 0


### Alquiler API

- Archivo: `alquiler_euskadi_provincias.csv`
- Registros: 33
- Columnas: 5
- Celdas nulas: 7
- Filas completamente duplicadas: 0


### Economia juvenil

- Archivo: `economia_juvenil_euskadi.csv`
- Registros: 148
- Columnas: 5
- Celdas nulas: 0
- Filas completamente duplicadas: 0


### Esfuerzo alquiler

- Archivo: `esfuerzo_alquiler_juvenil_municipios_2024.csv`
- Registros: 252
- Columnas: 7
- Celdas nulas: 279
- Filas completamente duplicadas: 0
- Codigos INE unicos: 252


### Accesibilidad compra

- Archivo: `accesibilidad_compra_juvenil_municipios.csv`
- Registros: 252
- Columnas: 8
- Celdas nulas: 938
- Filas completamente duplicadas: 0
- Codigos INE unicos: 252


### Indicadores finales

- Archivo: `indicadores_vivienda_juvenil_euskadi.csv`
- Registros: 252
- Columnas: 16
- Celdas nulas: 1217
- Filas completamente duplicadas: 0
- Codigos INE unicos: 252


## 4. Transformaciones principales

- Normalizacion de municipios y codigos INE.
- Integracion de fuentes oficiales de alquiler y compraventa.
- Limpieza y clasificacion de anuncios inmobiliarios.
- Deduplicacion de anuncios mediante identificador.
- Conservacion de registros pendientes de revision.
- Integracion de salarios juveniles por territorio.
- Calculo del esfuerzo economico de alquiler.
- Calculo de anos de salario equivalentes al precio de compra.
- Integracion final de indicadores municipales.

## 5. Limitaciones metodologicas

- No todos los municipios tienen precios oficiales publicados.
- Los anuncios representan precios de oferta, no ventas cerradas.
- Los salarios territoriales no representan salarios municipales.
- El alquiler de referencia corresponde a 2024.
- Los precios de compraventa corresponden a 2025.
- Existen anuncios pendientes de revision manual.
- Las fuentes INE y Registradores se mantienen separadas.

## 6. Interpretacion de valores nulos

Los valores ausentes se conservan como nulos. No se sustituyen por cero ni por medias municipales sin una justificacion metodologica.
