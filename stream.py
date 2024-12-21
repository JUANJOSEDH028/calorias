import pandas as pd
import os
from datetime import datetime
import streamlit as st

# Ruta al archivo de datos
#file_path = r"C:\Users\practicantev\juan\alimentos\alimentos_limpios.xlsx"
data = pd.read_excel("alimentos_limpios.xlsx")

# Ruta al archivo de historial
historial_path = "historial_consumo.csv"

# Variables globales
if "objetivo_proteinas" not in st.session_state:
    st.session_state.objetivo_proteinas = 0
if "limite_calorias" not in st.session_state:
    st.session_state.limite_calorias = 0

# Configurar objetivos
def configurar_objetivos():
    st.header("Configuración de Objetivos")
    peso = st.number_input("Peso actual (kg):", min_value=1.0, step=0.1)
    altura = st.number_input("Altura (cm):", min_value=1.0, step=0.1)
    edad = st.number_input("Edad (años):", min_value=1, step=1)
    peso_deseado = st.number_input("Peso deseado (kg):", min_value=1.0, step=0.1)
    
    if st.button("Calcular Objetivos"):
        # Cálculo de proteínas y calorías
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

# Registrar alimentos (actualizado para filtrar por nombre)
def registrar_alimentos():
    st.header("Registro de Alimentos Consumidos")
    
    # Crear una lista desplegable con los nombres de los alimentos
    alimento_nombre = st.selectbox("Selecciona un alimento:", data["name"])
    
    # Encontrar el alimento seleccionado
    alimento = data[data["name"] == alimento_nombre].iloc[0]
    
    # Ingresar la cantidad consumida
    cantidad = st.number_input("Cantidad consumida (g):", min_value=1.0, step=1.0)
    
    if st.button("Registrar Alimento"):
        # Calcular valores nutricionales
        valores = alimento[["Calories", "Fat (g)", "Protein (g)", "Carbohydrate (g)"]] * (cantidad / 100)
        
        # Crear registro con fecha y hora
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
        
        # Guardar en el historial
        if os.path.exists(historial_path):
            historial = pd.read_csv(historial_path)
            historial = pd.concat([historial, registro], ignore_index=True)
        else:
            historial = registro
        
        historial.to_csv(historial_path, index=False)
        st.success("Registro guardado con éxito.")
        mostrar_alertas()

# Mostrar alertas
def mostrar_alertas():
    if os.path.exists(historial_path):
        historial = pd.read_csv(historial_path)
        total_calorias = historial["Calorías"].sum()
        total_proteinas = historial["Proteínas (g)"].sum()
        
        st.warning(f"Te faltan {max(0, st.session_state.objetivo_proteinas - total_proteinas):.2f} g de proteínas.")
        if total_calorias >= st.session_state.limite_calorias:
            st.error("¡Has alcanzado o superado tu límite diario de calorías!")
        else:
            st.info(f"Te quedan {st.session_state.limite_calorias - total_calorias:.2f} calorías.")

# Mostrar resumen
def mostrar_resumen():
    st.header("Resumen Diario")
    if os.path.exists(historial_path):
        historial = pd.read_csv(historial_path)
        resumen = historial[["Calorías", "Grasas (g)", "Proteínas (g)", "Carbohidratos (g)"]].sum()
        st.table(resumen)
    else:
        st.info("No hay registros en el historial.")

# Cerrar el día
def cerrar_dia():
    st.header("Cierre del Día")
    if os.path.exists(historial_path):
        historial = pd.read_csv(historial_path)
        resumen = historial[["Calorías", "Grasas (g)", "Proteínas (g)", "Carbohidratos (g)"]].sum()
        st.write("Resumen del Día:")
        st.table(resumen)
        
        historial.to_csv(f"historial_{datetime.now().strftime('%Y_%m_%d')}.csv", index=False)
        os.remove(historial_path)
        st.success("Historial del día cerrado y guardado.")
    else:
        st.info("No hay registros en el historial.")

# Menú de navegación
st.sidebar.title("Menú")
opcion = st.sidebar.radio("Seleccione una opción:", ["Configurar Objetivos", "Registrar Alimentos", "Resumen Diario", "Cerrar Día"])

if opcion == "Configurar Objetivos":
    configurar_objetivos()
elif opcion == "Registrar Alimentos":
    registrar_alimentos()
elif opcion == "Resumen Diario":
    mostrar_resumen()
elif opcion == "Cerrar Día":
    cerrar_dia()
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def subir_a_google_drive():
    # Autenticación
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Abre el navegador para autenticar
    drive = GoogleDrive(gauth)
    
    # Verifica si el archivo existe
    archivo = 'historial_consumo.csv'
    if os.path.exists(archivo):
        # Crear archivo en Google Drive
        file_drive = drive.CreateFile({'title': archivo})  # Nombre en Drive
        file_drive.SetContentFile(archivo)  # Archivo local
        file_drive.Upload()
        st.success(f"Archivo '{archivo}' subido a Google Drive con éxito.")
    else:
        st.error("No se encontró el archivo para subir.")
