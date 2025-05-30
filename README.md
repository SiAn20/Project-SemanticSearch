# 🍰 Project-PastrySearch

**PastrySearch** es un buscador semántico desarrollado para facilitar la búsqueda inteligente de postres utilizando una ontología en OWL. Este proyecto combina **Flask**, **HTML**, **CSS**, y la biblioteca **OWLready2** para cargar, consultar y visualizar información estructurada desde una ontología propia, además de contemplar integración con fuentes externas como **DBpedia** y soporte para múltiples idiomas.

## 🧰 Tecnologías utilizadas

- Python 3
- Flask
- OWLready2
- HTML5 y CSS3
- DBpedia (para integración semántica)
- Jinja2 (motor de plantillas de Flask)

## ⚙️ Instalación y ejecución del entorno

1. Clona este repositorio:

```bash
git clone https://github.com/SiAn20/Project-SemanticSearch.git
```

2. Entrar en el proyecto:

```bash
cd Project-SemanticSearch
```

3. Preparar entorno virtul con una version de python compatible, en este caso python 3.11.0,
   si no se tiene instalado instalar de: [python](https://www.python.org/downloads/release/python-3110/)

```bash
py -3.11 -m venv venv
```
activar el entorno virtual:

```bash
source venv/Scripts/activate   #terminal de bash
.\venv\Scripts\Activate        #terminal de powershell
venv\Scripts\activate.bat      #terminal de cmd
```

finalmente, asegurarse de trabajar con la 3.11:

```bash
python --version
```

4. Instala las dependencias con el siguiente comando:

```bash
pip install -r requirements.txt
```

5. ejecutar el comando:

```bash
python app.py
```

6. Abrir la url que aparece en la terminal

## 🚀 Objetivo

El objetivo principal es demostrar cómo se puede aplicar la semántica y la estructuración de conocimiento para mejorar la búsqueda de información en un dominio específico: la repostería.

Se uso el siguiente comando para guardar dependencias:

```bash
pip freeze > requirements.txt
```
