import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta

def meses_a_anos_meses(meses_float):
    if meses_float <= 0:
        return "0 meses"
    total_dias = int(round(meses_float * 30.4375))
    anos = total_dias // 365
    dias_remanentes = total_dias % 365
    meses = dias_remanentes // 30
    dias = dias_remanentes % 30
    
    partes = []
    if anos > 0:
        partes.append(f"{anos} año{'s' if anos > 1 else ''}")
    if meses > 0:
        partes.append(f"{meses} mes{'es' if meses > 1 else ''}")
    if dias > 0 and anos == 0:
        partes.append(f"{dias} día{'s' if dias > 1 else ''}")
        
    return " y ".join(partes) if partes else "0 meses"

def calcular_prescripcion(fecha_hecho, max_meses_pena, es_tentativa, hubo_imputacion, fecha_imputacion=None):
    meses_base = max_meses_pena / 2.0 if es_tentativa else max_meses_pena
    anos_prescripcion = meses_base / 12.0
    
    if anos_prescripcion < 5.0:
        anos_prescripcion = 5.0
        
    anos_enteros = int(anos_prescripcion)
    dias_restantes = int((anos_prescripcion - anos_enteros) * 365)
    fecha_prescripcion_inicial = fecha_hecho + relativedelta(years=anos_enteros, days=dias_restantes)
    
    fecha_prescripcion_final = fecha_prescripcion_inicial
    interrumpida = False
    anos_interrupcion = 0.0
    
    if hubo_imputacion and fecha_imputacion:
        interrumpida = True
        anos_interrupcion = anos_prescripcion / 2.0
        if anos_interrupcion < 3.0:
            anos_interrupcion = 3.0
            
        anos_int = int(anos_interrupcion)
        dias_int = int((anos_interrupcion - anos_int) * 365)
        fecha_prescripcion_final = fecha_imputacion + relativedelta(years=anos_int, days=dias_int)
        
    return {
        "anos_termino": round(anos_prescripcion, 2),
        "interrumpida": interrumpida,
        "anos_interrupcion": round(anos_interrupcion, 2) if interrumpida else 0.0,
        "fecha_inicial": fecha_prescripcion_inicial,
        "fecha_final": fecha_prescripcion_final
    }

def obtener_catalogo_delitos(fecha_hecho):
    aplica_ley_890 = fecha_hecho >= datetime.date(2005, 1, 1)
    
    if aplica_ley_890:
        catalogo = {
            "Personalizado (Ingresar límites manualmente)": (108.0, 360.0, False, 0.0),
            
            # --- TÍTULO I: DELITOS CONTRA LA VIDA Y LA INTEGRIDAD PERSONAL ---
            "Homicidio Simple (Art. 103)": (208.0, 450.0, False, 0.0),
            "Homicidio Agravado (Art. 104)": (400.0, 600.0, False, 0.0),
            "Homicidio Piadoso (Art. 106)": (12.0, 54.0, False, 0.0),
            "Lesiones: Incapacidad < 30 días (Art. 112 inc. 1)": (16.0, 36.0, False, 0.0),
            "Lesiones: Incapacidad de 30 a 90 días (Art. 112 inc. 2)": (16.0, 54.0, True, 10.0),
            "Lesiones: Incapacidad > 90 días (Art. 112 inc. 3)": (32.0, 90.0, True, 13.33),
            "Lesiones: Deformidad física transitoria (Art. 113 inc. 1)": (16.0, 108.0, True, 15.0),
            "Lesiones: Deformidad física permanente (Art. 113 inc. 2)": (24.0, 144.0, True, 20.0),
            "Lesiones: Perturbación funcional transitoria (Art. 114 inc. 1)": (24.0, 126.0, True, 15.0),
            "Lesiones: Perturbación funcional permanente (Art. 114 inc. 2)": (48.0, 144.0, True, 26.66),
            "Lesiones: Perturbación psíquica transitoria (Art. 115 inc. 1)": (24.0, 126.0, True, 26.0),
            "Lesiones: Perturbación psíquica permanente (Art. 115 inc. 2)": (36.0, 150.0, True, 30.0),
            "Lesiones: Pérdida anatómica/funcional órgano o miembro (Art. 116)": (72.0, 120.0, True, 25.0),
            "Inasistencia Alimentaria (Art. 233)": (16.0, 54.0, True, 13.33),

            # --- TÍTULO II: DELITOS CONTRA PERSONAS Y BIENES PROTEGIDOS POR DIH ---
            "Genocidio (Art. 101)": (208.0, 450.0, False, 0.0),

            # --- TÍTULO III: DELITOS CONTRA LA LIBERTAD INDIVIDUAL Y OTRAS GARANTÍAS ---
            "Secuestro Simple (Art. 168)": (192.0, 360.0, True, 666.66),
            "Secuestro Extorsivo (Art. 169)": (320.0, 500.0, True, 2666.66),
            "Desaparición Forzada (Art. 165)": (400.0, 720.0, True, 1333.33),
            "Constreñimiento Ilegal (Art. 182)": (16.0, 36.0, True, 13.33),
            "Amenazas (Art. 347)": (16.0, 72.0, True, 13.33),

            # --- TÍTULO IV: DELITOS CONTRA LA LIBERTAD, INTEGRIDAD Y FORMACIÓN SEXUALES ---
            "Acceso Carnal Violento (Art. 205)": (144.0, 252.0, False, 0.0),
            "Acto Sexual Violento (Art. 206)": (96.0, 180.0, False, 0.0),
            "Acceso Carnal Abusivo con Menor de 14 años (Art. 208)": (144.0, 252.0, False, 0.0),

            # --- TÍTULO VII: DELITOS CONTRA EL PATRIMONIO ECONÓMICO ---
            "Hurto Simple (Art. 239)": (16.0, 108.0, True, 13.33),
            "Hurto Calificado y Agravado (Arts. 239-241)": (72.0, 216.0, True, 13.33),
            "Hurto Calificado Mínimo (Art. 240)": (36.0, 108.0, True, 13.33),
            "Abuso de Confianza (Art. 249)": (16.0, 90.0, True, 13.33),
            "Estafa (Art. 246)": (32.0, 144.0, True, 13.33),
            "Extorsión (Art. 244)": (192.0, 288.0, True, 666.66),
            "Receptación (Art. 447)": (48.0, 144.0, True, 6.66),
            "Daño en Bien Ajeno (Art. 265)": (16.0, 72.0, True, 6.66),

            # --- TÍTULO IX: DELITOS CONTRA LA FAMILIA ---
            "Incesto (Art. 262)": (16.0, 72.0, False, 0.0),
            "Adopción Irregular (Art. 230)": (32.0, 96.0, True, 13.33),

            # --- TÍTULO X: DELITOS CONTRA LA ADMINISTRACIÓN PÚBLICA ---
            "Peculado por Apropiación (Art. 397)": (96.0, 216.0, True, 0.0),
            "Peculado por Uso (Art. 398)": (16.0, 72.0, True, 13.33),
            "Peculado Culposo (Art. 400)": (16.0, 54.0, True, 13.33),
            "Concusión (Art. 404)": (96.0, 180.0, True, 66.66),
            "Cohecho Propio (Art. 405)": (80.0, 144.0, True, 66.66),
            "Cohecho Impropio (Art. 406)": (48.0, 96.0, True, 33.33),
            "Celebración indebida de contratos (Art. 410)": (64.0, 144.0, True, 66.66),
            "Prevaricato por Acción (Art. 413)": (48.0, 144.0, False, 0.0),
            "Prevaricato por Omisión (Art. 414)": (32.0, 90.0, False, 0.0),
            "Abuso de Autoridad (Art. 416)": (16.0, 48.0, False, 0.0),
            "Cohecho por dar u ofrecer (Art. 407)": (48.0, 108.0, True, 50.0),

            # --- TÍTULO XI: DELITOS CONTRA LA FE PÚBLICA ---
            "Falsedad Material en Documento Público (Art. 287)": (48.0, 108.0, True, 13.33),
            "Falsedad en Documento Privado (Art. 289)": (16.0, 108.0, True, 13.33),
            "Falsedad Personal (Art. 296)": (16.0, 36.0, False, 0.0),

            # --- TÍTULO XII: DELITOS CONTRA EL ORDEN ECONÓMICO SOCIAL ---
            "Lavado de Activos (Art. 323)": (120.0, 300.0, True, 650.0),
            "Enriquecimiento Ilícito (Art. 327)": (96.0, 216.0, True, 133.33),

            # --- TÍTULO XIII: DELITOS CONTRA LA SEGURIDAD PÚBLICA ---
            "Fabricación, tráfico, porte de armas de fuego (Art. 365)": (108.0, 216.0, False, 0.0),
            "Fabricación, tráfico y porte de armas de uso privativo (Art. 366)": (132.0, 276.0, False, 0.0),
            "Concierto para delinquir (Art. 340)": (48.0, 108.0, False, 0.0),
            "Concierto para delinquir agravado (Art. 340 inc. 2)": (96.0, 216.0, False, 0.0),
            "Terrorismo (Art. 343)": (160.0, 270.0, True, 1333.33),
            "Tráfico, fabricación o porte de estupefacientes (Art. 376)": (128.0, 360.0, True, 133.33),
            "Destinación ilícita de bienes (Art. 377)": (72.0, 144.0, True, 133.33),

            # --- TÍTULO XVIII: DELITOS CONTRA LA ADMINISTRACIÓN DE JUSTICIA ---
            "Fuga de Presos (Art. 448)": (48.0, 108.0, False, 0.0),
            "Falso Testimonio (Art. 442)": (72.0, 144.0, True, 66.66),
            "Prevaricato (Defensa) / Fraude a Subvenciones": (48.0, 108.0, True, 13.33),
            "Encubrimiento (Art. 446)": (16.0, 48.0, False, 0.0)
        }
    else:
        # Catálogo histórico (anterior al 2005 - sin incremento Ley 890)
        catalogo = {
            "Personalizado (Ingresar límites manualmente)": (72.0, 240.0, False, 0.0),
            "Homicidio Simple (Art. 103 - Original)": (156.0, 300.0, False, 0.0),
            "Homicidio Agravado (Art. 104 - Original)": (300.0, 480.0, False, 0.0),
            "Secuestro Simple (Art. 168 - Original)": (96.0, 180.0, True, 500.0),
            "Hurto Calificado (Art. 240 - Original)": (36.0, 120.0, True, 10.0),
            "Fabricación y porte de armas (Art. 365 - Original)": (72.0, 144.0, False, 0.0),
            "Peculado por apropiación (Art. 397 - Original)": (48.0, 108.0, True, 0.0)
        }
    return catalogo, aplica_ley_890

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
    else:
        nuevo_min = min_trabajo
        nuevo_max = max_trabajo

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

    rango_base_movilidad = (round(nuevo_min, 2), round(nuevo_max, 2))

    rango_rebajado = rango_base_movilidad
    if modalidad_rebaja == "Allanamiento unilateral (Fases legales)":
        if "imputación" in fase_allanamiento.lower() or "1/2" in fase_allanamiento:
            rango_rebajado = (round(nuevo_min * 0.50, 2), round(nuevo_max * 0.50, 2))
        elif "preparatoria" in fase_allanamiento.lower() or "1/3" in fase_allanamiento:
            rango_rebajado = (round(nuevo_min * (2/3), 2), round(nuevo_max * (2/3), 2))
        elif "juicio" in fase_allanamiento.lower() or "1/5" in fase_allanamiento:
            rango_rebajado = (round(nuevo_min * (4/5), 2), round(nuevo_max * (4/5), 2))
            
    elif modalidad_rebaja == "Preacuerdo pactado (Porcentaje negociado)":
        factor_descuento = (100.0 - rebaja_pactada_pct) / 100.0
        rango_rebajado = (round(nuevo_min * factor_descuento, 2), round(nuevo_max * factor_descuento, 2))
    
    return {
        "rango_base": rango_base_movilidad,
        "cuartos_base": cuartos_dict,
        "rango_rebajado": rango_rebajado,
        "modalidad_rebaja": modalidad_rebaja
    }

st.set_page_config(page_title="Individualización de Penas", page_icon="⚖️")

st.title("⚖️ Calculadora Integral de Penas, Cuartos y Prescripción")
st.caption("Conforme a la Ley 599 de 2000, Ley 890 de 2004 y Ley 906 de 2004")

st.sidebar.header("📋 Parámetros del Caso")

fecha_hecho = st.sidebar.date_input("Fecha del hecho delictivo", value=datetime.date(2026, 1, 1))

delitos_catalogo, aplica_ley_890 = obtener_catalogo_delitos(fecha_hecho)
if aplica_ley_890:
    st.sidebar.success("✅ Vigencia posterior al 01/01/2005 (Incluye incrementos Ley 890).")
else:
    st.sidebar.warning("⚠️ Vigencia anterior al 01/01/2005 (Aplica penas históricas originales).")

st.sidebar.subheader("⏳ Control de Prescripción (Arts. 83 y 86 C.P. / Art. 292 Ley 906)")
hubo_imputacion = st.sidebar.checkbox("¿Se formuló imputación de cargos?")
fecha_imputacion = None
if hubo_imputacion:
    fecha_imputacion = st.sidebar.date_input("Fecha de la formulación de imputación", value=datetime.date(2026, 6, 1))

st.sidebar.subheader("🔒 Selección de Delito y Prisión Básica")
delito_sel = st.sidebar.selectbox("Seleccione el delito o tipo penal:", options=list(delitos_catalogo.keys()))

min_cat, max_cat, tiene_multa_sugerida, val_multa_sug = delitos_catalogo[delito_sel]

if "Personalizado" in delito_sel:
    min_basico = st.sidebar.number_input("Pena Mínima Básica (meses)", min_value=0.0, value=min_cat, step=1.0)
    max_basico = st.sidebar.number_input("Pena Máxima Básica (meses)", min_value=0.0, value=max_cat, step=1.0)
    aplica_multa = st.sidebar.checkbox("¿El tipo penal incluye pena de multa? (Art. 39)")
    min_multa, max_multa = 0.0, 0.0
else:
    min_basico = min_cat
    max_basico = max_cat
    st.sidebar.info(f"Pena básica legal: {min_basico} a {max_basico} meses ({meses_a_anos_meses(min_basico)} a {meses_a_anos_meses(max_basico)})")
    aplica_multa = st.sidebar.checkbox("¿Incluye pena de multa?", value=tiene_multa_sugerida)
    min_multa, max_multa = val_multa_sug, val_multa_sug * 10 if val_multa_sug > 0 else 0.0

valor_smlmv = 1423500.0  
if aplica_multa and not "Personalizado" in delito_sel:
    valor_smlmv = st.sidebar.number_input("Valor SMLMV (COP)", min_value=0.0, value=1423500.0, step=10000.0)
elif aplica_multa:
    min_multa = st.sidebar.number_input("Multa Mínima (SMLMV)", min_value=0.0, value=10.0, step=5.0)
    max_multa = st.sidebar.number_input("Multa Máxima (SMLMV)", min_value=0.0, value=100.0, step=5.0)
    valor_smlmv = st.sidebar.number_input("Valor SMLMV (COP)", min_value=0.0, value=1423500.0, step=10000.0)

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

st.sidebar.subheader("🤝 Terminación Anticipada")
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
        "Porcentaje de reb
