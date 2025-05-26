from flask import Flask, request, render_template, jsonify
from services.ontology_loader import onto
from services.dbpedia import consultar_dbpedia, obtener_info_productos
from services.translator import traducir_valores
from deep_translator import GoogleTranslator
import re
import spacy
import os
import json

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

def normalizar_nombre(nombre):
    nombre = nombre.replace("_", " ")
    nombre = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', nombre)
    return nombre.lower().strip()

def extraer_keywords(frase):
    doc = nlp(frase)
    return [token.lemma_.lower() for token in doc if token.pos_ in ("NOUN", "PROPN", "ADJ")]

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

    

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    consulta_original = request.form['consulta'].strip()
    idioma = request.form.get('idioma', 'en')

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

    # Si no se encontró localmente, buscar en DBpedia
    if not encontrado:
        resultadosDbpedia = consultar_datos_poblados(consulta_original, idioma)
        if resultadosDbpedia and isinstance(resultadosDbpedia, dict):
            resultados["descripcion_dbpedia"] = GoogleTranslator(source='auto', target=idioma).translate(resultadosDbpedia.get("abstract", ""))
            resultados["pais"] = resultadosDbpedia.get("country", "")

            ingredientes = resultadosDbpedia.get("ingredientNames", [])
            ingredientes_list = []
            if isinstance(ingredientes, list):
                if len(ingredientes) == 1 and isinstance(ingredientes[0], str):
                    ingredientes_list = [i.strip() for i in ingredientes[0].split(",")]
                else:
                    ingredientes_list = [i.strip() for i in ingredientes]

            if idioma != "en":
                try:
                    ingredientes_traducidos = [
                        GoogleTranslator(source='en', target=idioma).translate(i)
                        for i in ingredientes_list
                    ]
                    resultados["ingredientes"] = ingredientes_traducidos
                except Exception as e:
                    resultados["ingredientes"] = ingredientes_list
            else:
                resultados["ingredientes"] = ingredientes_list

            resultados["thumbnail"] = resultadosDbpedia.get("thumbnail", "")
            resultados["nombre"] = resultadosDbpedia.get("nombre", "")

        if(resultados["descripcion_dbpedia"] == ''):
            resultados["descripcion_dbpedia"] = consultar_dbpedia(consulta_original, idioma)
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

    resultados = traducir_valores(resultados, idioma)
        
    return jsonify(resultados)



if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
