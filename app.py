from flask import Flask, request, render_template, jsonify
from services.ontology_loader import onto
from services.dbpedia import consultar_dbpedia, consultar_datos_poblados
from services.translator import traducir_ingredientes, traducir_texto, traducir_consulta_si_necesario, traducir_valores_ontologia
from utils.text_utils import normalizar_nombre
import os

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    """Método principal de búsqueda"""
    consulta_original = request.form['consulta'].strip()
    idioma = request.form.get('idioma', 'en')

    # Traducir consulta si es necesario
    consulta_es = traducir_consulta_si_necesario(consulta_original, idioma)
    
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
            # Procesar resultados de DBpedia
            _procesar_resultados_dbpedia(resultadosDbpedia, idioma, resultados)

        if(resultados["descripcion_dbpedia"] == ''):
            resultados["descripcion_dbpedia"] = consultar_dbpedia(consulta_original, idioma)
        

    if idioma != 'es':
        try:
            resultados = traducir_valores_ontologia(resultados, idioma)
        except Exception as e:
            print(f"Error al traducir resultados: {e}")
        
    return jsonify(resultados)


def _procesar_resultados_dbpedia(resultadosDbpedia, idioma, resultados):
    """Procesa y traduce resultados de DBpedia"""
    # Traducir descripción
    abstract = resultadosDbpedia.get("abstract", "")
    if abstract:
        resultados["descripcion_dbpedia"] = traducir_texto(abstract, 'en', idioma)

    # Campos que no necesitan traducción
    resultados["pais"] = resultadosDbpedia.get("country", "")
    resultados["thumbnail"] = resultadosDbpedia.get("thumbnail", "")
    resultados["nombre"] = resultadosDbpedia.get("nombre", "")

    # Procesar y traducir ingredientes
    ingredientes = resultadosDbpedia.get("ingredientNames", [])
    ingredientes_list = _procesar_lista_ingredientes(ingredientes)
    resultados["ingredientes"] = traducir_ingredientes(ingredientes_list, idioma)

def _procesar_lista_ingredientes(ingredientes):
    """Procesa la lista de ingredientes normalizando el formato"""
    ingredientes_list = []
    if isinstance(ingredientes, list):
        if len(ingredientes) == 1 and isinstance(ingredientes[0], str):
            ingredientes_list = [i.strip() for i in ingredientes[0].split(",")]
        else:
            ingredientes_list = [i.strip() for i in ingredientes]
    return ingredientes_list



if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)