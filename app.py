from flask import Flask, request, render_template, jsonify
from ontology_loader import onto
import re

app = Flask(__name__)

def normalizar_nombre(nombre):
    nombre = nombre.replace("_", " ")
    nombre = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', nombre)
    return nombre.lower().strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])

def buscar():
    palabra = normalizar_nombre(request.form['consulta'].strip())

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
        "valores": []
    }

    # --- CLASES Y SUBCLASES ---
    for clase in onto.classes():
        # Si la palabra coincide con una clase
        if palabra == normalizar_nombre(clase.name):
            resultados["clases"].append(clase.name)

            # Propiedades de la clase
            props = set()
            for instancia in clase.instances():
                for prop in instancia.get_properties():
                    props.add(prop.name)
            resultados["propiedades_clase"][clase.name] = list(props)

            # Subclases
            subclases = list(clase.subclasses())
            for sub in subclases:
                resultados["subclases"].append(sub.name)

            # Instancias de la clase
            instancias = [inst.name for inst in clase.instances()]
            resultados["instancias_clase"][clase.name] = instancias

        # Si la palabra coincide con una subclase
        for sub in clase.subclasses():
            if palabra == normalizar_nombre(sub.name):
                resultados["subclases"].append(sub.name)
                resultados["superclases"][sub.name] = clase.name

                props = [p.name for p in sub.get_class_properties()]
                resultados["propiedades_subclase"][sub.name] = props

    # --- PROPIEDADES --- (opcional: seguir mostrando si coinciden con nombre)
    for prop in onto.properties():
        if palabra in normalizar_nombre(prop.name):
            resultados.setdefault("propiedades", []).append(prop.name)

    # --- INDIVIDUOS E INSTANCIAS ---
    for individuo in onto.individuals():
        if palabra == normalizar_nombre(individuo.name):
            resultados["individuos"].append(individuo.name)

            # A qué clase pertenece
            clases = [c.name for c in individuo.is_a if hasattr(c, 'name')]
            resultados["clase_de_instancia"][individuo.name] = clases

            # Propiedades y valores del individuo
            props_dict = {}
            for prop in individuo.get_properties():
                valores = prop[individuo]
                props_dict[prop.name] = [str(v) for v in valores]
            resultados["propiedades_instancia"][individuo.name] = props_dict

            # Buscar si este individuo es usado como valor en otras instancias
            for otro in onto.individuals():
                for prop in otro.get_properties():
                    if individuo in prop[otro]:
                        usados = resultados["usado_en_instancias"].setdefault(individuo.name, [])
                        usados.append(f"{otro.name} → {prop.name}")

        # Búsqueda por valores literales
        for prop in individuo.get_properties():
            for val in prop[individuo]:
                if isinstance(val, str) and normalizar_nombre(val) == palabra:
                    resultados["valores"].append(f"{individuo.name} → {prop.name} = {normalizar_nombre(val)}")

    return jsonify(resultados)

if __name__ == '__main__':
    app.run(debug=True)
 