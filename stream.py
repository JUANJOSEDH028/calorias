import os
from datetime import datetime
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import streamlit as st

# Ruta del archivo de datos
#file_path = r"C:\Users\practicantev\juan\alimentos\alimentos_limpios.xlsx"
data = pd.read_excel("alimentos_limpios.csv")

# Ruta del historial
historial_path = "historial_consumo.csv"

# Autenticación con Google Drive
def autenticar_google_drive():
    gauth = GoogleAuth()
    
    # Intentar cargar credenciales guardadas
    gauth.LoadCredentialsFile("mycreds.txt")
    
    if gauth.credentials is None:
        # Si no hay credenciales guardadas, abrir el navegador para autenticar
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Si el token ha expirado, refrescarlo
        gauth.Refresh()
    else:
        # Si las credenciales son válidas, cargarlas
        gauth.Authorize()
    
    # Guardar credenciales para futuras ejecuciones
    gauth.SaveCredentialsFile("mycreds.txt")
    return GoogleDrive(gauth)

# Función para subir archivo a Google Drive
def subir_a_google_drive():
    drive = autenticar_google_drive()
    archivo = 'historial_consumo.csv'
    
    if os.path.exists(archivo):
        file_drive = drive.CreateFile({'title': archivo})  # Nombre del archivo en Drive
        file_drive.SetContentFile(archivo)  # Archivo local
        file_drive.Upload()
        st.success(f"Archivo '{archivo}' subido a Google Drive con éxito.")
    else:
        st.error("No se encontró el archivo para subir.")

# Configurar objetivos
def configurar_objetivos():
    st.header("Configuración de Objetivos")
    peso = st.number_input("Peso actual (kg):", min_value=1.0, step=0.1)
    altura = st.number_input("Altura (cm):", min_value=1.0, step=0.1)
    edad = st.number_input("Edad (años):", min_value=1, step=1)
    peso_deseado = st.number_input("Peso deseado (kg):", min_value=1.0, step=0.1)
    
    if st.button("Calcular Objetivos"):
        # Cálculo de proteínas y calorías
        objetivo_proteinas = peso * 1.8
        if peso_deseado > peso:
            limite_calorias = peso_deseado * 22 * 1.5 + 500
            st.success(f"Meta diaria de calorías: {limite_calorias:.2f} calorías.")
        elif peso_deseado < peso:
            limite_calorias = 10 * peso + 6.25 * altura - 5 * edad + 5 - 500
            st.success(f"Límite diario de calorías: {limite_calorias:.2f} calorías.")
        else:
            limite_calorias = 10 * peso + 6.25 * altura - 5 * edad + 5
            st.success(f"Requerimiento calórico diario: {limite_calorias:.2f} calorías.")
        
        st.success(f"Objetivo diario de proteínas: {objetivo_proteinas:.2f} g.")

# Registrar alimentos
def registrar_alimentos():
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
        
        if os.path.exists(historial_path):
            historial = pd.read_csv(historial_path)
            historial = pd.concat([historial, registro], ignore_index=True)
        else:
            historial = registro
        
        historial.to_csv(historial_path, index=False)
        st.success("Registro guardado con éxito.")

# Resumen diario
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
opcion = st.sidebar.radio("Seleccione una opción:", ["Configurar Objetivos", "Registrar Alimentos", "Resumen Diario", "Cerrar Día", "Subir a Google Drive"])

if opcion == "Configurar Objetivos":
    configurar_objetivos()
elif opcion == "Registrar Alimentos":
    registrar_alimentos()
elif opcion == "Resumen Diario":
    mostrar_resumen()
elif opcion == "Cerrar Día":
    cerrar_dia()
elif opcion == "Subir a Google Drive":
    subir_a_google_drive()

