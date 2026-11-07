import streamlit as st

def calcular_penas_y_cuartos(min_basico, max_basico, regla, prop1, prop2=None):
    if regla == 1:
        nuevo_min = min_basico + (min_basico * prop1)
        nuevo_max = max_basico + (max_basico * prop1)
    elif regla == 2:
        nuevo_min = min_basico
        nuevo_max = max_basico + (max_basico * prop1)
    elif regla == 3:
        nuevo_min = min_basico - (min_basico * prop1)
        nuevo_max = max_basico
    elif regla == 4:
        menor = min(prop1, prop2)
        mayor = max(prop1, prop2)
        nuevo_min = min_basico + (min_basico * menor)
        nuevo_max = max_basico + (max_basico * mayor)
    elif regla == 5:
        menor = min(prop1, prop2)
        mayor = max(prop1, prop2)
        nuevo_min = min_basico - (min_basico * mayor)
        nuevo_max = max_basico - (max_basico * menor)
    
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

st.title("⚖️ Calculadora de Penas y Cuartos Punitivos")
st.caption("Conforme al Código Penal Colombiano (Ley 599 de 2000)")

st.sidebar.header("Parámetros Punitivos")
min_basico = st.sidebar.number_input("Pena Mínima Básica (meses)", min_value=0.0, value=108.0, step=1.0)
max_basico = st.sidebar.number_input("Pena Máxima Básica (meses)", min_value=0.0, value=360.0, step=1.0)

reglas_dict = {
    1: "1. Aumento/Disminución proporcional al mín y máx",
    2: "2. Aumento hasta en una proporción al máx",
    3: "3. Disminución hasta en una proporción al mín",
    4: "4. Aumento en dos proporciones",
    5: "5. Disminución en dos proporciones"
}

regla_sel = st.sidebar.selectbox("Seleccione la Regla", options=list(reglas_dict.keys()), format_func=lambda x: reglas_dict[x])

prop1 = st.sidebar.number_input("Primera Proporción (ej. 0.5 para 1/2, 0.3333 para 1/3)", min_value=0.0, max_value=1.0, value=0.3333, step=0.01)

prop2 = 0.0
if regla_sel in [4, 5]:
    prop2 = st.sidebar.number_input("Segunda Proporción", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

if st.sidebar.button("Calcular individualización"):
    if min_basico > max_basico:
        st.error("El límite mínimo no puede superar el límite máximo.")
    else:
        res = calcular_penas_y_cuartos(min_basico, max_basico, regla_sel, prop1, prop2)
        
        st.subheader("📌 Rango de Pena Modificado")
        st.info(f"**Nuevo Límite:** {res['rango'][0]} meses a {res['rango'][1]} meses")
        
        st.subheader("📊 Sistema de Cuartos Punitivos (Art. 61)")
        
        cols = st.columns(2)
        idx = 0
        for nombre, (c_min, c_max) in res["cuartos"].items():
            with cols[idx % 2]:
                st.metric(label=nombre, value=f"{c_min} - {c_max} m")
            idx += 1
