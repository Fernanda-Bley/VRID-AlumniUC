"""
Mapeos oficiales de Clasificación Decimal Dewey (DDC) y Objetivos de Desarrollo Sostenible (ODS).
Ubicación: src/normalize_categories/dewey_mapping.py
"""

# Reemplazos específicos de Mojibake para campos de categorías y Dewey
CATEGORY_MOJIBAKE = {
    "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
    "Ã±": "ñ", "Ã¼": "ü", "Ã€": "À", "Ã‰": "É", "Ã‘": "Ñ",
    "Â¿": "¿", "Â¡": "¡", "Â«": "«", "Â»": "»", "Â": "",
    "â€™": "’", "â€œ": "“", "â€ ": "”", "â€“": "–", "â€”": "—",
    "â€¦": "…", "â†’": "→", "âˆš": "√",
    "√°": "á", "√©": "é", "√≠": "í", "√≥": "ó", "√∫": "ú", "√±": "ñ",
    "": "",  # Carácter de reemplazo desconocido en codificación corrupta
}

# Mapeo oficial de Códigos Dewey (Centenas y subclasificaciones principales SIPA) a Español
DEWEY_CODE_TO_SPANISH = {
    "0": "Ciencias de la computación",
    "000": "Ciencias de la computación",
    "10": "Ciencias de la información",
    "010": "Ciencias de la información",
    "70": "Periodismo",
    "070": "Periodismo",
    "100": "Filosofía",
    "150": "Psicología",
    "170": "Ética",
    "200": "Religión",
    "233": "Religión",
    "300": "Ciencias sociales",
    "320": "Ciencias políticas",
    "330": "Economía",
    "338": "Economía",
    "340": "Derecho",
    "350": "Administración pública",
    "370": "Educación",
    "380": "Comunicación y transporte",
    "400": "Lenguas",
    "500": "Ciencias",
    "510": "Matemáticas, física y química",
    "515": "Matemáticas, física y química",
    "516": "Matemáticas, física y química",
    "520": "Astronomía",
    "550": "Ciencias de la tierra",
    "570": "Biología",
    "600": "Tecnología",
    "610": "Medicina y salud",
    "620": "Ingeniería",
    "650": "Administración",
    "700": "Arte",
    "710": "Arquitectura",
    "711": "Arquitectura",
    "790": "Recreación",
    "800": "Literatura",
    "900": "Historia y geografía",
}

# Traducción y estandarización oficial de ODS de Inglés a Español
ODS_ENGLISH_TO_SPANISH = {
    "01 No poverty": "01 Fin de la pobreza",
    "02 Zero hunger": "02 Hambre cero",
    "03 Good health and well-being": "03 Salud y bienestar",
    "04 Quality education": "04 Educación de calidad",
    "05 Gender equality": "05 Igualdad de género",
    "06 Clean water and sanitation": "06 Agua limpia y saneamiento",
    "07 Affordable and clean energy": "07 Energía asequible y no contaminante",
    "08 Decent work and economic growth": "08 Trabajo decente y crecimiento económico",
    "09 Industry, innovation and infrastructure": "09 Industria, innovación e infraestructura",
    "10 Reduced inequalities": "10 Reducción de las desigualdades",
    "11 Sustainable cities and communities": "11 Ciudades y comunidades sostenibles",
    "12 Responsible consumption and production": "12 Producción y consumo responsables",
    "13 Climate action": "13 Acción por el clima",
    "14 Life below water": "14 Vida submarina",
    "15 Life on land": "15 Vida de ecosistemas terrestres",
    "16 Peace, justice and strong institutions": "16 Paz, justicia e instituciones sólidas",
    "17 Partnerships for the goals": "17 Alianzas para lograr los objetivos",
}

# Mapa inverso para asegurar idioma inglés en columna dc.subject.ods
ODS_SPANISH_TO_ENGLISH = {v: k for k, v in ODS_ENGLISH_TO_SPANISH.items()}

