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
    # Término base inicial: máximo de la pena (o la mitad si es tentativa) llevado a años, mínimo 5 años (Art. 83 C.P.)
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
        # Regla Ley 906 (Art. 292 / Art. 86 C.P.): Inicia un nuevo término igual a la mitad del máximo de la pena, mínimo 3 años (1095 días)
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

    if modalidad_rebaja == "Ninguna":
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

    if modalidad_rebaja == "Allanamiento unilateral (Fases legales)":
        if "imputación" in fase_allanamiento.lower() or "1/2" in fase_allanamiento:
            nuevo_min = nuevo_min * 0.50
            nuevo_max = nuevo_max * 0.50
        elif "preparatoria" in fase_allanamiento.lower() or "1/3" in fase_allanamiento:
            nuevo_min = nuevo_min * (2/3) 
            nuevo_max = max_trabajo * (2/3) if False else nuevo_max * (2/3)
        elif "juicio" in fase_allanamiento.lower() or "1/5" in fase_allanamiento:
            nuevo_min = nuevo_min * (4/5) 
            nuevo_max = nuevo_max * (4/5)
            
    elif modalidad_rebaja == "Preacuerdo pactado (Porcentaje negociado)":
        factor_descuento = (100.0 - rebaja_pactada_pct) / 100.0
        nuevo_min = nuevo_min * factor_descuento
        nuevo_max = nuevo_max * factor_descuento
    
    nuevo_min = max(0.0, nuevo_min)
    nuevo_max = max(0.0, nuevo_max)
    
    amplitud_total = nuevo_max - nuevo_min
    cuarto_tam = amplitud_total / 4.0

    c1 = (round(nuevo_min, 2), round(nuevo_min + cuarto_tam, 2))
    c2 = (round(nuevo_min + cuarto_tam, 2), round(nuevo_min + 2*cuarto_tam, 2))
    c3 = (round(nuevo_min + 2*cuarto_tam, 2), round(nuevo_min + 3*cuarto_tam, 2))
    c4 = (round(nuevo_min + 3*cuarto_tam, 2), round(nuevo_max, 2))

    if modalidad_rebaja != "Ninguna":
        nombre_etiqueta = "Rango Definitivo Rebajado por Allanamiento (Mínimo y Máximo)" if modalidad_rebaja == "Allanamiento unilateral (Fases legales)" else "Pena Fija / Rango Pactado en Preacuerdo"
        cuartos_dict = {
            nombre_etiqueta: (round(nuevo_min, 2), round(nuevo_max, 2))
        }
    else:
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
        if gen_agravantes and not gen_atenuantes and modalidad_rebaja == "Ninguna": 
            notas_ajuste.append("Agravantes Genéricas (Art. 61 - Se excluye 1er cuarto)")
        if gen_atenuantes and not gen_agravantes and modalidad_rebaja == "Ninguna": 
            notas_ajuste.append("Atenuantes Genéricas (Art. 61)")
        if tipo_circ_especifica != "Ninguna": notas_ajuste.append(tipo_circ_especifica)
        if es_tentativa: notas_ajuste.append("Tentativa (Art. 27)")
        if modalidad_rebaja != "Ninguna": 
            detalle_rebaja = fase_allanamiento if modalidad_rebaja == "Allanamiento unilateral (Fases legales)" else f"Preacuerdo del {rebaja_pactada_pct}%"
            notas_ajuste.append(f"Terminación Anticipada: {detalle_rebaja}")
        
        if notas_ajuste:
            st.warning(f"⚠️ Ajustes aplicados: {', '.join(notas_ajuste)}.")
            
        r_min_meses, r_max_meses = res_prision['rango']
        st.info(f"Límite Aplicable: {r_min_meses} - {r_max_meses} meses ({meses_a_anos_meses(r_min_meses)} a {meses_a_anos_meses(r_max_meses)})")
        
        if modalidad_rebaja == "Allanamiento unilateral (Fases legales)":
            titulo_seccion_prision = "📊 Rango Definitivo Rebajado (Mínimo y Máximo afectados por Allanamiento)"
        elif modalidad_rebaja == "Preacuerdo pactado (Porcentaje negociado)":
            titulo_seccion_prision = "📊 Rango Definitivo Pactado en Preacuerdo"
        else:
            titulo_seccion_prision = "📊 Sistema de Cuartos Punitivos (Prisión)"
            
        st.subheader(titulo_seccion_prision)
        
        cols = st.columns(2)
        idx = 0
        for nombre, (c_min, c_max) in res_prision["cuartos"].items():
            with cols[idx % 2]:
                st.metric(label=nombre, value=f"{c_min} - {c_max} m", delta=f"{meses_a_anos_meses(c_min)} a {meses_a_anos_meses(c_max)}")
            idx += 1
            
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
            st.info(f"Límite Multa Aplicable: {res_multa['rango'][0]} SMLMV a {res_multa['rango'][1]} SMLMV")
            
            min_cop = res_multa['rango'][0] * valor_smlmv
            max_cop = res_multa['rango'][1] * valor_smlmv
            st.caption(f"💵 Equivalente aproximado en pesos (COP): ${min_cop:,.2f} hasta ${max_cop:,.2f}")
            
            titulo_seccion_multa = "📊 Rango Definitivo de Multa Rebajada/Pactada" if modalidad_rebaja != "Ninguna" else "📊 Sistema de Cuartos Punitivos (Multa en SMLMV)"
            st.subheader(titulo_seccion_multa)
            
            cols_m = st.columns(2)
            idx_m = 0
            for nombre, (c_min, c_max) in res_multa["cuartos"].items():
                with cols_m[idx_m % 2]:
                    st.metric(label=nombre, value=f"{c_min} - {c_max} SMLMV")
                idx_m += 1

        st.markdown("---")
        st.subheader("📑 Resumen para Memoriales / Informes")
        
        texto_etapa_reporte = f"{fase_allanamiento}" if modalidad_rebaja == "Allanamiento unilateral (Fases legales)" else (f"Preacuerdo pactado del {rebaja_pactada_pct}%" if modalidad_rebaja == "Preacuerdo pactado (Porcentaje negociado)" else "Juicio Ordinario (Sin rebaja)")

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
- Rango o pena aplicable (Mínimo y Máximo rebajados): {res_prision['rango'][0]} a {res_prision['rango'][1]} meses ({meses_a_anos_meses(res_prision['rango'][0])} a {meses_a_anos_meses(res_prision['rango'][1])}).
"""
        if modalidad_rebaja != "Ninguna":
            texto_reporte += f"- Nota: Al tratarse de terminación anticipada ({modalidad_rebaja}), la rebaja se aplica sobre ambos extremos (mínimo y máximo) y no opera el sistema ordinario de cuartos punitivos (Jurisprudencia CSJ).\n"
        else:
            texto_reporte += f"- Sistema de Cuartos Punitivos (Art. 61):\n"
            for nombre, (c_min, c_max) in res_prision["cuartos"].items():
                texto_reporte += f"  * {nombre}: {c_min} a {c_max} meses ({meses_a_anos_meses(c_min)} a {meses_a_anos_meses(c_max)})\n"
            
        if aplica_multa and res_multa:
            texto_reporte += f"""
2. PENA PECUNIARIA (MULTA - Art. 39):
- Rango de multa aplicable: {res_multa['rango'][0]} SMLMV a {res_multa['rango'][1]} SMLMV.
- Equivalente en COP (${valor_smlmv:,.2f} por SMLMV): ${min_cop:,.2f} hasta ${max_cop:,.2f}.
"""

        st.text_area("Copia este texto para tus documentos:", value=texto_reporte, height=280)
