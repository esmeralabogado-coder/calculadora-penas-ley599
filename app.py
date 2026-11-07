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
    # Lógica de verificación temporal (Ley 890 de 2004 rige desde el 1 de enero de 2005)
    aplica_ley_890 = fecha_hecho >= datetime.date(2005, 1, 1)
    
    # Base de datos discriminada de delitos (valores en meses de prisión [min, max])
    # Si la fecha es anterior a 2005, se aplica la pena original del C.P. de 2000 sin incremento de Ley 890
    if aplica_ley_890:
        catalogo = {
            "Personalizado (Ingresar límites manualmente)": (108.0, 360.0, False, 0.0),
            "Homicidio Simple (Art. 103)": (208.0, 450.0, False, 0.0),
            "Homicidio Agravado (Art. 104)": (400.0, 600.0, False, 0.0),
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
            "Fabricación, tráfico y porte de armas (Art. 365)": (108.0, 216.0, False, 0.0),
            "Tráfico de estupefacientes (Art. 376)": (128.0, 360.0, True, 133.33),
            "Hurto Calificado y Agravado (Arts. 239-241)": (72.0, 216.0, False, 0.0),
            "Extorsión (Art. 244)": (192.0, 288.0, True, 666.66),
            "Secuestro Simple (Art. 168)": (192.0, 360.0, True, 666.66),
            "Peculado por apropiación (Art. 397)": (96.0, 216.0, True, 0.0),
            "Fuga de presos (Art. 448)": (48.0, 108.0, False, 0.0)
        }
    else:
        # Penas históricas originales (antes del incremento general de la Ley 890 de 2004)
        catalogo = {
            "Personalizado (Ingresar límites manualmente)": (72.0, 240.0, False, 0.0),
            "Homicidio Simple (Art. 103 - Original)": (156.0, 300.0, False, 0.0),
            "Homicidio Agravado (Art. 104 - Original)": (300.0, 480.0, False, 0.0),
            "Lesiones: Incapacidad < 30 días (Art. 112 - Original)": (12.0, 24.0, False, 0.0),
            "Fabricación, tráfico y porte de armas (Art. 365 - Original)": (72.0, 144.0, False, 0.0)
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
        max_trabajo = max(0.0, max_trabajo - (min_trabajo * frac_circ_min))

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

# Obtener catálogo dinámico según la fecha del hecho (vigencia Ley 890 / penas originales)
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
        st.success(f"📅 Fecha del hecho delictivo registrada: {fecha_hecho.strftime('%d/%m/%Y')}")
        
        res_presc = calcular_prescripcion(fecha_hecho, max_basico, es_tentativa, hubo_imputacion, fecha_imputacion)
        
        st.header("⏳ Análisis de Prescripción y Extinción de la Acción Penal (Ley 906 / Ley 599)")
        st.info(f"Término prescriptivo inicial: {res_presc['anos_termino']} años.")
        if res_presc['interrumpida']:
            st.warning(f"⚠️ Término interrumpido por Formulación de Imputación el {fecha_imputacion.strftime('%d/%m/%Y')}. Nuevo término de prescripción por la mitad del máximo ({res_presc['anos_interrupcion']} años, conforme al Art. 292 Ley 906).")
            st.error(f"🚨 FECHA FATÍDICA DE EXTINCIÓN DE LA ACCIÓN PENAL: {res_presc['fecha_final'].strftime('%d/%m/%Y')}")
        else:
            st.error(f"🚨 FECHA FATÍDICA DE EXTINCIÓN DE LA ACCIÓN PENAL: {res_presc['fecha_final'].strftime('%d/%m/%Y')}")

        st.markdown("---")

        res_prision = calcular_penas_y_cuartos(
            min_basico, max_basico, regla_sel, prop1, prop2, 
            es_calificado, calif_min_aumento, calif_max_aumento,
            estado_especial,
            es_concurso, aumento_concurso_min, aumento_concurso_max,
            es_tentativa,
            tipo_circ_especifica, frac_circ_min, frac_circ_max,
            gen_atenuantes, gen_agravantes,
            modalidad_rebaja, fase_allanamiento, rebaja_pactada_pct
        )
        
        st.header("🔒 1. Pena Privativa de la Libertad (Prisión)")
        notas_ajuste = []
        notas_ajuste.append(f"Delito: {delito_sel}")
        if es_calificado: notas_ajuste.append("Tipo Calificado / Agravante de Entrada")
        if estado_especial != "Ninguno": notas_ajuste.append(estado_especial)
        if es_concurso: notas_ajuste.append("Concurso de Delitos (Art. 31)")
        if gen_agravantes and not gen_atenuantes: notas_ajuste.append("Agravantes Genéricas (Art. 61 - Se excluye 1er cuarto)")
        if gen_atenuantes and not gen_agravantes: notas_ajuste.append("Atenuantes Genéricas (Art. 61)")
        if tipo_circ_especifica != "Ninguna": notas_ajuste.append(tipo_circ_especifica)
        if es_tentativa: notas_ajuste.append("Tentativa (Art. 27)")
        if modalidad_rebaja != "Ninguna": 
            detalle_rebaja = fase_allanamiento if modalidad_rebaja == "Allanamiento unilateral (Fases legales)" else f"Preacuerdo del {rebaja_pactada_pct}%"
            notas_ajuste.append(f"Terminación Anticipada: {detalle_rebaja}")
        
        if notas_ajuste:
            st.warning(f"⚠️ Parámetros aplicados: {', '.join(notas_ajuste)}.")
            
        # Mostrar Cuartos Base de Movilidad
        st.subheader("📊 Cuartos Punitivos de Movilidad (Marco Ajustado)")
        r_base_min, r_base_max = res_prision["rango_base"]
        st.info(f"Marco punitivo de movilidad: {r_base_min} a {r_base_max} meses ({meses_a_anos_meses(r_base_min)} a {meses_a_anos_meses(r_base_max)})")
        
        cols = st.columns(2)
        idx = 0
        for nombre, (c_min, c_max) in res_prision["cuartos_base"].items():
            with cols[idx % 2]:
                st.metric(label=nombre, value=f"{c_min} - {c_max} m", delta=f"{meses_a_anos_meses(c_min)} a {meses_a_anos_meses(c_max)}")
            idx += 1

        if modalidad_rebaja != "Ninguna":
            st.markdown("---")
            r_reb_min, r_reb_max = res_prision["rango_rebajado"]
            titulo_reb = "📉 Rango Definitivo Rebajado por Allanamiento (Mínimo y Máximo)" if modalidad_rebaja == "Allanamiento unilateral (Fases legales)" else "🤝 Rango Definitivo Pactado en Preacuerdo"
            st.subheader(titulo_reb)
            st.success(f"**{r_reb_min} a {r_reb_max} meses** ({meses_a_anos_meses(r_reb_min)} a {meses_a_anos_meses(r_reb_max)})")

        res_multa = None
        if aplica_multa and min_multa > 0:
            st.markdown("---")
            res_multa = calcular_penas_y_cuartos(
                min_multa, max_multa, regla_sel, prop1, prop2, 
                es_tentativa, modalidad_rebaja, fase_allanamiento, rebaja_pactada_pct,
                es_concurso, aumento_concurso_min, aumento_concurso_max,
                tipo_circ_especifica, frac_circ_min, frac_circ_max,
                gen_atenuantes, gen_agravantes,
                modalidad_rebaja, fase_allanamiento, rebaja_pactada_pct
            )
            
            st.header("💰 2. Pena Pecuniaria (Multa - Art. 39)")
            m_base_min, m_base_max = res_multa["rango_base"]
            st.info(f"Límite Multa Marco Base: {m_base_min} SMLMV a {m_base_max} SMLMV")
            
            cols_m = st.columns(2)
            idx_m = 0
            for nombre, (c_min, c_max) in res_multa["cuartos_base"].items():
                with cols_m[idx_m % 2]:
                    st.metric(label=nombre, value=f"{c_min} - {c_max} SMLMV")
                idx_m += 1
                
            if modalidad_rebaja != "Ninguna":
                m_reb_min, m_reb_max = res_multa["rango_rebajado"]
                min_cop = m_reb_min * valor_smlmv
                max_cop = m_reb_max * valor_smlmv
                st.success(f"📉 Multa Definitiva Rebajada: **{m_reb_min} a {m_reb_max} SMLMV** (Equivalente: ${min_cop:,.2f} - ${max_cop:,.2f})")
            else:
                min_cop = m_base_min * valor_smlmv
                max_cop = m_base_max * valor_smlmv
                st.caption(f"💵 Equivalente en COP (${valor_smlmv:,.2f} por SMLMV): ${min_cop:,.2f} hasta ${max_cop:,.2f}")

        st.markdown("---")
        st.subheader("📑 Resumen para Memoriales / Informes")
        
        texto_etapa_reporte = f"{fase_allanamiento}" if modalidad_rebaja == "Allanamiento unilateral (Fases legales)" else (f"Preacuerdo pactado del {rebaja_pactada_pct}%" if modalidad_rebaja == "Preacuerdo pactado (Porcentaje negociado)" else "Juicio Ordinario (Sin rebaja)")

        r_final_min, r_final_max = res_prision["rango_rebajado"] if modalidad_rebaja != "Ninguna" else res_prision["rango_base"]

        texto_reporte = f"""INFORME DE DOSIFICACIÓN Y PRESCRIPCIÓN
Fecha del hecho: {fecha_hecho.strftime('%d/%m/%Y')}
Normativa aplicable: Código Penal (Ley 599 de 2000) y Código de Procedimiento Penal (Ley 906 de 2004)
Delito analizado: {delito_sel}

CONTROL DE PRESCRIPCIÓN (Extinción de la Acción Penal - Art. 292 Ley 906 / Art. 86 C.P.):
- Término prescriptivo inicial: {res_presc['anos_termino']} años.
- ¿Hubo formulación de imputación?: {'SÍ (' + fecha_imputacion.strftime('%d/%m/%Y') + ' - Nuevo término por la mitad del máximo: ' + str(res_presc['anos_interrupcion']) + ' años)' if hubo_imputacion else 'NO'}
- FECHA FATÍDICA DE EXTINCIÓN DE LA ACCIÓN PENAL: {res_presc['fecha_final'].strftime('%d/%m/%Y')}

1. PENA PRIVATIVA DE LA LIBERTAD (PRISIÓN):
- Modalidad de terminación / defensa: {modalidad_rebaja}
- Detalle de la etapa / rebaja aplicada: {texto_etapa_reporte}
- Marco punitivo base de movilidad (Cuartos punitivos): {res_prision['rango_base'][0]} a {res_prision['rango_base'][1]} meses.
- Rango o pena definitiva aplicable: {r_final_min} a {r_final_max} meses ({meses_a_anos_meses(r_final_min)} a {meses_a_anos_meses(r_final_max)}).
"""
        if modalidad_rebaja != "Ninguna":
            texto_reporte += f"- Nota: Se calcularon los cuartos punitivos de movilidad y la rebaja por terminación anticipada ({modalidad_rebaja}) se aplicó sobre ambos extremos (mínimo y máximo) conforme a la jurisprudencia de la Sala Penal de la CSJ.\n"
        else:
            texto_reporte += f"- Sistema de Cuartos Punitivos (Art. 61):\n"
            for nombre, (c_min, c_max) in res_prision["cuartos_base"].items():
                texto_reporte += f"  * {nombre}: {c_min} a {c_max} meses ({meses_a_anos_meses(c_min)} a {meses_a_anos_meses(c_max)})\n"
            
        if aplica_multa and res_multa and min_multa > 0:
            m_fin_min, m_fin_max = res_multa["rango_rebajado"] if modalidad_rebaja != "Ninguna" else res_multa["rango_base"]
            texto_reporte += f"""
2. PENA PECUNIARIA (MULTA - Art. 39):
- Rango de multa aplicable: {m_fin_min} SMLMV a {m_fin_max} SMLMV.
"""

        st.text_area("Copia este texto para tus documentos:", value=texto_reporte, height=280)
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
    
    # 1. Tipo Calificado
    if es_calificado:
        min_trabajo = min_basico + (min_basico * calif_min_aumento)
        max_trabajo = max_basico + (max_basico * calif_max_aumento)

    # 2. Atenuantes Especiales (Ira / Marginalidad)
    if estado_especial == "Ira o Intenso Dolor (Art. 57: Disminución de 1/6 a 1/2)":
        min_trabajo = max(0.0, min_trabajo - (min_trabajo * 0.50)) 
        max_trabajo = max(0.0, max_trabajo - (max_trabajo * (1/6))) 
    elif estado_especial == "Marginalidad, Ignorancia o Pobreza Extrema (Art. 56: Disminución de 1/2 a 3/4)":
        min_trabajo = max(0.0, min_trabajo - (min_trabajo * 0.75)) 
        max_trabajo = max(0.0, max_trabajo - (max_trabajo * 0.50)) 

    # 3. Concurso
    if es_concurso:
        min_trabajo = min_trabajo + (min_trabajo * aumento_concurso_min)
        max_trabajo = max_trabajo + (max_trabajo * aumento_concurso_max)

    # 4. Tentativa
    if tentativa:
        min_trabajo = min_trabajo * 0.25  
        max_trabajo = max_trabajo * 0.50  

    # 5. Circunstancias Específicas
    if tipo_circ_especifica == "Agravante específica (Aumento fraccionado)":
        min_trabajo = min_trabajo + (min_trabajo * frac_circ_min)
        max_trabajo = max_trabajo + (max_trabajo * frac_circ_max)
    elif tipo_circ_especifica == "Atenuante específica (Disminución fraccionada)":
        min_trabajo = max(0.0, min_trabajo - (min_trabajo * frac_circ_max))
        max_trabajo = max(0.0, max_trabajo - (max_trabajo * frac_circ_min))

    # 6. Reglas de Modificación (Art. 61)
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
    
    # Cálculo de los 4 cuartos base de movilidad
    amplitud_total = nuevo_max - nuevo_min
    cuarto_tam = amplitud_total / 4.0

    c1 = (round(nuevo_min, 2), round(nuevo_min + cuarto_tam, 2))
    c2 = (round(nuevo_min + cuarto_tam, 2), round(nuevo_min + 2*cuarto_tam, 2))
    c3 = (round(nuevo_min + 2*cuarto_tam, 2), round(nuevo_min + 3*cuarto_tam, 2))
    c4 = (round(nuevo_min + 3*cuarto_tam, 2), round(nuevo_max, 2))

    # Diccionario de cuartos base antes de rebajas
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

    # Rango base de movilidad antes de rebajas
    rango_base_movilidad = (round(nuevo_min, 2), round(nuevo_max, 2))

    # 7. Aplicación de Rebajas por Terminación Anticipada sobre MÍNIMO y MÁXIMO
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
st.caption("Conforme al Código Penal (Ley 599 de 2000) y Código de Procedimiento Penal (Ley 906 de 2004)")

st.sidebar.header("📋 Parámetros del Caso")

fecha_hecho = st.sidebar.date_input("Fecha del hecho delictivo", value=datetime.date(2026, 1, 1))

st.sidebar.subheader("⏳ Control de Prescripción (Arts. 83 y 86 C.P. / Art. 292 Ley 906)")
hubo_imputacion = st.sidebar.checkbox("¿Se formuló imputación de cargos?")
fecha_imputacion = None
if hubo_imputacion:
    fecha_imputacion = st.sidebar.date_input("Fecha de la formulación de imputación", value=datetime.date(2026, 6, 1))

aplica_multa = st.sidebar.checkbox("¿El tipo penal incluye pena de multa? (Art. 39)")

st.sidebar.subheader("🔒 Prisión (Límites Básicos)")
min_basico = st.sidebar.number_input("Pena Mínima Básica (meses)", min_value=0.0, value=108.0, step=1.0)
max_basico = st.sidebar.number_input("Pena Máxima Básica (meses)", min_value=0.0, value=360.0, step=1.0)
st.sidebar.caption(f"Equivalente: {meses_a_anos_meses(min_basico)} a {meses_a_anos_meses(max_basico)}")

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
        st.success(f"📅 Fecha del hecho delictivo registrada: {fecha_hecho.strftime('%d/%m/%Y')}")
        
        res_presc = calcular_prescripcion(fecha_hecho, max_basico, es_tentativa, hubo_imputacion, fecha_imputacion)
        
        st.header("⏳ Análisis de Prescripción y Extinción de la Acción Penal (Ley 906 / Ley 599)")
        st.info(f"Término prescriptivo inicial: {res_presc['anos_termino']} años.")
        if res_presc['interrumpida']:
            st.warning(f"⚠️ Término interrumpido por Formulación de Imputación el {fecha_imputacion.strftime('%d/%m/%Y')}. Nuevo término de prescripción por la mitad del máximo ({res_presc['anos_interrupcion']} años, conforme al Art. 292 Ley 906).")
            st.error(f"🚨 FECHA FATÍDICA DE EXTINCIÓN DE LA ACCIÓN PENAL: {res_presc['fecha_final'].strftime('%d/%m/%Y')}")
        else:
            st.error(f"🚨 FECHA FATÍDICA DE EXTINCIÓN DE LA ACCIÓN PENAL: {res_presc['fecha_final'].strftime('%d/%m/%Y')}")

        st.markdown("---")

        res_prision = calcular_penas_y_cuartos(
            min_basico, max_basico, regla_sel, prop1, prop2, 
            es_calificado, calif_min_aumento, calif_max_aumento,
            estado_especial,
            es_concurso, aumento_concurso_min, aumento_concurso_max,
            es_tentativa,
            tipo_circ_especifica, frac_circ_min, frac_circ_max,
            gen_atenuantes, gen_agravantes,
            modalidad_rebaja, fase_allanamiento, rebaja_pactada_pct
        )
        
        st.header("🔒 1. Pena Privativa de la Libertad (Prisión)")
        notas_ajuste = []
        if es_calificado: notas_ajuste.append("Tipo Calificado / Agravante de Entrada")
        if estado_especial != "Ninguno": notas_ajuste.append(estado_especial)
        if es_concurso: notas_ajuste.append("Concurso de Delitos (Art. 31)")
        if gen_agravantes and not gen_atenuantes: notas_ajuste.append("Agravantes Genéricas (Art. 61 - Se excluye 1er cuarto)")
        if gen_atenuantes and not gen_agravantes: notas_ajuste.append("Atenuantes Genéricas (Art. 61)")
        if tipo_circ_especifica != "Ninguna": notas_ajuste.append(tipo_circ_especifica)
        if es_tentativa: notas_ajuste.append("Tentativa (Art. 27)")
        if modalidad_rebaja != "Ninguna": 
            detalle_rebaja = fase_allanamiento if modalidad_rebaja == "Allanamiento unilateral (Fases legales)" else f"Preacuerdo del {rebaja_pactada_pct}%"
            notas_ajuste.append(f"Terminación Anticipada: {detalle_rebaja}")
        
        if notas_ajuste:
            st.warning(f"⚠️ Ajustes aplicados: {', '.join(notas_ajuste)}.")
            
        # Mostrar Cuartos Base de Movilidad
        st.subheader("📊 Cuartos Punitivos de Movilidad (Marco Ajustado)")
        r_base_min, r_base_max = res_prision["rango_base"]
        st.info(f"Marco punitivo de movilidad: {r_base_min} a {r_base_max} meses ({meses_a_anos_meses(r_base_min)} a {meses_a_anos_meses(r_base_max)})")
        
        cols = st.columns(2)
        idx = 0
        for nombre, (c_min, c_max) in res_prision["cuartos_base"].items():
            with cols[idx % 2]:
                st.metric(label=nombre, value=f"{c_min} - {c_max} m", delta=f"{meses_a_anos_meses(c_min)} a {meses_a_anos_meses(c_max)}")
            idx += 1

        # Si hay rebaja por terminación anticipada, mostrar el rango definitivo resultante
        if modalidad_rebaja != "Ninguna":
            st.markdown("---")
            r_reb_min, r_reb_max = res_prision["rango_rebajado"]
            titulo_reb = "📉 Rango Definitivo Rebajado por Allanamiento (Mínimo y Máximo)" if modalidad_rebaja == "Allanamiento unilateral (Fases legales)" else "🤝 Rango Definitivo Pactado en Preacuerdo"
            st.subheader(titulo_reb)
            st.success(f"**{r_reb_min} a {r_reb_max} meses** ({meses_a_anos_meses(r_reb_min)} a {meses_a_anos_meses(r_reb_max)})")

        res_multa = None
        if aplica_multa:
            st.markdown("---")
            res_multa = calcular_penas_y_cuartos(
                min_multa, max_multa, regla_sel, prop1, prop2, 
                es_tentativa, modalidad_rebaja, fase_allanamiento, rebaja_pactada_pct,
                es_concurso, aumento_concurso_min, aumento_concurso_max,
                tipo_circ_especifica, frac_circ_min, frac_circ_max,
                gen_atenuantes, gen_agravantes,
                modalidad_rebaja, fase_allanamiento, rebaja_pactada_pct
            )
            
            st.header("💰 2. Pena Pecuniaria (Multa - Art. 39)")
            m_base_min, m_base_max = res_multa["rango_base"]
            st.info(f"Límite Multa Marco Base: {m_base_min} SMLMV a {m_base_max} SMLMV")
            
            cols_m = st.columns(2)
            idx_m = 0
            for nombre, (c_min, c_max) in res_multa["cuartos_base"].items():
                with cols_m[idx_m % 2]:
                    st.metric(label=nombre, value=f"{c_min} - {c_max} SMLMV")
                idx_m += 1
                
            if modalidad_rebaja != "Ninguna":
                m_reb_min, m_reb_max = res_multa["rango_rebajado"]
                min_cop = m_reb_min * valor_smlmv
                max_cop = m_reb_max * valor_smlmv
                st.success(f"📉 Multa Definitiva Rebajada: **{m_reb_min} a {m_reb_max} SMLMV** (Equivalente: ${min_cop:,.2f} - ${max_cop:,.2f})")
            else:
                min_cop = m_base_min * valor_smlmv
                max_cop = m_base_max * valor_smlmv
                st.caption(f"💵 Equivalente en COP (${valor_smlmv:,.2f} por SMLMV): ${min_cop:,.2f} hasta ${max_cop:,.2f}")

        st.markdown("---")
        st.subheader("📑 Resumen para Memoriales / Informes")
        
        texto_etapa_reporte = f"{fase_allanamiento}" if modalidad_rebaja == "Allanamiento unilateral (Fases legales)" else (f"Preacuerdo pactado del {rebaja_pactada_pct}%" if modalidad_rebaja == "Preacuerdo pactado (Porcentaje negociado)" else "Juicio Ordinario (Sin rebaja)")

        r_final_min, r_final_max = res_prision["rango_rebajado"] if modalidad_rebaja != "Ninguna" else res_prision["rango_base"]

        texto_reporte = f"""INFORME DE DOSIFICACIÓN Y PRESCRIPCIÓN
Fecha del hecho: {fecha_hecho.strftime('%d/%m/%Y')}
Normativa aplicable: Código Penal (Ley 599 de 2000) y Código de Procedimiento Penal (Ley 906 de 2004)

CONTROL DE PRESCRIPCIÓN (Extinción de la Acción Penal - Art. 292 Ley 906 / Art. 86 C.P.):
- Término prescriptivo inicial: {res_presc['anos_termino']} años.
- ¿Hubo formulación de imputación?: {'SÍ (' + fecha_imputacion.strftime('%d/%m/%Y') + ' - Nuevo término por la mitad del máximo: ' + str(res_presc['anos_interrupcion']) + ' años)' if hubo_imputacion else 'NO'}
- FECHA FATÍDICA DE EXTINCIÓN DE LA ACCIÓN PENAL: {res_presc['fecha_final'].strftime('%d/%m/%Y')}

1. PENA PRIVATIVA DE LA LIBERTAD (PRISIÓN):
- Modalidad de terminación / defensa: {modalidad_rebaja}
- Detalle de la etapa / rebaja aplicada: {texto_etapa_reporte}
- Marco punitivo base de movilidad (Cuartos punitivos): {res_prision['rango_base'][0]} a {res_prision['rango_base'][1]} meses.
- Rango o pena definitiva aplicable: {r_final_min} a {r_final_max} meses ({meses_a_anos_meses(r_final_min)} a {meses_a_anos_meses(r_final_max)}).
"""
        if modalidad_rebaja != "Ninguna":
            texto_reporte += f"- Nota: Se calcularon los cuartos punitivos de movilidad y la rebaja por terminación anticipada ({modalidad_rebaja}) se aplicó sobre ambos extremos (mínimo y máximo) conforme a la jurisprudencia de la Sala Penal de la CSJ.\n"
        else:
            texto_reporte += f"- Sistema de Cuartos Punitivos (Art. 61):\n"
            for nombre, (c_min, c_max) in res_prision["cuartos_base"].items():
                texto_reporte += f"  * {nombre}: {c_min} a {c_max} meses ({meses_a_anos_meses(c_min)} a {meses_a_anos_meses(c_max)})\n"
            
        if aplica_multa and res_multa:
            m_fin_min, m_fin_max = res_multa["rango_rebajado"] if modalidad_rebaja != "Ninguna" else res_multa["rango_base"]
            texto_reporte += f"""
2. PENA PECUNIARIA (MULTA - Art. 39):
- Rango de multa aplicable: {m_fin_min} SMLMV a {m_fin_max} SMLMV.
"""

        st.text_area("Copia este texto para tus documentos:", value=texto_reporte, height=280)
