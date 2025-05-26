import re
import spacy

nlp = spacy.load("en_core_web_sm")

def normalizar_nombre(nombre):
    nombre = nombre.replace("_", " ")
    nombre = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', nombre)
    return nombre.lower().strip()

def extraer_keywords(frase):
    doc = nlp(frase)
    return [token.lemma_.lower() for token in doc if token.pos_ in ("NOUN", "PROPN", "ADJ")]   