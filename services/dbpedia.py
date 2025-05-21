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
        if resultados["results"]["bindings"]:
            return resultados["results"]["bindings"][0]["abstract"]["value"]
    except Exception as e:
        print("Error DBpedia:", e)
    return "No results found in DBpedia."