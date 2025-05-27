import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from utils.text_utils import normalizar_nombre
import json

DBPEDIA_ENDPOINTS = {
    "es": "https://es.dbpedia.org/sparql",
    "en": "https://dbpedia.org/sparql",
    "pt": "https://pt.dbpedia.org/sparql",
    "de": "https://de.dbpedia.org/sparql",
    "fr": "https://fr.dbpedia.org/sparql",
}

def consultar_dbpedia(termino, idioma):
    endpoint = DBPEDIA_ENDPOINTS.get(idioma, DBPEDIA_ENDPOINTS["en"])
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat(JSON)
    termino_limpio = termino.strip().lower()

    def obtener_recurso(filtro):
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?s WHERE {{
          ?s rdfs:label ?label .
          FILTER (LANG(?label) = "{idioma}")
          FILTER ({filtro})
        }} LIMIT 2
        """
        sparql.setQuery(query)
        try:
            resultados = sparql.query().convert()
            if resultados["results"]["bindings"]:
                return resultados["results"]["bindings"][0]["s"]["value"]
        except Exception as e:
            print("⚠️ Error al obtener recurso DBpedia:", e)
        return None

    def obtener_abstract(recurso):
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT ?abstract WHERE {{
          <{recurso}> dbo:abstract ?abstract .
          FILTER (LANG(?abstract) = "{idioma}")
        }} LIMIT 2
        """
        sparql.setQuery(query)
        try:
            resultados = sparql.query().convert()
            if resultados["results"]["bindings"]:
                abstract = resultados["results"]["bindings"][0]["abstract"]["value"]
                return f"{abstract}\n\n🔗 Más información: {recurso}"
        except Exception as e:
            print("⚠️ Error al obtener abstract DBpedia:", e)
        return None
    def usar_lookup_api(termino):
        try:
            url = "https://lookup.dbpedia.org/api/search/KeywordSearch"
            headers = {"Accept": "application/json"}
            params = {"QueryString": termino, "MaxHits": 1}
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    res = data["results"][0]
                    desc = res.get("description", "")
                    uri = res.get("uri", "")
                    return f"{desc}\n\n🔗 Más información: {uri}"
        except Exception as e:
            print("⚠️ Error al usar Lookup API:", e)
        return "No se encontraron resultados en DBpedia (incluyendo búsqueda rápida)."
    
    # Paso 1: intentar con STRSTARTS
    filtro_1 = f'STRSTARTS(LCASE(STR(?label)), "{termino_limpio}")'
    recurso = obtener_recurso(filtro_1)

    # Paso 2: si falla, intentar con CONTAINS
    if not recurso:
        filtro_2 = f'CONTAINS(LCASE(STR(?label)), "{termino_limpio}")'
        recurso = obtener_recurso(filtro_2)

    # Paso 3: si hay recurso, buscar su abstract
    if recurso:
        resultado = obtener_abstract(recurso)
        if resultado:
            return resultado
        else:
            return f"No se encontró descripción para el recurso: {recurso}"
    
    # Paso 4: Fallback a Lookup API
    return usar_lookup_api(termino)

    return "No se encontraron resultados en DBpedia."



def obtener_productos():
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)

    query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?producto ?nombre ?sabor ?tipo ?lang WHERE {
      ?producto rdf:type dbo:Food ;
                rdfs:label ?nombre ;
                dbo:type ?tipo .
      OPTIONAL { ?producto dbp:flavor ?sabor . }
      BIND (lang(?nombre) AS ?lang)
      FILTER (?lang = "en" || ?lang = "es")
      FILTER CONTAINS(LCASE(STR(?tipo)), "cake")
    }
    LIMIT 2
    """

    sparql.setQuery(query)

    try:
        resultados = sparql.query().convert()
        productos = []
        for r in resultados["results"]["bindings"]:
            productos.append({
                "producto": r["producto"]["value"],
                "nombre": r["nombre"]["value"],
                "sabor": r.get("sabor", {}).get("value", "N/A"),
                "tipo": r["tipo"]["value"],
                "idioma": r["lang"]["value"]
            })
        with open("data/productos_cake.json", "w", encoding="utf-8") as f:
            json.dump(productos, f, ensure_ascii=False, indent=4)

        return productos
    except Exception as e:
        print("Error al consultar productos tipo cake:", e)
        return []

obtener_productos()

def obtener_info_productos(resource_url):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    resource = f"<{resource_url}>"

    query = f"""
    SELECT ?abstract ?country ?ingredient ?ingredientName ?thumbnail WHERE {{
        {resource} dbo:abstract ?abstract .
        OPTIONAL {{ {resource} dbo:country ?country . }}
        OPTIONAL {{ {resource} dbo:ingredient ?ingredient . }}
        OPTIONAL {{ {resource} dbo:ingredientName ?ingredientName . }}
        OPTIONAL {{ {resource} dbo:thumbnail ?thumbnail . }}
        FILTER (lang(?abstract) = 'en')
    }}
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    data = {
        "abstract": None,
        "country": None,
        "ingredients": set(),
        "ingredientNames": set(),
        "thumbnail": None
    }

    for result in results["results"]["bindings"]:
        if "abstract" in result:
            data["abstract"] = result["abstract"]["value"]
        if "country" in result:
            data["country"] = result["country"]["value"]
        if "ingredient" in result:
            data["ingredients"].add(result["ingredient"]["value"])
        if "ingredientName" in result:
            data["ingredientNames"].add(result["ingredientName"]["value"])
        if "thumbnail" in result:
            data["thumbnail"] = result["thumbnail"]["value"]

    # Convert sets to lists for easier JSON serialization if needed
    data["ingredients"] = list(data["ingredients"])
    data["ingredientNames"] = list(data["ingredientNames"])

    return data

def consultar_datos_poblados(consulta, idioma):
    from deep_translator import GoogleTranslator

    with open("data/productos_cake.json", "r", encoding="utf-8") as archivo:
        productos = json.load(archivo)

    for producto in productos:
        nombre_normalizado = normalizar_nombre(producto["nombre"])
        tipo_normalizado = normalizar_nombre(producto["tipo"].split("/")[-1])
        consulta_normalizada = normalizar_nombre(consulta)

        nombre_traducido = normalizar_nombre(GoogleTranslator(source=idioma, target='en').translate(producto["nombre"]))
        tipo_traducido = normalizar_nombre(GoogleTranslator(source=idioma, target='en').translate(producto["tipo"].split("/")[-1]))

        if consulta_normalizada == nombre_normalizado or consulta_normalizada == nombre_traducido:
             return {**obtener_info_productos(producto["producto"]), "nombre": producto['nombre']}

        if consulta_normalizada == tipo_normalizado or consulta_normalizada == tipo_traducido:
            return obtener_info_productos(producto["tipo"])