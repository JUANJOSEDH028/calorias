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
    file_path = "https://github.com/JUANJOSEDH028/calorias/raw/main/colombia.xlsx"
    data = pd.read_excel(file_path)
    
    # Renombrar y limpiar datos
    data.rename(columns={
        "Gramos por Porción": "Grams per Portion",
        "Calorías por Porción": "Calories",
        "Proteína (g)": "Protein (g)"
    }, inplace=True)
    
    # Manejar valores faltantes
    data['Protein (g)'] = data['Protein (g)'].fillna(0)
    return data

class NutritionTracker:
    def __init__(self):
        self.data = load_food_data()
        self.user_data = None

    # ... (métodos existentes get_drive_service y upload_to_drive)

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
        # ... (método existente actualizado para incluir carbohidratos)

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

    if 'tracker' not in st.session_state:
        st.session_state.tracker = NutritionTracker()

    # Autenticación y perfil de usuario
    st.sidebar.header("👤 Perfil de Usuario")
    usuario = st.sidebar.text_input("Email:", key="user_email")
    
    if not usuario:
        st.warning("⚠️ Por favor, ingresa tu email para comenzar.")
        return

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

    # ... (resto del código existente actualizado con nuevas métricas)

    # Nueva sección de progreso
    if menu == "Progreso":
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
