import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()
client = None
try:
    uri = os.getenv('MONGODB_URI')
    database_name = os.getenv('DATABASE_NAME')
    if not uri or not database_name:
        raise ValueError('Faltan MONGODB_URI o DATABASE_NAME en .env')
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[database_name]
    faltantes = {'municipios', 'anuncios'} - set(db.list_collection_names())
    if faltantes:
        raise ValueError(f'Faltan colecciones: {", ".join(sorted(faltantes))}')

    pipeline = [
        {'$match': {
            'indicadores.eustat_alquiler_medio_2024': {'$type': 'number', '$gt': 0},
            'indicadores.salario_neto_mensual': {'$type': 'number', '$gt': 0},
            'indicadores.esfuerzo_alquiler_pct': {'$type': 'number'}
        }},
        {'$lookup': {
            'from': 'anuncios',
            'let': {'codigo_municipio': '$_id'},
            'pipeline': [
                {'$match': {'$expr': {'$and': [
                    {'$eq': ['$municipio_id', '$$codigo_municipio']},
                    {'$eq': ['$operacion', 'venta']},
                    {'$gt': ['$precio', 0]},
                    {'$in': [{'$type': '$precio'}, ['int', 'long', 'double', 'decimal']]},
                    {'$ne': ['$calidad.precio_no_valido', True]},
                    {'$ne': ['$calidad.posible_duplicado', True]},
                    {'$ne': ['$calidad.posible_duplicado_ampliado', True]}
                ]}}},
                {'$group': {
                    '_id': None,
                    'num_anuncios': {'$sum': 1},
                    'precio_medio_oferta': {'$avg': '$precio'}
                }}
            ],
            'as': 'resumen_venta'
        }},
        {'$unwind': '$resumen_venta'},
        {'$addFields': {
            'anos_salario_compra_oferta': {
                '$divide': [
                    '$resumen_venta.precio_medio_oferta',
                    {'$multiply': ['$indicadores.salario_neto_mensual', 12]}
                ]
            }
        }},
        {'$project': {
            '_id': 0, 'municipio': '$nombre', 'provincia': 1,
            'alquiler_mensual_2024': '$indicadores.eustat_alquiler_medio_2024',
            'salario_neto_mensual': '$indicadores.salario_neto_mensual',
            'esfuerzo_alquiler_pct': '$indicadores.esfuerzo_alquiler_pct',
            'anuncios_venta': '$resumen_venta.num_anuncios',
            'precio_medio_oferta_venta': {'$round': ['$resumen_venta.precio_medio_oferta', 2]},
            'anos_salario_compra_oferta': {'$round': ['$anos_salario_compra_oferta', 2]}
        }},
        {'$sort': {'esfuerzo_alquiler_pct': -1}}
    ]
    resultados = list(db.municipios.aggregate(pipeline))
    print('\n=== ALQUILER Y OFERTA DE COMPRAVENTA POR MUNICIPIO ===\n')
    if not resultados:
        print('No hay municipios con alquiler y anuncios de venta válidos.')
    for r in resultados:
        print(f"{r['municipio']} ({r['provincia']})")
        print(f"  Alquiler medio 2024: {r['alquiler_mensual_2024']:,.2f} €/mes")
        print(f"  Salario de referencia: {r['salario_neto_mensual']:,.2f} €/mes")
        print(f"  Esfuerzo alquiler: {r['esfuerzo_alquiler_pct']:.2f} %")
        print(f"  Anuncios venta: {r['anuncios_venta']}")
        print(f"  Precio medio de oferta: {r['precio_medio_oferta_venta']:,.2f} €")
        print(f"  Años de salario neto para compra (teórico): {r['anos_salario_compra_oferta']:.2f}")
        print('-' * 65)
    print(f'Municipios comparados: {len(resultados)}')
    print('NOTA: Alquiler Eustat 2024 vs anuncios de venta de la muestra de 2026.')
    print('Los años de salario son teóricos: no incluyen gastos, impuestos ni financiación.')
except (PyMongoError, ValueError, KeyError, TypeError) as error:
    print(f'ERROR: {error}')
finally:
    if client is not None:
        client.close()
