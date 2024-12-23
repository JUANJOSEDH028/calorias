import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Ruta del archivo de alimentos
file_path = "alimentos_limpios.xlsx"
data = pd.read_excel(file_path)

# Inicialización de variables en session_state
if "objetivo_proteinas" not in st.session_state:
    st.session_state.objetivo_proteinas = 0
if "limite_calorias" not in st.session_state:
    st.session_state.limite_calorias = 0

# Función para configurar objetivos
def configurar_objetivos():
    st.header("Configuración de Objetivos")
    peso = st.number_input("Peso actual (kg):", min_value=1.0, step=0.1)
    altura = st.number_input("Altura (cm):", min_value=1.0, step=0.1)
    edad = st.number_input("Edad (años):", min_value=1, step=1)
    peso_deseado = st.number_input("Peso deseado (kg):", min_value=1.0, step=0.1)

    if st.button("Calcular Objetivos"):
        st.session_state.objetivo_proteinas = peso * 1.8
        if peso_deseado > peso:
            st.session_state.limite_calorias = peso_deseado * 22 * 1.5 + 500
            st.success(f"Meta diaria de calorías: {st.session_state.limite_calorias:.2f} calorías.")
        elif peso_deseado < peso:
            st.session_state.limite_calorias = 10 * peso + 6.25 * altura - 5 * edad + 5 - 500
            st.success(f"Límite diario de calorías: {st.session_state.limite_calorias:.2f} calorías.")
        else:
            st.session_state.limite_calorias = 10 * peso + 6.25 * altura - 5 * edad + 5
            st.success(f"Requerimiento calórico diario: {st.session_state.limite_calorias:.2f} calorías.")

        st.success(f"Objetivo diario de proteínas: {st.session_state.objetivo_proteinas:.2f} g.")

# Función para mostrar el resumen diario con alertas
def mostrar_resumen():
    st.header("Resumen Diario")
    if os.path.exists("historial_consumo.csv"):
        historial = pd.read_csv("historial_consumo.csv")
        resumen = historial[["Calorías", "Grasas (g)", "Proteínas (g)", "Carbohidratos (g)"]].sum()
        st.table(resumen)

        # Mostrar alertas sobre objetivos
        st.subheader("Alertas de Objetivos")
        if resumen["Calorías"] >= st.session_state.limite_calorias:
            st.warning("¡Has alcanzado o superado tu límite diario de calorías!")
        else:
            st.info(f"Te quedan {st.session_state.limite_calorias - resumen['Calorías']:.2f} calorías antes de alcanzar tu límite.")

        if resumen["Proteínas (g)"] >= st.session_state.objetivo_proteinas:
            st.success("¡Has alcanzado tu objetivo diario de proteínas!")
        else:
            st.info(f"Te faltan {st.session_state.objetivo_proteinas - resumen['Proteínas (g)']:.2f} g de proteínas para alcanzar tu objetivo.")
    else:
        st.info("No hay registros en el historial.")

# Configuración inicial
st.sidebar.title("Menú")
opcion = st.sidebar.radio("Selecciona una opción:", ["Configurar Objetivos", "Registrar Alimentos", "Resumen Diario", "Cerrar Día"])

if opcion == "Configurar Objetivos":
    configurar_objetivos()
elif opcion == "Registrar Alimentos":
    st.header("Registro de Alimentos Consumidos")
    alimento_nombre = st.selectbox("Selecciona un alimento:", data["name"])
    alimento = data[data["name"] == alimento_nombre].iloc[0]
    cantidad = st.number_input("Cantidad consumida (g):", min_value=1.0, step=1.0)

    if st.button("Registrar Alimento"):
        valores = alimento[["Calories", "Fat (g)", "Protein (g)", "Carbohydrate (g)"]] * (cantidad / 100)
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        registro = pd.DataFrame({
            'Fecha y Hora': [fecha_hora],
            'Alimento': [alimento["name"]],
            'Cantidad (g)': [cantidad],
            'Calorías': [valores["Calories"]],
            'Grasas (g)': [valores["Fat (g)"]],
            'Proteínas (g)': [valores["Protein (g)"]],
            'Carbohidratos (g)': [valores["Carbohydrate (g)"]],
        })

        if os.path.exists("historial_consumo.csv"):
            historial = pd.read_csv("historial_consumo.csv")
            historial = pd.concat([historial, registro], ignore_index=True)
        else:
            historial = registro

        historial.to_csv("historial_consumo.csv", index=False)
        st.success("Registro guardado con éxito.")
elif opcion == "Resumen Diario":
    mostrar_resumen()
elif opcion == "Cerrar Día":
    st.header("Cierre del Día")
    if os.path.exists("historial_consumo.csv"):
        historial = pd.read_csv("historial_consumo.csv")
        resumen = historial[["Calorías", "Grasas (g)", "Proteínas (g)", "Carbohidratos (g)"]].sum()
        st.subheader("Resumen del Día")
        st.table(resumen)

        # Guardar historial general
        fecha_cierre = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        historial["Fecha de Cierre"] = fecha_cierre
        if os.path.exists("historial_general.csv"):
            historial_general = pd.read_csv("historial_general.csv")
            historial_general = pd.concat([historial_general, historial], ignore_index=True)
        else:
            historial_general = historial
        historial_general.to_csv("historial_general.csv", index=False)

        # Limpiar el historial diario
        os.remove("historial_consumo.csv")
        st.success("Día cerrado con éxito.")
    else:
        st.info("No hay registros en el historial diario para cerrar el día.")



