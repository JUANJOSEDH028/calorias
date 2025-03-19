import streamlit as st
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
import os
import json
import matplotlib.pyplot as plt

# Configuración de constantes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

@st.cache_data
def load_food_data():
    """Carga y limpia el dataset de alimentos."""
    file_path = "https://github.com/JUANJOSEDH028/calorias/raw/main/colombia.csv"
    data = pd.read_csv(file_path, sep=';')
    
    # Renombrar y limpiar datos
    data.rename(columns={
        "Gramos por Porciуn": "Grams per Portion",
        "Calorнas por Porciуn": "Calories",
        "Proteнna (g)": "Protein (g)"
    }, inplace=True)
    
    # Manejar valores faltantes
    data['Protein (g)'] = data['Protein (g)'].fillna(0)
    return data

class NutritionTracker:
    def __init__(self):
        """Inicializa el tracker con los datos de alimentos."""
        self.data = load_food_data()
        self.user_data = None

    def get_drive_service(self, usuario):
        """Configura y retorna el servicio de Google Drive."""
        try:
            if not st.session_state.get('is_authenticated', False):
                client_config = {
                    'web': {
                        'client_id': st.secrets["client_secrets"]["web"]["client_id"],
                        'project_id': st.secrets["client_secrets"]["web"]["project_id"],
                        'auth_uri': st.secrets["client_secrets"]["web"]["auth_uri"],
                        'token_uri': st.secrets["client_secrets"]["web"]["token_uri"],
                        'auth_provider_x509_cert_url': st.secrets["client_secrets"]["web"]["auth_provider_x509_cert_url"],
                        'client_secret': st.secrets["client_secrets"]["web"]["client_secret"],
                        'redirect_uris': [st.secrets["client_secrets"]["web"]["redirect_uris"][-1]]
                    }
                }

                flow = Flow.from_client_config(
                    client_config,
                    SCOPES
                )
                flow.redirect_uri = st.secrets["client_secrets"]["web"]["redirect_uris"][-1]

                auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
                st.markdown(f"[Haz clic aquí para autorizar]({auth_url})")

                code = st.query_params.get('code')
                if code:
                    try:
                        if isinstance(code, list):
                            code = code[0]
                        flow.fetch_token(code=code)
                        st.session_state['token'] = flow.credentials.to_json()
                        st.session_state['is_authenticated'] = True
                        st.success("¡Autorización exitosa!")
                    except Exception as e:
                        st.error(f"Error al procesar el código de autorización: {str(e)}")
                else:
                    st.error("No se recibió un código de autorización válido.")
                return None

            creds = Credentials.from_authorized_user_info(
                json.loads(st.session_state['token']),
                SCOPES
            )
            return build('drive', 'v3', credentials=creds)

        except Exception as e:
            st.error(f"Error en la autenticación: {str(e)}")
            return None

    def upload_to_drive(self, usuario, content, filename):
        """Sube contenido a Google Drive."""
        try:
            service = self.get_drive_service(usuario)
            if not service:
                return False

            with open(filename, 'w') as f:
                f.write(content)

            file_metadata = {'name': filename}
            media = MediaFileUpload(filename, resumable=True)

            results = service.files().list(
                q=f"name='{filename}' and trashed=false",
                fields="files(id)"
            ).execute()
            existing_files = results.get('files', [])

            if existing_files:
                file = service.files().update(
                    fileId=existing_files[0]['id'],
                    body=file_metadata,
                    media_body=media
                ).execute()
            else:
                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            os.remove(filename)
            return True

        except Exception as e:
            st.error(f"Error al subir archivo: {str(e)}")
            return False

    def calculate_bmr(self, weight, height, age, gender):
        """Calcula la tasa metabólica basal usando Mifflin-St Jeor."""
        if gender == "Masculino":
            return 10 * weight + 6.25 * height - 5 * age + 5
        else:
            return 10 * weight + 6.25 * height - 5 * age - 161

    def save_user_profile(self, usuario, profile_data):
        """Guarda el perfil del usuario en Google Drive."""
        filename = f"user_profile_{usuario}.json"
        return self.upload_to_drive(
            usuario,
            json.dumps(profile_data),
            filename
        )

    def load_user_profile(self, usuario):
        """Carga el perfil del usuario desde Google Drive."""
        try:
            service = self.get_drive_service(usuario)
            if not service:
                return None

            filename = f"user_profile_{usuario}.json"
            results = service.files().list(
                q=f"name='{filename}' and trashed=false",
                fields="files(id)"
            ).execute()
            
            if results.get('files', []):
                file_id = results['files'][0]['id']
                request = service.files().get_media(fileId=file_id)
                file_content = request.execute().decode('utf-8')
                return json.loads(file_content)
                
            return None
        except Exception as e:
            st.error(f"Error al cargar perfil: {str(e)}")
            return None

    def register_food(self, usuario, alimento_nombre, cantidad):
        """Registra un alimento consumido."""
        try:
            if self.data.empty:
                st.error("No se han cargado los datos de alimentos")
                return False

            alimento = self.data[self.data["Alimento"] == alimento_nombre].iloc[0]
            valores = alimento[["Calories", "Protein (g)"]] * (cantidad / alimento["Grams per Portion"])

            nuevo_registro = pd.DataFrame({
                'Fecha y Hora': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                'Alimento': [alimento_nombre],
                'Cantidad (g)': [cantidad],
                'Calorías': [valores["Calories"]],
                'Proteínas (g)': [valores["Protein (g)"]]
            })

            if 'historial' not in st.session_state:
                st.session_state.historial = nuevo_registro
            else:
                st.session_state.historial = pd.concat(
                    [st.session_state.historial, nuevo_registro],
                    ignore_index=True
                )

            filename = f"historial_consumo_{usuario}.csv"
            return self.upload_to_drive(
                usuario,
                st.session_state.historial.to_csv(index=False),
                filename
            )

        except Exception as e:
            st.error(f"Error al registrar alimento: {str(e)}")
            return False

    def get_daily_summary(self):
        """Obtiene el resumen diario de nutrición."""
        if 'historial' in st.session_state and not st.session_state.historial.empty:
            return st.session_state.historial[
                ["Calorías", "Proteínas (g)"]
            ].sum()
        return None

    def get_progress_chart(self):
        """Genera gráfico de progreso nutricional."""
        if 'historial' in st.session_state and not st.session_state.historial.empty:
            fig, ax = plt.subplots()
            st.session_state.historial['Fecha y Hora'] = pd.to_datetime(st.session_state.historial['Fecha y Hora'])
            daily = st.session_state.historial.groupby(
                st.session_state.historial['Fecha y Hora'].dt.date
            )[['Calorías', 'Proteínas (g)']].sum()
            
            daily.plot(kind='line', ax=ax)
            plt.title("Progreso Diario")
            plt.xlabel("Fecha")
            plt.ylabel("Valores")
            st.pyplot(fig)

def main():
    st.title("📊 Seguimiento Nutricional Avanzado")
    
    # Aumentar la duración de la sesión - Configuración previa al inicio
    if not st.session_state.get('_is_session_initialized', False):
        # Configura el tiempo de expiración de la sesión (en segundos)
        # 24 horas = 86400 segundos
        st.session_state['_session_expiry'] = 86400
        st.session_state['_is_session_initialized'] = True

    if 'tracker' not in st.session_state:
        st.session_state.tracker = NutritionTracker()

    if 'is_authenticated' not in st.session_state:
        st.session_state['is_authenticated'] = False

    # Autenticación y perfil de usuario
    st.sidebar.header("👤 Perfil de Usuario")
    usuario = st.sidebar.text_input("Email:", key="user_email")
    
    if not usuario:
        st.warning("⚠️ Por favor, ingresa tu email para comenzar.")
        return

    # Cargar historial previo al inicio de la aplicación
    if usuario and 'historial' not in st.session_state:
        try:
            service = st.session_state.tracker.get_drive_service(usuario)
            if service:
                filename = f"historial_consumo_{usuario}.csv"
                results = service.files().list(
                    q=f"name='{filename}' and trashed=false",
                    fields="files(id)"
                ).execute()
                
                if results.get('files', []):
                    file_id = results['files'][0]['id']
                    request = service.files().get_media(fileId=file_id)
                    file_content = request.execute().decode('utf-8')
                    
                    # Guardar en un archivo temporal para leerlo con pandas
                    with open('temp_historial.csv', 'w') as f:
                        f.write(file_content)
                    
                    st.session_state.historial = pd.read_csv('temp_historial.csv')
                    os.remove('temp_historial.csv')
        except Exception as e:
            st.error(f"Error al cargar historial previo: {str(e)}")
            st.session_state.historial = pd.DataFrame()

    # Cargar o crear perfil
    if 'user_profile' not in st.session_state:
        profile = st.session_state.tracker.load_user_profile(usuario)
        if profile:
            st.session_state.user_profile = profile
        else:
            st.session_state.user_profile = {}

    # Sección de configuración de perfil
    with st.sidebar.expander("⚙️ Configuración de Perfil"):
        weight = st.number_input("Peso (kg):", min_value=30.0, value=float(st.session_state.user_profile.get('weight', 70.0)))
        height = st.number_input("Altura (cm):", min_value=100.0, value=float(st.session_state.user_profile.get('height', 170.0)))
        age = st.number_input("Edad:", min_value=1, value=int(st.session_state.user_profile.get('age', 30)))
        gender = st.selectbox("Sexo:", ["Masculino", "Femenino"], index=0 if st.session_state.user_profile.get('gender') == "Masculino" else 1)
        activity_level = st.selectbox("Nivel de Actividad:", [
            "Sedentario",
            "Ligero",
            "Moderado",
            "Intenso",
            "Muy intenso"
        ], index=0)
        
        if st.button("💾 Guardar Perfil"):
            st.session_state.user_profile = {
                'weight': weight,
                'height': height,
                'age': age,
                'gender': gender,
                'activity_level': activity_level
            }
            if st.session_state.tracker.save_user_profile(usuario, st.session_state.user_profile):
                st.success("Perfil guardado correctamente")

    # Cálculo de requerimientos
    if st.session_state.user_profile:
        bmr = st.session_state.tracker.calculate_bmr(
            st.session_state.user_profile['weight'],
            st.session_state.user_profile['height'],
            st.session_state.user_profile['age'],
            st.session_state.user_profile['gender']
        )
        
        activity_factors = {
            "Sedentario": 1.2,
            "Ligero": 1.375,
            "Moderado": 1.55,
            "Intenso": 1.725,
            "Muy intenso": 1.9
        }
        
        tdee = bmr * activity_factors[st.session_state.user_profile['activity_level']]
        st.sidebar.markdown(f"**🔥 Calorías Diarias Estimadas:** {tdee:.0f} kcal")

    # Menú principal
    menu = st.sidebar.selectbox(
        "📋 Menú:",
        ["Registrar Alimentos", "Resumen Diario", "Progreso"]
    )

    if menu == "Registrar Alimentos":
        st.header("🍽️ Registro de Alimentos")

        col1, col2 = st.columns(2)
        with col1:
            # CORRECCIÓN: Usar la columna "Alimento" en lugar de "Grams per Portion"
            alimento = st.selectbox(
                "Alimento:",
                st.session_state.tracker.data["Alimento"].tolist() if not st.session_state.tracker.data.empty else []
            )
        with col2:
            cantidad = st.number_input("Cantidad (g):", min_value=1.0, step=1.0)

        if st.button("📝 Registrar"):
            if st.session_state.tracker.register_food(usuario, alimento, cantidad):
                st.success("✅ Alimento registrado correctamente")

    elif menu == "Resumen Diario":
        st.header("📈 Resumen del Día")
        resumen = st.session_state.tracker.get_daily_summary()

        if resumen is not None:
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Calorías",
                    f"{resumen['Calorías']:.1f} kcal",
                    f"{resumen['Calorías'] - tdee:.1f} kcal"
                )

            with col2:
                st.metric(
                    "Proteínas",
                    f"{resumen['Proteínas (g)']:.1f} g",
                    f"{resumen['Proteínas (g)'] - (tdee * 0.15 / 4):.1f} g"
                )

            st.table(resumen)
        else:
            st.info("📝 No hay registros para hoy")

    elif menu == "Progreso":
        st.header("📈 Progreso y Análisis")
        st.session_state.tracker.get_progress_chart()
        
        if st.session_state.user_profile and 'historial' in st.session_state:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Peso Actual", f"{st.session_state.user_profile['weight']} kg")
            with col2:
                st.metric("IMC", f"{(st.session_state.user_profile['weight'] / (st.session_state.user_profile['height']/100)**2):.1f}")
            with col3:
                st.metric("Requerimiento Calórico", f"{tdee:.0f} kcal")

if __name__ == "__main__":
    main()
