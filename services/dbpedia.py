from SPARQLWrapper import SPARQLWrapper, JSON

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

        print(resultados)
        
        if resultados["results"]["bindings"]:
            return resultados["results"]["bindings"][0]["abstract"]["value"]
    except Exception as e:
        print("Error DBpedia:", e)
    return "No results found in DBpedia."


#Esta funcion simplemente es para obtener todos los productos que estan en
def obtener_productos_tipo_cake():
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
    LIMIT 1000
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

        return productos

    except Exception as e:
        print("Error al consultar productos tipo cake:", e)
        return []
