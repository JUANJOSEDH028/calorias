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

# Autenticación con Google Drive usando flujo manual
def autenticar_google_drive(usuario):
    credenciales_usuario = f"mycreds_{usuario}.txt"

    try:
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

        # Configurar GoogleAuth
        gauth = GoogleAuth()
        gauth.LoadClientConfigFile(client_secrets_path)

        if not os.path.exists(credenciales_usuario):
            st.info("Autenticación manual requerida. Sigue los pasos:")
            auth_url = gauth.GetAuthUrl()  # Generar URL de autenticación
            st.write(f"[Haz clic aquí para autenticarte]({auth_url})")

            # Capturar el código de autenticación
            auth_code = st.text_input("Introduce el código de autenticación aquí:")
            if st.button("Enviar Código"):
                gauth.Auth(auth_code)  # Autenticar usando el código
                gauth.SaveCredentialsFile(credenciales_usuario)
                st.success("Autenticación completada y credenciales guardadas.")
        else:
            gauth.LoadCredentialsFile(credenciales_usuario)
            if gauth.access_token_expired:
                st.info("Token expirado. Renovando...")
                gauth.Refresh()
                gauth.SaveCredentialsFile(credenciales_usuario)
                st.success("Token renovado.")
            else:
                st.success("Autenticación ya realizada.")
        
        return GoogleDrive(gauth)
    
    except Exception as e:
        st.error(f"Error durante la autenticación: {str(e)}")
        return None

# Función de prueba para verificar autenticación
def probar_google_drive(usuario):
    st.header("Probar conexión con Google Drive")
    drive = autenticar_google_drive(usuario)
    if drive:
        st.success("Autenticación exitosa. Probando acceso a Google Drive...")
        # Listar archivos como prueba
        try:
            file_list = drive.ListFile({'q': "trashed=false"}).GetList()
            st.write("Archivos en Google Drive:")
            for file in file_list[:5]:  # Mostrar los primeros 5 archivos
                st.write(f"{file['title']} ({file['id']})")
        except Exception as e:
            st.error(f"No se pudo acceder a Google Drive: {str(e)}")
    else:
        st.error("No se pudo autenticar con Google Drive.")

# Llamar a la función de prueba
usuario_actual = st.sidebar.text_input("Introduce tu correo electrónico:")
if st.sidebar.button("Probar Google Drive"):
    probar_google_drive(usuario_actual)
