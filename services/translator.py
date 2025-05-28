from deep_translator import GoogleTranslator
import re

def normalizar_nombre(nombre):
    nombre = nombre.replace("_", " ")
    nombre = re.sub(r'(\w):(\w)', r'\1 : \2', nombre)
    nombre = re.sub(r'(\w):', r'\1 :', nombre)
    nombre = re.sub(r':(\w)', r': \1', nombre)  
    nombre = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', nombre)
    return nombre.lower().strip()

def traducir_valores(data, idioma_destino):
    """
    Traduce recursivamente strings dentro de dicts y listas
    usando GoogleTranslator desde 'es' a idioma_destino.
    """
    if isinstance(data, str):
        try:
            texto_limpio = normalizar_nombre(data)
            return GoogleTranslator(source='es', target=idioma_destino).translate(texto_limpio)
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
    
def traducir_valores_ontologia(resultados, idioma_destino):
    """
    Traduce específicamente los elementos de la ontología manteniendo la estructura
    """
    if idioma_destino == 'es':
        return resultados

    def traducir_nombre_ontologico(nombre):
        """Traduce nombres de la ontología preservando ciertas convenciones"""
        try:
            # Primero normalizamos el nombre para traducción
            nombre_limpio = normalizar_nombre(nombre)
            
            # Traducimos el nombre completo
            traducido = GoogleTranslator(source='es', target=idioma_destino).translate(nombre_limpio)
            
            print(traducido)
            
            # Si el original tenía guiones bajos, los mantenemos
            if '_' in nombre:
                traducido = traducido.replace(' ', '_')
            
            # Mantenemos la capitalización similar al original
            if nombre == nombre.title():
                traducido = traducido.title()
            elif nombre == nombre.upper():
                traducido = traducido.upper()
                
            return traducido
        except Exception as e:
            print(f"Error traduciendo nombre ontológico {nombre}: {e}")
            return nombre

    # 1. Primero aplicamos la traducción genérica para valores simples
    resultados = traducir_valores(resultados, idioma_destino)
    
    # 2. Luego aplicamos traducción especializada para nombres de ontología
    
    # Traducción de clases
    if 'clases' in resultados:
        resultados['clases'] = [traducir_nombre_ontologico(clase) for clase in resultados['clases']]
    
    # Traducción de propiedades de clase
    if 'propiedades_clase' in resultados:
        nuevas_prop_clase = {}
        for clase, props in resultados['propiedades_clase'].items():
            nuevas_prop_clase[traducir_nombre_ontologico(clase)] = [traducir_nombre_ontologico(prop) for prop in props]
        resultados['propiedades_clase'] = nuevas_prop_clase
    
    # Traducción de subclases
    if 'subclases' in resultados:
        resultados['subclases'] = [traducir_nombre_ontologico(sub) for sub in resultados['subclases']]
    
    # Traducción de instancias de clase
    if 'instancias_clase' in resultados:
        nuevas_instancias = {}
        for clase, instancias in resultados['instancias_clase'].items():
            nuevas_instancias[traducir_nombre_ontologico(clase)] = [traducir_nombre_ontologico(inst) for inst in instancias]
        resultados['instancias_clase'] = nuevas_instancias
    
    # Traducción de superclases de subclases
    if 'superclases' in resultados:
        nuevas_superclases = {}
        for subclase, superclase in resultados['superclases'].items():
            nuevas_superclases[traducir_nombre_ontologico(subclase)] = traducir_nombre_ontologico(superclase)
        resultados['superclases'] = nuevas_superclases
        
        # Añadir etiqueta traducida para la sección
        resultados['etiqueta_superclases'] = GoogleTranslator(source='es', target=idioma_destino).translate("Superclases de subclases")
    
    # Traducción de propiedades de subclase
    if 'propiedades_subclase' in resultados:
        nuevas_prop_subclase = {}
        for subclase, props in resultados['propiedades_subclase'].items():
            nuevas_prop_subclase[traducir_nombre_ontologico(subclase)] = [traducir_nombre_ontologico(prop) for prop in props]
        resultados['propiedades_subclase'] = nuevas_prop_subclase
        
        # Añadir etiqueta traducida para la sección
        resultados['etiqueta_propiedades_subclase'] = GoogleTranslator(source='es', target=idioma_destino).translate("Propiedades de subclase")
    
    # Traducción de individuos
    if 'individuos' in resultados:
        resultados['individuos'] = [traducir_nombre_ontologico(ind) for ind in resultados['individuos']]
    
    # Traducción de clase de instancia
    if 'clase_de_instancia' in resultados:
        nuevas_clase_inst = {}
        for instancia, clases in resultados['clase_de_instancia'].items():
            nuevas_clase_inst[traducir_nombre_ontologico(instancia)] = [traducir_nombre_ontologico(clase) for clase in clases]
        resultados['clase_de_instancia'] = nuevas_clase_inst
    
    # Traducción de propiedades de instancia
    if 'propiedades_instancia' in resultados:
        nuevas_prop_inst = {}
        for instancia, props in resultados['propiedades_instancia'].items():
            nuevas_props = {}
            for prop, valores in props.items():
                nuevas_props[traducir_nombre_ontologico(prop)] = [traducir_nombre_ontologico(v) if isinstance(v, str) else v for v in valores]
            nuevas_prop_inst[traducir_nombre_ontologico(instancia)] = nuevas_props
        resultados['propiedades_instancia'] = nuevas_prop_inst
    
    # Traducción de usado en instancias
    if 'usado_en_instancias' in resultados:
        nuevas_usos = {}
        for instancia, usos in resultados['usado_en_instancias'].items():
            nuevos_usos = []
            for uso in usos:
                partes = uso.split(' → ')
                if len(partes) == 2:
                    nuevos_usos.append(f"{traducir_nombre_ontologico(partes[0])} → {traducir_nombre_ontologico(partes[1])}")
                else:
                    nuevos_usos.append(uso)
            nuevas_usos[traducir_nombre_ontologico(instancia)] = nuevos_usos
        resultados['usado_en_instancias'] = nuevas_usos
    
    # Traducción de valores
    if 'valores' in resultados:
        nuevos_valores = []
        for valor in resultados['valores']:
            partes = valor.split(' → ')
            if len(partes) == 2:
                prop_valor = partes[1].split(' = ')
                if len(prop_valor) == 2:
                    nuevos_valores.append(
                        f"{traducir_nombre_ontologico(partes[0])} → {traducir_nombre_ontologico(prop_valor[0])} = {traducir_nombre_ontologico(prop_valor[1])}"
                    )
                else:
                    nuevos_valores.append(valor)
            else:
                nuevos_valores.append(valor)
        resultados['valores'] = nuevos_valores
    
    # Traducción de propiedades simples
    if 'propiedades' in resultados:
        resultados['propiedades'] = [traducir_nombre_ontologico(prop) for prop in resultados['propiedades']]
    
    return resultados