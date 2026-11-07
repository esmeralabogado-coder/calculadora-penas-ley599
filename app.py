import streamlit as st
import datetime

from dateutil.relativedelta import relativedelta


# ==================================================
# FUNCIONES
# ==================================================

def meses_a_texto(meses):
    meses = round(meses, 2)

    anos = int(meses // 12)
    resto = round(meses % 12, 2)

    if anos > 0:
        return f"{anos} años y {resto:.2f} meses"

    return f"{resto:.2f} meses"


def calcular_cuartos(minimo, maximo):

    amplitud = maximo - minimo
    cuarto = amplitud / 4

    return {
        "Primer Cuarto": (
            round(minimo, 2),
            round(minimo + cuarto, 2)
        ),
        "Segundo Cuarto": (
            round(minimo + cuarto, 2),
            round(minimo + cuarto * 2, 2)
        ),
        "Tercer Cuarto": (
            round(minimo + cuarto * 2, 2),
            round(minimo + cuarto * 3, 2)
        ),
        "Cuarto Cuarto": (
            round(minimo + cuarto * 3, 2),
            round(maximo, 2)
        )
    }


def calcular_prescripcion(
    fecha_hecho,
    pena_maxima_meses,
    tentativa=False,
    fecha_imputacion=None
):

    if tentativa:
        pena_maxima_meses *= 0.75

    termino_anos = pena_maxima_meses / 12

    if termino_anos < 5:
        termino_anos = 5

    fecha_inicial = fecha_hecho + relativedelta(
        years=int(termino_anos)
    )

    fecha_final = fecha_inicial

    if fecha_imputacion:

        nuevo_termino = termino_anos / 2

        if nuevo_termino < 3:
            nuevo_termino = 3

        if nuevo_termino > 5:
            nuevo_termino = 5

        fecha_final = fecha_imputacion + relativedelta(
            years=int(nuevo_termino)
        )

    return {
        "termino": round(termino_anos, 2),
        "fecha": fecha_final
    }


# ==================================================
# CATALOGO DELITOS
# ==================================================

DELITOS = {

    "Personalizado":
        (108, 360),

    "Homicidio Simple":
        (153, 450),

    "Homicidio Agravado":
        (400, 600),

    "Porte Ilegal de Armas":
        (108, 216),

    "Estupefacientes":
        (128, 360),

    "Hurto Calificado":
        (72, 216),

    "Extorsión":
        (192, 288),

    "Secuestro":
        (192, 360),

    "Peculado":
        (96, 216),

    "Acceso Carnal Violento":
        (144, 252)
}

# ==================================================
# CONFIGURACION
# ==================================================

st.set_page_config(
    page_title="Calculadora Penal Colombia",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Calculadora Penal Colombiana")
st.caption(
    "Ley 599 de 2000 - Versión Simplificada"
)

# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.header("Parámetros")

fecha_hecho = st.sidebar.date_input(
    "Fecha del Hecho",
    value=datetime.date.today()
)

delito = st.sidebar.selectbox(
    "Delito",
    list(DELITOS.keys())
)

if delito == "Personalizado":

    minimo = st.sidebar.number_input(
        "Pena mínima",
        value=108.0
    )

    maximo = st.sidebar.number_input(
        "Pena máxima",
        value=360.0
    )

else:

    minimo, maximo = DELITOS[delito]

st.sidebar.markdown("---")

tentativa = st.sidebar.checkbox(
    "Tentativa (Art. 27)"
)

concurso = st.sidebar.checkbox(
    "Concurso de Conductas"
)

if concurso:

    incremento = st.sidebar.slider(
        "Aumento Concurso (%)",
        0,
        300,
        50
    )

else:
    incremento = 0

st.sidebar.markdown("---")

atenuantes = st.sidebar.checkbox(
    "Atenuantes Genéricas"
)

agravantes = st.sidebar.checkbox(
    "Agravantes Genéricas"
)

st.sidebar.markdown("---")

aplica_multa = st.sidebar.checkbox(
    "Tiene pena de multa"
)

if aplica_multa:

    multa_min = st.sidebar.number_input(
        "Multa mínima SMLMV",
        value=100.0
    )

    multa_max = st.sidebar.number_input(
        "Multa máxima SMLMV",
        value=1000.0
    )

else:

    multa_min = 0
    multa_max = 0

st.sidebar.markdown("---")

hubo_imputacion = st.sidebar.checkbox(
    "Hubo Imputación"
)

fecha_imputacion = None

if hubo_imputacion:

    fecha_imputacion = st.sidebar.date_input(
        "Fecha Imputación",
        value=datetime.date.today()
    )

# ==================================================
# CALCULAR
# ==================================================

if st.sidebar.button("CALCULAR"):

    min_calc = minimo
    max_calc = maximo

    # Tentativa

    if tentativa:

        min_calc *= 0.50
        max_calc *= 0.75

    # Concurso

    if concurso:

        factor = incremento / 100

        min_calc += min_calc * factor
        max_calc += max_calc * factor

    # Atenuantes

    if atenuantes and not agravantes:

        max_calc *= 0.75

    # Agravantes

    if agravantes and not atenuantes:

        min_calc *= 1.25

    min_calc = round(min_calc, 2)
    max_calc = round(max_calc, 2)

    cuartos = calcular_cuartos(
        min_calc,
        max_calc
    )

    prescripcion = calcular_prescripcion(
        fecha_hecho,
        max_calc,
        tentativa,
        fecha_imputacion
    )

    # ==================================================
    # RESULTADOS
    # ==================================================

    st.header("Resultado")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Pena mínima",
            f"{min_calc} meses"
        )

    with col2:

        st.metric(
            "Pena máxima",
            f"{max_calc} meses"
        )

    st.info(
        f"{meses_a_texto(min_calc)} "
        f"a "
        f"{meses_a_texto(max_calc)}"
    )

    st.subheader("Cuartos punitivos")

    for nombre, valores in cuartos.items():

        st.write(
            f"**{nombre}:** "
            f"{valores[0]} "
            f"a "
            f"{valores[1]} meses"
        )

    st.subheader("Prescripción")

    st.success(
        f"Término: "
        f"{prescripcion['termino']} años"
    )

    st.error(
        f"Fecha de prescripción: "
        f"{prescripcion['fecha'].strftime('%d/%m/%Y')}"
    )

    if aplica_multa:

        st.subheader("Multa")

        st.write(
            f"{multa_min} "
            f"a "
            f"{multa_max} SMLMV"
        )

    st.subheader("Informe")

    informe = f"""
INFORME DE DOSIFICACIÓN PENAL

Delito: {delito}

Fecha del hecho:
{fecha_hecho.strftime('%d/%m/%Y')}

Pena aplicable:

Mínimo:
{min_calc} meses

Máximo:
{max_calc} meses

Equivalencia:

{meses_a_texto(min_calc)}
a
{meses_a_texto(max_calc)}

Prescripción:

{prescripcion['termino']} años

Fecha de prescripción:

{prescripcion['fecha'].strftime('%d/%m/%Y')}

Circunstancias aplicadas:

Tentativa: {'SI' if tentativa else 'NO'}

Concurso: {'SI' if concurso else 'NO'}

Atenuantes: {'SI' if atenuantes else 'NO'}

Agravantes: {'SI' if agravantes else 'NO'}
"""

    st.text_area(
        "Copiar informe",
        informe,
        height=350
    )
