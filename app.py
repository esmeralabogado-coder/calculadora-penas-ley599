import streamlit as st
import datetime

def calcular_penas_y_cuartos(min_basico, max_basico, regla, prop1=0.0, prop2=None, tentativa=False, modalidad_rebaja="Ninguna", fase_allanamiento="", rebaja_pactada_pct=0.0, es_concurso=False, aumento_concurso_min=0.0, aumento_concurso_max=0.0):
    min_trabajo = min_basico
    max_trabajo = max_basico
    
    # 1. Concurso de Delitos (Art. 31 Ley 599)
    if es_concurso:
        min_trabajo = min_basico + (min_basico * aumento_concurso_min)
        max_trabajo = max_basico + (max_basico * aumento_concurso_max)

    # 2. Tentativa (Art. 27 Ley 599)
    if tentativa:
        min_trabajo = min_trabajo * 0.25  
        max_trabajo = max_trabajo * 0.50  

    # 3. Terminación anticipada
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

    # 4. Reglas de modificación (Art. 61)
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
        nuevo_max = max_trabajo - (min_trabajo * menor)
    
    nuevo_min = max(0.0, nuevo_min)
    nuevo_max = max(0.0, nuevo_max)
    
    amplitud_total = nuevo_max - nuevo_min
    cuarto_tam = amplitud_total / 4.0
    
    return {
        "rango": (round(nuevo_min, 2), round(nuevo_max, 2)),
        "cuartos": {
            "Primer cuarto (Mínimo)": (round(nuevo_min, 2), round(nuevo_min + cuarto_tam, 2)),
            "Segundo cuarto (Medio 1)": (round(nuevo_min + cuarto_tam, 2), round(nuevo_min + 2*cuarto_tam, 2)),
            "Tercer cuarto (Medio 2)": (round(nuevo_min + 2*cuarto_tam, 2), round(nuevo_min + 3*cuarto_tam, 2)),
            "Cuarto cuarto (Máximo)": (round(nuevo_min + 3*cuarto_tam, 2), round(nuevo_max, 2)),
        }
    }

st.set_page_config(page_title="Individualización de Penas", page_icon="⚖️")

st.title("⚖️ Calculadora Integral de Penas y Cuartos Punitivos")
st.caption("Conforme al Código Penal Colombiano (Ley 599 de 2000) y Ley 906 de 2004")

st.sidebar.header("📋 Parámetros del Caso")

fecha_hecho = st.sidebar.date_input("Fecha del hecho delictivo", value=datetime.date(2026, 1, 1))
aplica_multa = st.sidebar.checkbox("¿El tipo penal incluye pena de multa? (Art. 39)")

st.sidebar.subheader("🔒 Prisión (Delito Mayor)")
min_basico = st.sidebar.number_input("Pena Mínima Básica (meses)", min_value=0.0, value=108.0, step=1.0)
max_basico = st.sidebar.number_input("Pena Máxima Básica (meses)", min_value=0.0, value=360.0, step=1.0)

st.sidebar.subheader("🔗 Concurso de Delitos (Art. 31)")
es_concurso = st.sidebar.checkbox("¿Hay concurso de delitos?")
aumento_concurso_min, aumento_concurso_max = 0.0, 0.0
if es_concurso:
    aumento_concurso_min = st.sidebar.number_input("Fracción incremento mín (ej: 0.5)", min_value=0.0, value=0.0, step=0.1)
    aumento_concurso_max = st.sidebar.number_input("Fracción incremento máx (ej: 1.0)", min_value=0.0, value=0.0, step=0.1)

min_multa, max_multa = 0.0, 0.0
valor_smlmv = 1423500.0  
if aplica_multa:
    st.sidebar.subheader("💰 Multa (SMLMV)")
    min_multa = st.sidebar.number_input("Multa Mínima Básica (SMLMV)", min_value=0.0, value=133.33, step=10.0)
    max_multa = st.sidebar.number_input("Multa Máxima Básica (SMLMV)", min_value=0.0, value=1500.0, step=10.0)
    valor_smlmv = st.sidebar.number_input("Valor SMLMV (COP)", min_value=0.0, value=1423500.0, step=10000.0)

st.sidebar.subheader("🎯 Fase de Ejecución")
es_tentativa = st.sidebar.checkbox("¿Es conducta tentada? (Art. 27)")

st.sidebar.subheader("🤝 Terminación Anticipada")
modalidad_rebaja = st.sidebar.radio(
    "Modalidad de rebaja:",
    options=["Ninguna", "Allanamiento unilateral (Fases legales)", "Preacuerdo pactado (Porcentaje negociado)"]
)

fase_allanamiento = ""
rebaja_pactada_pct = 0.0

if modalidad_rebaja == "Allanamiento unilateral (Fases legales)":
    fase_allanamiento = st.sidebar.selectbox(
        "Fase Procesal del Allanamiento",
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

st.sidebar.subheader("⚖️ Reglas de Modificación (Art. 61)")
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
    prop1 = st.sidebar.number_input("Proporción (ej: 0.33 para 1/3, 0.5 para 1/2)", min_value=0.0, max_value=1.0, value=0.3333, step=0.01)
elif regla_sel in [4, 5]:
    prop1 = st.sidebar.number_input("Primera Proporción", min_value=0.0, max_value=1.0, value=0.3333, step=0.01)
    prop2 = st.sidebar.number_input("Segunda Proporción", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

if st.sidebar.button("Calcular individualización"):
    if min_basico > max_basico:
        st.error("El límite mínimo de prisión no puede superar el límite máximo.")
    elif aplica_multa and min_multa > max_multa:
        st.error("El límite mínimo de multa no puede superar el máximo.")
    else:
        st.success(f"📅 **Fecha del hecho delictivo registrada:** {fecha_hecho.strftime('%d/%m/%Y')}")
        
        # --- CÁLCULO PRISIÓN ---
        res_prision = calcular_penas_y_cuartos(
            min_basico, max_basico, regla_sel, prop1, prop2, 
            es_tentativa, modalidad_rebaja, fase_allanamiento, rebaja_pactada_pct,
            es_concurso, aumento_concurso_min, aumento_concurso_max
        )
        
        st.header("🔒 1. Pena Privativa de la Libertad (Prisión)")
        notas_ajuste = []
        if es_concurso: notas_ajuste.append("Concurso de Delitos (Art. 31)")
        if es_tentativa: notas_ajuste.append("Tentativa (Art. 27)")
        if modalidad_rebaja != "Ninguna": notas_ajuste.append(modalidad_rebaja)
        
        if notas_ajuste:
            st.warning(f"⚠️ **Ajustes aplicados:** {', '.join(notas_ajuste)}.")
            
        st.info(f"**Límite Aplicable:** {res_prision['rango'][0]} meses a {res_prision['rango'][1]} meses")
        
        st.subheader("📊 Sistema de Cuartos Punitivos (Prisión)")
        cols = st.columns(2)
        idx = 0
        for nombre, (c_min, c_max) in res_prision["cuartos"].items():
            with cols[idx % 2]:
                st.metric(label=nombre, value=f"{c_min} - {c_max} m")
            idx += 1
            
        # --- CÁLCULO MULTA ---
        res_multa = None
        if aplica_multa:
            st.markdown("---")
            res_multa = calcular_penas_y_cuartos(
                min_multa, max_multa, regla_sel, prop1, prop2, 
                es_tentativa, modalidad_rebaja, fase_allanamiento, rebaja_pactada_pct,
                es_concurso, aumento_concurso_min, aumento_concurso_max
            )
            
            st.header("💰 2. Pena Pecuniaria (Multa - Art. 39)")
            st.info(f"**Límite Multa Aplicable:** {res_multa['rango'][0]} SMLMV a {res_multa['rango'][1]} SMLMV")
            
            min_cop = res_multa['rango'][0] * valor_smlmv
            max_cop = res_multa['rango'][1] * valor_smlmv
            st.caption(f"💵 **Equivalente aproximado en pesos (COP):** ${min_cop:,.2f} hasta ${max_cop:,.2f}")
            
            st.subheader("📊 Sistema de Cuartos Punitivos (Multa en SMLMV)")
            cols_m = st.columns(2)
            idx_m = 0
            for nombre, (c_min, c_max) in res_multa["cuartos"].items():
                with cols_m[idx_m % 2]:
                    st.metric(label=nombre, value=f"{c_min} - {c_max} SMLMV")
                idx_m += 1

        # --- GENERADOR DE INFORME PARA MEMORIALES ---
        st.markdown("---")
        st.subheader("📑 Resumen para Memoriales / Informes")
        
        texto_reporte = f"""INFORME DE DOSIFICACIÓN Y CUARTOS PUNITIVOS
Fecha del hecho: {fecha_hecho.strftime('%d/%m/%Y')}
Normativa aplicable: Código Penal Colombiano (Ley 599 de 2000)

1. PENA PRIVATIVA DE LA LIBERTAD (PRISIÓN):
- Rango de movilidad aplicable: {res_prision['rango'][0]} meses a {res_prision['rango'][1]} meses.
- Sistema de Cuartos Punitivos (Art. 61):
"""
        for nombre, (c_min, c_max) in res_prision["cuartos"].items():
            texto_reporte += f"  * {nombre}: {c_min} a {c_max} meses\n"
            
        if aplica_multa and res_multa:
            texto_reporte += f"""
2. PENA PECUNIARIA (MULTA - Art. 39):
- Rango de multa aplicable: {res_multa['rango'][0]} SMLMV a {res_multa['rango'][1]} SMLMV.
- Equivalente en COP (${valor_smlmv:,.2f} por SMLMV): ${min_cop:,.2f} hasta ${max_cop:,.2f}.
- Cuartos Punitivos (Multa):
"""
            for nombre, (c_min, c_max) in res_multa["cuartos"].items():
                texto_reporte += f"  * {nombre}: {c_min} a {c_max} SMLMV\n"

        st.text_area("Copia este texto para tus documentos:", value=texto_reporte, height=250)
