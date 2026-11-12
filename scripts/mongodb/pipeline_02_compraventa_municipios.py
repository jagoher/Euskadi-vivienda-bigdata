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
    necesarias = {'anuncios', 'municipios'}
    faltantes = necesarias - set(db.list_collection_names())
    if faltantes:
        raise ValueError(f'Faltan colecciones: {", ".join(sorted(faltantes))}')

    pipeline = [
        {'$match': {
            'operacion': 'venta',
            'precio': {'$type': 'number', '$gt': 0},
            'municipio_id': {'$type': 'string'},
            'calidad.precio_no_valido': {'$ne': True},
            'calidad.posible_duplicado': {'$ne': True},
            'calidad.posible_duplicado_ampliado': {'$ne': True}
        }},
        {'$group': {
            '_id': '$municipio_id',
            'anuncios': {'$sum': 1},
            'precio_medio': {'$avg': '$precio'},
            'precio_minimo': {'$min': '$precio'},
            'precio_maximo': {'$max': '$precio'}
        }},
        {'$lookup': {
            'from': 'municipios', 'localField': '_id',
            'foreignField': '_id', 'as': 'datos_municipio'
        }},
        {'$unwind': '$datos_municipio'},
        {'$project': {
            '_id': 0,
            'municipio': '$datos_municipio.nombre',
            'provincia': '$datos_municipio.provincia',
            'anuncios': 1,
            'precio_medio': {'$round': ['$precio_medio', 2]},
            'precio_minimo': 1, 'precio_maximo': 1
        }},
        {'$sort': {'precio_medio': -1}}
    ]
    resultados = list(db.anuncios.aggregate(pipeline))
    print('\n=== PRECIOS DE OFERTA DE COMPRAVENTA POR MUNICIPIO ===\n')
    if not resultados:
        print('No se encontraron anuncios válidos.')
    for r in resultados:
        print(f"{r['municipio']} ({r['provincia']})")
        print(f"  Anuncios: {r['anuncios']}")
        print(f"  Precio medio de oferta: {r['precio_medio']:,.2f} €")
        print(f"  Mínimo: {r['precio_minimo']:,.2f} € | Máximo: {r['precio_maximo']:,.2f} €")
        print('-' * 60)
    print(f'Municipios analizados: {len(resultados)}')
    print(f"Anuncios analizados: {sum(r['anuncios'] for r in resultados)}")
    print('NOTA: Son precios anunciados, no precios de operaciones cerradas.')
except (PyMongoError, ValueError, KeyError, TypeError) as error:
    print(f'ERROR: {error}')
finally:
    if client is not None:
        client.close()
