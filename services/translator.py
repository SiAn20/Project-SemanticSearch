from deep_translator import GoogleTranslator

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
    

def traducir_ingredientes(ingredientes_list, idioma):
    """Traduce lista de ingredientes del inglés al idioma especificado"""
    if idioma == "en" or not ingredientes_list:
        return ingredientes_list
    
    try:
        return [
            GoogleTranslator(source='en', target=idioma).translate(ingrediente)
            for ingrediente in ingredientes_list
        ]
    except Exception as e:
        print(f"Error traduciendo ingredientes: {e}")
        return ingredientes_list

def traducir_texto(texto, idioma_origen, idioma_destino):
    """Traduce un texto individual con manejo de errores"""
    if not texto or idioma_origen == idioma_destino:
        return texto
    
    try:
        return GoogleTranslator(source=idioma_origen, target=idioma_destino).translate(texto)
    except Exception as e:
        print(f"Error traduciendo texto: {e}")
        return texto

def traducir_campos_resultados(resultados, idioma):
    """Traduce campos específicos de los resultados del español al idioma destino"""
    if idioma == 'es':
        return
    
    campos_a_traducir = ["descripcion_dbpedia", "valores"]
    
    for campo in campos_a_traducir:
        if campo in resultados and resultados[campo]:
            if isinstance(resultados[campo], str):
                resultados[campo] = traducir_texto(resultados[campo], 'es', idioma)
            elif isinstance(resultados[campo], list):
                resultados[campo] = [
                    traducir_texto(texto, 'es', idioma)
                    for texto in resultados[campo]
                ]
    
def traducir_consulta_si_necesario(consulta_original, idioma):
    """Traduce la consulta al español si no está en español"""
    if idioma != 'es':
        try:
            return GoogleTranslator(source=idioma, target='es').translate(consulta_original)
        except Exception as e:
            raise Exception(f"Error traduciendo la consulta: {str(e)}")
    else:
        return consulta_original