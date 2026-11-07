import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta

def calcular_prescripcion(fecha_hecho, max_meses_pena, es_tentativa, hubo_imputacion, fecha_imputacion=None):
    # Término base en años (máximo de la pena)
    # Si es tentativa, se reduce a la mitad
    meses_base = max_meses_pena / 2.0 if es_tentativa else max_meses_pena
    anos_prescripcion = meses_base / 12.0
    
    # Por regla general, el término no puede ser inferior a 5 años (Art. 83)
    if anos_prescripcion < 5.0:
        anos_prescripcion = 5.0
        
    # 1. Prescripción desde la ocurrencia del hecho
    anos_enteros = int(anos_prescripcion)
    dias_restantes = int((anos_prescripcion - anos_enteros) * 365)
    fecha_prescripcion_inicial = fecha_hecho + relativedelta(years=anos_enteros, days=dias_restantes)
    
    fecha_prescripcion_final = fecha_prescripcion_inicial
    interrumpida = False
    
    # 2. Interrupción por Formulación de Imputación (Art. 86)
    if hubo_imputacion and fecha_imputacion:
        interrumpida = True
        # Comienza a correr la mitad del término (mínimo 3 años, máximo 5 años)
        termino_interrupcion_anos = anos_prescripcion / 2.0
        if termino_interrupcion_anos < 3.0:
            termino_interrupcion_anos = 3.0
        elif termino_interrupcion_anos > 5.0:
            termino_interrupcion_anos = 5.0
            
        anos_int = int(termino_interrupcion_anos)
        dias_int = int((termino_interrupcion_anos - anos_int) * 365)
        fecha_prescripcion_final = fecha_imputacion + relativedelta(years=anos_int, days=dias_int)
        
    return {
        "anos_termino": round(anos_prescripcion, 2),
        "fecha_inicial": fecha_prescripcion_inicial,
        "interrumpida": interrumpida,
        "fecha_final": fecha_prescripcion_final
    }

def calcular_penas_y_cuartos(
    min_basico, max_basico, regla, prop1=0.0, prop2=None, 
    es_calificado=False, calif_min_aumento=0.0, calif_max_aumento=0.0,
    estado_especial="Ninguno",
    es_concurso=False, aumento_concurso_min=0.0, aumento_concurso_max=0.0,
    tentativa=False,
    tipo_circ_especifica="Ninguna", frac_circ_min=0.0, frac_circ_max=0.0,
    gen_atenuantes=False, gen_agravantes=False,
    modalidad_rebaja="Ninguna", fase_allanamiento="", rebaja_pactada_pct=0.0
):
    min_trabajo = min_basico
    max_trabajo = max_basico
    
    if es_calificado:
        min_trabajo = min_basico + (min_basico * calif_min_aumento)
        max_trabajo = max_basico + (max_basico * calif_max_aumento)

    if estado_especial == "Ira o Intenso Dolor (Art. 57: Disminución de 1/6 a 1/2)":
        min_trabajo = max(0.0, min_trabajo - (min_trabajo * 0.50)) 
        max_trabajo = max(0.0, max_trabajo - (max_trabajo * (1/6))) 
    elif estado_especial == "Marginalidad, Ignorancia o Pobreza Extrema (Art. 56: Disminución de 1/2 a 3/4)":
        min_trabajo = max(0.0, min_trabajo - (min_trabajo * 0.75)) 
        max_trabajo = max(0.0, max_trabajo - (max_trabajo * 0.50)) 

    if es_concurso:
        min_trabajo = min_trabajo + (min_trabajo * aumento_concurso_min)
        max_trabajo = max_trabajo + (max_trabajo * aumento_concurso_max)

    if tentativa:
        min_trabajo = min_trabajo * 0.25  
        max_trabajo = max_trabajo * 0.50  

    if tipo_circ_especifica == "Agravante específica (Aumento fraccionado)":
        min_trabajo = min_trabajo + (min_trabajo * frac_circ_min)
        max_trabajo = max_trabajo + (max_trabajo * frac_circ_max)
    elif tipo_circ_especifica == "Atenuante específica (Disminución fraccionada)":
        min_trabajo = max(0.0, min_trabajo - (min_trabajo * frac_circ_max))
        max_trabajo = max(0.0, max_trabajo - (max_trabajo * frac_circ_min))

    if modalidad_rebaja == "Allanamiento unilateral (Fases legales)":
        if "Imputación" in fase_allanamiento:
            min_trabajo = min_trabajo * 0.50
            max_trabajo = max_trabajo * 0.50
        elif "Preparatoria" in fase_allanamiento:
            min_trabajo = min_trabajo * (2/3)
            max_trabajo = max_trabajo * (2/3)
        elif "Juicio" in fase_allanamiento:
            min_trabajo = min_trabajo * (4/5)
            max_trabajo = max_trabajo * (4/5)
            
    elif modalidad_rebaja == "Preacuerdo pactado (Porcentaje negociado)":
        factor_descuento = (100.0 - rebaja_pactada_pct) / 100.0
        min_trabajo = min_trabajo * factor_descuento
        max_trabajo = max_trabajo * factor_descuento

    if regla == 0:
        nuevo_min = min_trabajo
        nuevo_max = max_trabajo
    elif regla == 1:
        nuevo_min = min_trabajo + (min_trabajo * prop1)
        nuevo_max = max_trabajo + (max_trabajo * prop1)
    elif regla == 2:
        nuevo_min = min_trabajo
        nuevo_max = max_trabajo + (max_trabajo * prop1)
    elif regla == 3:
        nuevo_min = min_trabajo - (min_trabajo * prop1)
        nuevo_max = max_trabajo
    elif regla == 4:
        menor = min(prop1, prop2 if prop2 is not None else 0.0)
        mayor = max(prop1, prop2 if prop2 is not None else 0.0)
        nuevo_min = min_trabajo + (min_trabajo * menor)
        nuevo_max = max_trabajo + (max_trabajo * mayor)
    elif regla == 5:
        menor = min(prop1, prop2 if prop2 is not None else 0.0)
        mayor = max(prop1, prop2 if prop2 is not None else 0.0)
        nuevo_min = min_trabajo - (min_trabajo * mayor)
        nuevo_max = max_trabajo - (max_trabajo * menor)
    
    nuevo_min = max(0.0, nuevo_min)
    nuevo_max = max(0.0, nuevo_max)
    
    amplitud_total = nuevo_max - nuevo_min
    cuarto_tam = amplitud_total / 4.0

    c1 = (round(nuevo_min, 2), round(nuevo_min + cuarto_tam, 2))
    c2 = (round(nuevo_min + cuarto_tam, 2), round(nuevo_min + 2*cuarto_tam, 2))
    c3 = (round(nuevo_min + 2*cuarto_tam, 2), round(nuevo_min + 3*cuarto_tam, 2))
    c4 = (round(nuevo_min + 3*cuarto_tam, 2), round(nuevo_max, 2))

    if gen_agravantes and not gen_atenuantes:
        cuartos_dict = {
            "Segundo cuarto (Medio 1)": c2,
            "Tercer cuarto (Medio 2)": c3,
            "Cuarto cuarto (Máximo)": c4,
            "(Primer cuarto excluido por Art. 61)": c1
        }
    elif gen_atenuantes and not gen_agravantes:
        cuartos_dict = {
            "Primer cuarto (Mínimo - Atenuado)": c1,
            "Segundo cuarto (Medio 1)": c2,
            "Tercer cuarto (Medio 2)": c3,
            "(Cuarto cuarto desplazado)": c4
        }
    else:
        cuartos_dict = {
            "Primer cuarto (Mínimo)": c1,
            "Segundo cuarto (Medio 1)": c2,
            "Tercer cuarto (Medio 2)": c3,
            "Cuarto cuarto (Máximo)": c4,
        }
    
    return {
        "rango": (round(nuevo_min, 2), round(nuevo_max, 2)),
        "cuartos": cuartos_dict
    }

st.set_page_config(page_title="Individualización de Penas", page_icon="⚖️")

st.title("⚖️ Calculadora Integral de Penas, Cuartos y Prescripción")
st.caption("Conforme al Código Penal Colombiano (Ley 599 de 2000) y Ley 906 de 2004")

st.sidebar.header("📋 Parámetros del Caso")

fecha_hecho = st.sidebar.date_input("Fecha del hecho delictivo", value=datetime.date(2026, 1, 1))

# Control de Prescripción Procesal
st.sidebar.subheader("⏳ Control de Prescripción (Art. 83 y 86)")
hubo_imputacion = st.sidebar.checkbox("¿Se formuló imputación de cargos?")
fecha_imputacion = None
if hubo_imputacion:
    fecha_imputacion = st.sidebar.date_input("Fecha de la formulación de imputación", value=datetime.date(2026, 6, 1))

aplica_multa = st.sidebar.checkbox("¿El tipo penal incluye pena de multa? (Art. 39)")

st.sidebar.subheader("🔒 Prisión (Delito Base)")
min_basico = st.sidebar.number_input("Pena Mínima Básica (meses)", min_value=0.0, value=108.0, step=1.0)
max_basico = st.sidebar.number_input("Pena Máxima Básica (meses)", min_value=0.0, value=360.0, step=1.0)

st.sidebar.subheader("🔺 1. Circunstancias Calificantes")
es_calificado = st.sidebar.checkbox("¿Es tipo calificado / agravante de entrada?")
calif_min_aumento, calif_max_aumento = 0.0, 0.0
if es_calificado:
    calif_min_aumento = st.sidebar.number_input("Incremento mín al básico", min_value=0.0, value=0.5, step=0.1)
    calif_max_aumento = st.sidebar.number_input("Incremento máx al básico", min_value=0.0, value=1.0, step=0.1)

st.sidebar.subheader("🔥 2. Atenuantes Especiales")
estado_especial = st.sidebar.selectbox(
    "Seleccione estado especial:",
    options=[
        "Ninguno",
        "Ira o Intenso Dolor (Art. 57: Disminución de 1/6 a 1/2)",
        "Marginalidad, Ignorancia o Pobreza Extrema (Art. 56: Disminución de 1/2 a 3/4)"
    ]
)

st.sidebar.subheader("🔗 3. Concurso de Delitos (Art. 31)")
es_concurso = st.sidebar.checkbox("¿Hay concurso de delitos?")
aumento_concurso_min, aumento_concurso_max = 0.0, 0.0
if es_concurso:
    aumento_concurso_min = st.sidebar.number_input("Fracción incremento mín concurso", min_value=0.0, value=0.0, step=0.1)
    aumento_concurso_max = st.sidebar.number_input("Fracción incremento máx concurso", min_value=0.0, value=0.0, step=0.1)

st.sidebar.subheader("🎯 4. Fase de Ejecución")
es_tentativa = st.sidebar.checkbox("¿Es conducta tentada? (Art. 27)")

st.sidebar.subheader("📌 5. Circunstancias Específicas")
tipo_circ_especifica = st.sidebar.selectbox(
    "Modificadores específicos:",
    options=["Ninguna", "Agravante específica (Aumento fraccionado)", "Atenuante específica (Disminución fraccionada)"]
)
frac_circ_min, frac_circ_max = 0.0, 0.0
if tipo_circ_especifica != "Ninguna":
    frac_circ_min = st.sidebar.number_input("Fracción inferior", min_value=0.0, max_value=2.0, value=0.33, step=0.01)
    frac_circ_max = st.sidebar.number_input("Fracción superior", min_value=0.0, max_value=2.0, value=0.50, step=0.01)

st.sidebar.subheader("⚖️ 6. Circunstancias Genéricas (Art. 55 y 58)")
gen_atenuantes = st.sidebar.checkbox("Concurren atenuantes genéricas (Art. 55)")
gen_agravantes = st.sidebar.checkbox("Concurren agravantes genéricas (Art. 58 - Excluye 1er cuarto)")

min_multa, max_multa = 0.0, 0.0
valor_smlmv = 1423500.0  
if aplica_multa:
    st.sidebar.subheader("💰 Pena Pecuniaria (Multa)")
    min_multa = st.sidebar.number_input("Multa Mínima Básica (SMLMV)", min_value=0.0, value=133.33, step=10.0)
    max_multa = st.sidebar.number_input("Multa Máxima Básica (SMLMV)", min_value=0.0, value=1500.0, step=10.0)
    valor_smlmv = st.sidebar.number_input("Valor SMLMV (COP)", min_value=0.0, value=1423500.0, step=10000.0)

st.sidebar.subheader("🤝 7. Terminación Anticipada")
modalidad_rebaja = st.sidebar.radio(
    "Modalidad de rebaja:",
    options=["Ninguna", "Allanamiento unilateral (Fases legales)", "Preacuerdo pactado (Porcentaje negociado)"]
)

fase_allanamiento = ""
rebaja_pactada_pct = 0.0

if modalidad_rebaja == "Allanamiento unilateral (Fases legales)":
    fase_allanamiento = st.sidebar.selectbox(
        "Fase Procesal",
        options=[
            "Hasta formulación de imputación (Rebaja hasta 1/2)",
            "Hasta antes de audiencia preparatoria (Rebaja hasta 1/3)",
            "Hasta inicio del juicio oral (Rebaja hasta 1/5)"
        ]
    )
elif modalidad_rebaja == "Preacuerdo pactado (Porcentaje negociado)":
    rebaja_pactada_pct = st.sidebar.number_input(
        "Porcentaje de rebaja pactado (%)",
        min_value=0.0,
        max_value=100.0,
        value=35.0,
        step=1.0
    )

st.sidebar.subheader("📊 8. Reglas de Modificación (Art. 61)")
reglas_dict = {
    0: "0. Sin regla (Límites básicos / post-ajustes)",
    1: "1. Aumento/Disminución proporcional al mín y máx",
    2: "2. Aumento hasta en una proporción al máx",
    3: "3. Disminución hasta en una proporción al mín",
    4: "4. Aumento en dos proporciones",
    5: "5. Disminución en dos proporciones"
}

regla_sel = st.sidebar.selectbox("Seleccione la Regla", options=list(reglas_dict.keys()), format_func=lambda x: reglas_dict[x])

prop1, prop2 = 0.0, 0.0
if regla_sel in [1, 2, 3]:
    prop1 = st.sidebar.number_input("Proporción", min_value=0.0, max_value=1.0, value=0.3333, step=0.01)
elif regla_sel in [4, 5]:
    prop1 = st.sidebar.number_input("Primera Proporción", min_value=0.0, max_value=1.0, value=0.3333, step=0.01)
    prop2 = st.sidebar.number_input("Segunda Proporción", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

if st.sidebar.button("Calcular individualización"):
    if min_basico > max_basico:
        st.error("El límite mínimo de prisión no puede superar el límite máximo.")
    elif aplica_multa and min_multa > max_multa:
        st.error("El límite mínimo de multa no puede superar el máximo.")
    else:
        st.success(f"📅 **Fecha del
