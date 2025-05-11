from flask import Flask, request, render_template, jsonify
from ontology_loader import onto
from SPARQLWrapper import SPARQLWrapper, JSON
import re
import spacy

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

DBPEDIA_ENDPOINTS = {
    "es": "https://es.dbpedia.org/sparql",
    "en": "https://dbpedia.org/sparql",
    "pt": "https://pt.dbpedia.org/sparql",
    "de": "https://de.dbpedia.org/sparql",
    "fr": "https://fr.dbpedia.org/sparql",
}

def normalizar_nombre(nombre):
    nombre = nombre.replace("_", " ")
    nombre = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', nombre)
    return nombre.lower().strip()

def extraer_keywords(frase):
    doc = nlp(frase)
    return [token.lemma_.lower() for token in doc if token.pos_ in ("NOUN", "PROPN", "ADJ")]

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    consulta_original = request.form['consulta'].strip()
    idioma = request.form.get('idioma', 'en')
    palabra = normalizar_nombre(consulta_original)

    resultados = {
        "clases": [],
        "propiedades_clase": {},
        "subclases": [],
        "instancias_clase": {},
        "superclases": {},
        "propiedades_subclase": {},
        "individuos": [],
        "clase_de_instancia": {},
        "propiedades_instancia": {},
        "usado_en_instancias": {},
        "valores": [],
        "descripcion_dbpedia": ""
    }

    encontrado = False

    # Búsqueda local en ontología
    for clase in onto.classes():
        if palabra == normalizar_nombre(clase.name):
            encontrado = True
            resultados["clases"].append(clase.name)
            props = set()
            for instancia in clase.instances():
                for prop in instancia.get_properties():
                    props.add(prop.name)
            resultados["propiedades_clase"][clase.name] = list(props)
            resultados["subclases"].extend([s.name for s in clase.subclasses()])
            resultados["instancias_clase"][clase.name] = [i.name for i in clase.instances()]

        for sub in clase.subclasses():
            if palabra == normalizar_nombre(sub.name):
                encontrado = True
                resultados["subclases"].append(sub.name)
                resultados["superclases"][sub.name] = clase.name
                resultados["propiedades_subclase"][sub.name] = [p.name for p in sub.get_class_properties()]

    for prop in onto.properties():
        if palabra in normalizar_nombre(prop.name):
            encontrado = True
            resultados.setdefault("propiedades", []).append(prop.name)

    for individuo in onto.individuals():
        if palabra == normalizar_nombre(individuo.name):
            encontrado = True
            resultados["individuos"].append(individuo.name)
            clases = [c.name for c in individuo.is_a if hasattr(c, 'name')]
            resultados["clase_de_instancia"][individuo.name] = clases
            props_dict = {}
            for prop in individuo.get_properties():
                valores = prop[individuo]
                props_dict[prop.name] = [str(v) for v in valores]
            resultados["propiedades_instancia"][individuo.name] = props_dict
            for otro in onto.individuals():
                for prop in otro.get_properties():
                    if individuo in prop[otro]:
                        usados = resultados["usado_en_instancias"].setdefault(individuo.name, [])
                        usados.append(f"{otro.name} → {prop.name}")

        for prop in individuo.get_properties():
            for val in prop[individuo]:
                if isinstance(val, str) and normalizar_nombre(val) == palabra:
                    encontrado = True
                    resultados["valores"].append(f"{individuo.name} → {prop.name} = {val}")

    # Si no se encontró, consultar DBpedia
    if not encontrado:
        resultados["descripcion_dbpedia"] = consultar_dbpedia(consulta_original, idioma)

    return jsonify(resultados)

if __name__ == '__main__':
    app.run(debug=True)
