from SPARQLWrapper import SPARQLWrapper, JSON
from utils.text_utils import normalizar_nombre
from deep_translator import GoogleTranslator
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

    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dbo: <http://dbpedia.org/ontology/>

    SELECT DISTINCT ?abstract WHERE {{
      ?s rdfs:label ?label ;
         dbo:abstract ?abstract .
      FILTER (LANG(?label) = "{idioma}")
      FILTER (LANG(?abstract) = "{idioma}")
      FILTER (CONTAINS(LCASE(?label), "{termino.lower()}"))
    }} LIMIT 1
    """
    sparql.setQuery(query)

    try:
        resultados = sparql.query().convert()
        
        if resultados["results"]["bindings"]:
            return resultados["results"]["bindings"][0]["abstract"]["value"]
    except Exception as e:
        print("Error DBpedia:", e)
    return "No results found in DBpedia."


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
    LIMIT 50
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
    try:
        consulta_normalizada = normalizar_nombre(consulta)
        consulta_traducida = normalizar_nombre(
            GoogleTranslator(source=idioma, target='en').translate(consulta)
        )
    except Exception as e:
        print(f"Error al traducir la consulta: {e}")
        consulta_traducida = consulta_normalizada

    with open("data/productos_cake.json", "r", encoding="utf-8") as archivo:
        productos = json.load(archivo)

    for producto in productos:
        nombre_normalizado = normalizar_nombre(producto["nombre"])
        tipo_normalizado = normalizar_nombre(producto["tipo"].split("/")[-1])

        if (
            consulta_normalizada in [nombre_normalizado, tipo_normalizado] or
            consulta_traducida in [nombre_normalizado, tipo_normalizado]
        ):
            if consulta_normalizada in nombre_normalizado or consulta_traducida in nombre_normalizado:
                return {
                    **obtener_info_productos(producto["producto"]),
                    "nombre": producto["nombre"]
                }
            else:
                return obtener_info_productos(producto["tipo"])
    return None