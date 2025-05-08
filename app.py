from flask import Flask, request, render_template
from ontology_loader import onto  # Importamos la ontología cargada

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    palabra = request.form['consulta'].strip().lower()
    resultados = []

    for instancia in onto.individuals():
        if palabra in instancia.name.lower():
            resultados.append(instancia.name)

    return render_template('results.html', resultados=resultados)

if __name__ == '__main__':
    app.run(debug=True)
