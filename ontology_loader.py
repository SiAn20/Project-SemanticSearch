from owlready2 import *

# Ruta a tu archivo OWL
onto_path.append(".")  # Ej. "ontologias/"
onto = get_ontology("PastryOntology.rdf").load()

