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