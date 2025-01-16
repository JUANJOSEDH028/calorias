import streamlit as st
import pandas as pd
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from datetime import datetime
import os
import json
import tempfile

# Ruta del archivo de alimentos
file_path = "alimentos_limpios.xlsx"
data = pd.read_excel(file_path)

# Autenticación con Google Drive usando PyDrive2
def autenticar_google_drive(usuario):
    credenciales_usuario = f"mycreds_{usuario}.txt"

    # Crear un archivo temporal de client_secrets.json desde st.secrets
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        temp_file.write(json.dumps({
            "web": {
                "client_id": st.secrets["client_secrets"]["web"]["client_id"],
                "client_secret": st.secrets["client_secrets"]["web"]["client_secret"],
                "auth_uri": st.secrets["client_secrets"]["web"]["auth_uri"],
                "token_uri": st.secrets["client_secrets"]["web"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["client_secrets"]["web"]["auth_provider_x509_cert_url"],
                "redirect_uris": st.secrets["client_secrets"]["web"]["redirect_uris"]
            }
        }).encode("utf-8"))
        client_secrets_path = temp_file.name

    # Autenticación con Google Drive
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(client_secrets_path)

    if not os.path.exists(credenciales_usuario):
        gauth.LocalWebserverAuth()  # Abre el navegador para autenticación
        gauth.SaveCredentialsFile(credenciales_usuario)
    else:
        gauth.LoadCredentialsFile(credenciales_usuario)

    return GoogleDrive(gauth)

# Subir archivo de un usuario específico
def subir_a_google_drive_usuario(usuario):
    archivo = f"historial_consumo_{usuario}.csv"
    drive = autenticar_google_drive(usuario)

    if os.path.exists(archivo):
        file_drive = drive.CreateFile({'title': archivo})
        file_drive.SetContentFile(archivo)
        file_drive.Upload()
        st.success(f"Archivo '{archivo}' subido a Google Drive con éxito.")
    else:
        st.error("No se encontró el archivo para subir.")

# Descargar archivo de un usuario específico
def descargar_desde_google_drive_usuario(usuario):
    archivo = f"historial_consumo_{usuario}.csv"
    drive = autenticar_google_drive(usuario)
    file_list = drive.ListFile({'q': f"title='{archivo}'"}).GetList()

    if file_list:
        file_drive = file_list[0]
        file_drive.GetContentFile(archivo)
        st.success(f"Archivo '{archivo}' descargado desde Google Drive.")
    else:
        st.warning(f"No se encontró un archivo en Google Drive con el nombre '{archivo}'.")

# Función para manejar el inicio de sesión y archivos
def gestionar_usuario():
    st.sidebar.header("Inicio de Sesión")
    usuario = st.sidebar.text_input("Introduce tu correo electrónico:")
    if st.sidebar.button("Iniciar Sesión"):
        descargar_desde_google_drive_usuario(usuario)
        st.session_state["usuario"] = usuario
        st.sidebar.success(f"Sesión iniciada para {usuario}.")
    return st.session_state.get("usuario")

# Registrar alimentos para un usuario específico
def registrar_alimentos(usuario):
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

        archivo = f"historial_consumo_{usuario}.csv"
        if os.path.exists(archivo):
            historial = pd.read_csv(archivo)
            historial = pd.concat([historial, registro], ignore_index=True)
        else:
            historial = registro

        historial.to_csv(archivo, index=False)
        st.success("Registro guardado con éxito.")

# Mostrar resumen diario para un usuario específico
def mostrar_resumen(usuario):
    st.header("Resumen Diario")
    archivo = f"historial_consumo_{usuario}.csv"
    if os.path.exists(archivo):
        historial = pd.read_csv(archivo)
        resumen = historial[["Calorías", "Grasas (g)", "Proteínas (g)", "Carbohidratos (g)"]].sum()
        st.table(resumen)
    else:
        st.info("No hay registros en el historial.")

# Inicializar sesión de usuario
usuario_actual = gestionar_usuario()

if usuario_actual:
    opcion = st.sidebar.radio("Selecciona una opción:", ["Registrar Alimentos", "Resumen Diario", "Subir a Google Drive", "Cerrar Día"])

    if opcion == "Registrar Alimentos":
        registrar_alimentos(usuario_actual)
    elif opcion == "Resumen Diario":
        mostrar_resumen(usuario_actual)
    elif opcion == "Subir a Google Drive":
        subir_a_google_drive_usuario(usuario_actual)




