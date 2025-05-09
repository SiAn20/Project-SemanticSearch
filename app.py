from flask import Flask, request, render_template
from ontology_loader import onto  # Importamos la ontología cargada

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
@app.route('/buscar', methods=['POST'])
def buscar():
    palabra = request.form['consulta'].strip().lower()
    
    resultados = {
        "clases": [],
        "subclases": [],
        "propiedades": [],
        "individuos": [],
        "valores": []
    }

    # Buscar en clases
    for clase in onto.classes():
        if palabra in clase.name.lower():
            resultados["clases"].append(clase.name)

        # Buscar en subclases
        for subclase in clase.subclasses():
            if palabra in subclase.name.lower():
                resultados["subclases"].append(subclase.name)

    # Buscar en propiedades
    for prop in onto.properties():
        if palabra in prop.name.lower():
            resultados["propiedades"].append(prop.name)

    # Buscar en individuos (nombres)
    for individuo in onto.individuals():
        if palabra in individuo.name.lower():
            resultados["individuos"].append(individuo.name)

        # Buscar en valores literales de propiedades del individuo
        for prop in individuo.get_properties():
            for val in prop[individuo]:
                if isinstance(val, str) and palabra in val.lower():
                    resultados["valores"].append(f"{individuo.name} → {prop.name} = {val}")

    return render_template('results.html', resultados=resultados)


if __name__ == '__main__':
    app.run(debug=True)
