from flask import Flask, request, render_template, jsonify
from ontology_loader import onto
from SPARQLWrapper import SPARQLWrapper, JSON
from deep_translator import GoogleTranslator
import re
import spacy
import os

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
def traducir_valores(data, idioma_destino):
    """
    Traduce recursivamente strings dentro de dicts y listas
    usando GoogleTranslator desde 'es' a idioma_destino.
    """
    if isinstance(data, str):
        try:
            return GoogleTranslator(source='es', target=idioma_destino).translate(data)
        except Exception as e:
            print(f"Error traduciendo texto: {e}")
            return data
    elif isinstance(data, list):
        return [traducir_valores(item, idioma_destino) for item in data]
    elif isinstance(data, dict):
        return {key: traducir_valores(value, idioma_destino) for key, value in data.items()}
    else:
        return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    consulta_original = request.form['consulta'].strip()
    idioma = request.form.get('idioma', 'en')
     # Si el idioma no es español, traducimos la consulta al español
    if idioma != 'es':
        try:
            consulta_es = GoogleTranslator(source=idioma, target='es').translate(consulta_original)
        except Exception as e:
            return jsonify({"error": f"Error traduciendo la consulta: {str(e)}"})
    else:
        consulta_es = consulta_original

    palabra = normalizar_nombre(consulta_es)

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

   # Si el idioma no es español, traducimos los resultados relevantes a ese idioma
    if idioma != 'es':
        campos_a_traducir = ["descripcion_dbpedia", "valores"]
        for campo in campos_a_traducir:
            if campo in resultados:
                if isinstance(resultados[campo], str):
                    resultados[campo] = GoogleTranslator(source='es', target=idioma).translate(resultados[campo])
                elif isinstance(resultados[campo], list):
                    resultados[campo] = [
                        GoogleTranslator(source='es', target=idioma).translate(texto)
                        for texto in resultados[campo]
                    ]
    # Traducir TODO el resultado solo si el idioma no es español
    if idioma != 'es':
        resultados = traducir_valores(resultados, idioma)


    return jsonify(resultados)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
