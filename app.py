# ==============================================================
# DƏSTƏK KİTABXANALARI (Libraries)
# ==============================================================

import streamlit as st  # Veb interfeys qurmaq üçün (düymələr, yazı qutuları, sidebar)
from huggingface_hub import InferenceClient  # Hugging Face modellərini pulsuz çağırmaq üçün
import datetime  # Hər söhbətin vaxtını yadda saxlamaq üçün

# ==============================================================
# SƏHİFƏNİN ƏSAS QURULUŞU (Page Config) - ilk əmr olmalıdır
# ==============================================================
st.set_page_config(
    page_title="Dragon-X AI",  # Brauzerin tabında görünən başlıq
    page_icon="🐉",             # Tabın yanında kiçik ikon
    layout="wide"              # Geniş ekran rejimi (rahat görünüş)
)

# ==============================================================
# SÖHBƏT TARİXÇƏSİNİ SAXLAMAQ ÜÇÜN YADDAŞ (Session State)
# ==============================================================
# st.session_state - istifadəçi səhifəni yeniləsə belə məlumatları unutmayan "sehrli qutu"
if "messages" not in st.session_state:
    # Əgər hələ heç bir mesaj yoxdursa, boş siyahı yarat
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    # Bütün köhnə söhbətlərin siyahısı: hər söhbət {ad, mesajlar, vaxt, model}
    st.session_state.chat_history = []

if "current_chat_id" not in st.session_state:
    # Hazırda hansı söhbətin açıq olduğunu saxlamaq üçün unikal ID (vaxta görə)
    st.session_state.current_chat_id = None

if "model_name" not in st.session_state:
    # Standart olaraq DeepSeek modelini seçək (pulsuz, güclü)
    st.session_state.model_name = "deepseek-ai/DeepSeek-R1-Distill-Llama-8B"

# ==============================================================
# KÖMƏKÇİ FONKSİYALAR (Helper Functions)
# ==============================================================

def get_model_client():
    """Hazırda seçilmiş model üçün Hugging Face InferenceClient qaytarır"""
    # InferenceClient heç bir API açarı tələb etmir - tamamilə pulsuz!
    # Amma limitsiz deyil: dəqiqədə təxminən 30-40 sorğu edə bilərsən
    return InferenceClient(model=st.session_state.model_name)

def chat_with_ai(user_message):
    """
    İstifadəçinin mesajını seçilmiş modele göndər, cavabı al.
    Burada bütün əvvəlki mesajları yaddaş kimi göndəririk.
    """
    client = get_model_client()
    
    # Söhbət yaddaşını qur: bütün keçmiş mesajlar (sistem, user, assistant)
    # "role" = "user" (istifadəçi) və ya "assistant" (bot)
    messages_for_model = []
    
    # Sistem mesajı: botun necə davranacağını təyin edir
    messages_for_model.append({
        "role": "system",
        "content": "Sən Dragon-X AI adlı güclü və dost bir köməkçisən. Azərbaycan dilində cavab verirsən. Əvvəlki söhbəti unutma, yadda saxla."
    })
    
    # Bütün keçmiş mesajları yaddaşdan əlavə et (əgər hazırkı söhbətdə varsa)
    if st.session_state.messages:
        messages_for_model.extend(st.session_state.messages)
    
    # İndiki istifadəçi mesajını əlavə et
    messages_for_model.append({
        "role": "user",
        "content": user_message
    })
    
    # Modelə sorğu göndər
    try:
        response = client.chat_completion(
            messages=messages_for_model,
            max_tokens=1024,   # Cavabın uzunluğu (nə qədər çox olsa, bir o qədər yavaş)
            temperature=0.7    # Yaradıcılıq səviyyəsi (0=soyuq, 1=dəlisov)
        )
        # Cavabın içindən yalnız mətni çıxar
        return response.choices[0].message.content
    except Exception as e:
        # Xəta olarsa istifadəçiyə bildir (model bəzən yüklənir)
        return f"❌ Xəta baş verdi: {str(e)}. Bir az sonra yenə cəhd et."

def save_current_chat():
    """Hazırkı söhbəti chat_history siyahısına yadda saxla"""
    if st.session_state.messages and st.session_state.current_chat_id:
        # Həmin ID ilə söhbət varsa, onu yenilə
        for i, chat in enumerate(st.session_state.chat_history):
            if chat["id"] == st.session_state.current_chat_id:
                st.session_state.chat_history[i]["messages"] = st.session_state.messages.copy()
                st.session_state.chat_history[i]["last_updated"] = datetime.datetime.now()
                return
        # Əgər yoxdursa, yeni söhbət kimi əlavə et
        st.session_state.chat_history.append({
            "id": st.session_state.current_chat_id,
            "name": f"Söhbət {len(st.session_state.chat_history)+1}",
            "messages": st.session_state.messages.copy(),
            "created": datetime.datetime.now(),
            "last_updated": datetime.datetime.now(),
            "model": st.session_state.model_name
        })

def load_chat(chat_id):
    """Köhnə söhbəti yaddaşdan götür və ekranda göstər"""
    for chat in st.session_state.chat_history:
        if chat["id"] == chat_id:
            st.session_state.messages = chat["messages"].copy()
            st.session_state.current_chat_id = chat_id
            st.session_state.model_name = chat.get("model", st.session_state.model_name)
            break

def new_chat():
    """Yeni boş söhbət yarat"""
    st.session_state.messages = []
    st.session_state.current_chat_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    save_current_chat()  # Boş da olsa, zaman damğası ilə qeydə al

# ==============================================================
# SIDEBAR (SOL PANEL) - Yeni Çat, Çat Tarixçəsi, Model seçimi
# ==============================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/5969/5969141.png", width=50)  # Dragon ikonu (əvəz edə bilərsən)
    st.title("🐉 Dragon-X AI")
    
    # 1. Yeni Çat düyməsi
    if st.button("➕ Yeni Çat", use_container_width=True):
        new_chat()
        st.rerun()  # Səhifəni yenilə ki, yeni boş söhbət görünsün
    
    st.divider()
    
    # 2. Model seçimi (iki pulsuz model arasında keçid)
    selected_model = st.selectbox(
        "🤖 Model seç:",
        options=["deepseek-ai/DeepSeek-R1-Distill-Llama-8B", "meta-llama/Meta-Llama-3-8B-Instruct"],
        format_func=lambda x: "DeepSeek-R1" if "deepseek" in x else "Llama 3",
        index=0
    )
    if selected_model != st.session_state.model_name:
        st.session_state.model_name = selected_model
        # Model dəyişəndə xəbərdarlıq et (yaddaş qalır)
        st.info(f"Model dəyişdirildi: {'DeepSeek' if 'deepseek' in selected_model else 'Llama 3'}")
        st.rerun()
    
    st.divider()
    st.subheader("📜 Çat Tarixçəsi")
    
    # Əvvəlcə hazırkı söhbəti yadda saxla (əgər mesajlar varsa)
    if st.session_state.messages and st.session_state.current_chat_id:
        save_current_chat()
    
    # Bütün köhnə söhbətləri sol paneldə göstər
    if st.session_state.chat_history:
        for chat in reversed(st.session_state.chat_history):  # Ən yeni yuxarıda
            # Hər söhbət üçün düymə yarat
            if st.button(
                f"💬 {chat['name']} ({chat['last_updated'].strftime('%H:%M')})",
                key=chat["id"],
                use_container_width=True
            ):
                load_chat(chat["id"])
                st.rerun()
    else:
        st.caption("Hələ heç bir söhbət yoxdur. 'Yeni Çat' ilə başla!")

# ==============================================================
# ƏSAS SAHƏ (Main Area) - Söhbət interfeysi
# ==============================================================
st.title("🐉 Dragon-X AI - Sənin Güclü Köməkçin")
st.caption(f"Aktiv model: `{'DeepSeek-R1' if 'deepseek' in st.session_state.model_name else 'Llama 3'}` | Yaddaş aktiv | Pulsuz")

# Bütün keçmiş mesajları ekranda göstər
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# ==============================================================
# YENİ MESAJ GİRİŞİ (Chat Input)
# ==============================================================
if prompt := st.chat_input("Burada mesajını yaz..."):
    # 1. İstifadəçinin mesajını ekrana və yaddaşa əlavə et
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Botun cavabını al (yaddaşlı)
    with st.chat_message("assistant"):
        with st.spinner("Dragon-X düşünür..."):
            response = chat_with_ai(prompt)
            st.markdown(response)
    
    # 3. Botun cavabını yaddaşa əlavə et
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # 4. Söhbəti tarixçəyə yadda saxla
    if st.session_state.current_chat_id is None:
        # Əgər yeni söhbət hələ ID almamışsa, indi ver
        st.session_state.current_chat_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    save_current_chat()
    
    st.rerun()  # Ekranı yenilə ki, yeni mesaj görünsün
