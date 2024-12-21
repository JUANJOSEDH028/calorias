import streamlit as st
import pandas as pd
import json
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from datetime import datetime
import os

# Ruta del archivo de alimentos (asegúrate de que está en el mismo directorio que este script)
file_path = "alimentos_limpios.xlsx"
data = pd.read_excel(file_path)

# Autenticación con Google Drive
def autenticar_google_drive():
    # Leer los secrets desde Streamlit
    client_secrets_content = {
        "installed": {
            "client_id": st.secrets["client_secrets.installed.client_id"],
            "project_id": st.secrets["client_secrets.installed.project_id"],
            "auth_uri": st.secrets["client_secrets.installed.auth_uri"],
            "token_uri": st.secrets["client_secrets.installed.token_uri"],
            "auth_provider_x509_cert_url": st.secrets["client_secrets.installed.auth_provider_x509_cert_url"],
            "client_secret": st.secrets["client_secrets.installed.client_secret"],
            "redirect_uris": st.secrets["client_secrets.installed.redirect_uris"]
        }
    }

    # Guardar temporalmente el archivo client_secrets.json
    with open("client_secrets.json", "w") as f:
        json.dump(client_secrets_content, f)

    # Configurar PyDrive
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("client_secrets.json")
    gauth.LocalWebserverAuth()  # Abre un navegador para autenticarse
    gauth.SaveCredentialsFile("mycreds.txt")  # Guarda las credenciales
    return GoogleDrive(gauth)

# Subir archivo a Google Drive
def subir_a_google_drive():
    drive = autenticar_google_drive()
    archivo = "historial_consumo.csv"

    if os.path.exists(archivo):
        # Crear y subir el archivo
        file_drive = drive.CreateFile({'title': archivo})
        file_drive.SetContentFile(archivo)
        file_drive.Upload()
        st.success(f"Archivo '{archivo}' subido a Google Drive con éxito.")
    else:
        st.error("No se encontró el archivo para subir.")

# Configuración inicial
st.sidebar.title("Menú")
opcion = st.sidebar.radio("Selecciona una opción:", ["Configurar Objetivos", "Registrar Alimentos", "Resumen Diario", "Subir a Google Drive"])

# Configurar objetivos
def configurar_objetivos():
    st.header("Configuración de Objetivos")
    peso = st.number_input("Peso actual (kg):", min_value=1.0, step=0.1)
    altura = st.number_input("Altura (cm):", min_value=1.0, step=0.1)
    edad = st.number_input("Edad (años):", min_value=1, step=1)
    peso_deseado = st.number_input("Peso deseado (kg):", min_value=1.0, step=0.1)

    if st.button("Calcular Objetivos"):
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

        # Guardar en historial
        if os.path.exists("historial_consumo.csv"):
            historial = pd.read_csv("historial_consumo.csv")
            historial = pd.concat([historial, registro], ignore_index=True)
        else:
            historial = registro

        historial.to_csv("historial_consumo.csv", index=False)
        st.success("Registro guardado con éxito.")

# Mostrar resumen diario
def mostrar_resumen():
    st.header("Resumen Diario")
    if os.path.exists("historial_consumo.csv"):
        historial = pd.read_csv("historial_consumo.csv")
        resumen = historial[["Calorías", "Grasas (g)", "Proteínas (g)", "Carbohidratos (g)"]].sum()
        st.table(resumen)
    else:
        st.info("No hay registros en el historial.")

# Navegación del menú
if opcion == "Configurar Objetivos":
    configurar_objetivos()
elif opcion == "Registrar Alimentos":
    registrar_alimentos()
elif opcion == "Resumen Diario":
    mostrar_resumen()
elif opcion == "Subir a Google Drive":
    subir_a_google_drive()

