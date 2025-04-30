import streamlit as st
import os
import numpy as np
import pandas as pd
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from verify import send_otp_with_verify, check_otp  # OTP functions

# ========== Create Encoder using MobileNetV2 ==========
def create_encoder():
    base_model = MobileNetV2(include_top=False, input_shape=(160, 160, 3), weights='imagenet')
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    encoder = Model(inputs=base_model.input, outputs=x)
    return encoder

encoder = create_encoder()

# ========== Preprocess image for MobileNetV2 ==========
def preprocess_image(img_path):
    img = Image.open(img_path).convert('RGB')
    img = img.resize((160, 160))
    img = np.array(img)
    img = preprocess_input(img)
    return img

# ========== Compare new signature with stored ones ==========
def compute_similarity(new_img_path, user_folder):
    new_img = preprocess_image(new_img_path)
    new_img = np.expand_dims(new_img, axis=0)
    new_features = encoder.predict(new_img)

    similarities = []
    for file in os.listdir(user_folder):
        reg_img = preprocess_image(os.path.join(user_folder, file))
        reg_img = np.expand_dims(reg_img, axis=0)
        reg_features = encoder.predict(reg_img)

        l1_distance = np.mean(np.abs(new_features - reg_features))
        similarity = 1 - l1_distance
        similarities.append(similarity)

    avg_similarity = np.mean(similarities)
    return avg_similarity

# ========== Retrieve user phone number ==========
def get_user_phone(user_name):
    df = pd.read_csv('dataset/users.csv')
    user_row = df[df['name'] == user_name]
    if not user_row.empty:
        phone = str(user_row.iloc[0]['phone'])
        return phone if phone.startswith('+') else '+1' + phone  # Adjust country code if needed
    return None

# ========== Streamlit UI ==========
st.set_page_config(page_title="Signature Verification - MobileNetV2", layout="centered")
st.title("✍️ Signature Verification with OTP")

user_name = st.text_input("Enter Registered User Name")
uploaded_file = st.file_uploader("Upload New Signature to Verify", type=['png', 'jpg', 'jpeg'])

# ✅ Show uploaded signature preview
if uploaded_file is not None:
    st.image(uploaded_file, caption="🖼️ Uploaded Signature Preview", width=300)

if st.button("Verify Signature"):
    if not user_name or not uploaded_file:
        st.error("❌ Please provide both username and signature file.")
    else:
        user_folder = f"dataset/images/{user_name}"
        if not os.path.exists(user_folder):
            st.error("❌ User not found.")
        else:
            # Show registered stored signatures
            st.markdown("### 📂 Stored Registered Signatures for User:")
            col1, col2, col3 = st.columns(3)
            registered_files = os.listdir(user_folder)
            registered_files = sorted(registered_files)[:5]

            for idx, file in enumerate(registered_files):
                img_path = os.path.join(user_folder, file)
                img = Image.open(img_path)

                if idx % 3 == 0:
                    with col1:
                        st.image(img, width=200, caption=f"Signature {idx+1}")
                elif idx % 3 == 1:
                    with col2:
                        st.image(img, width=200, caption=f"Signature {idx+1}")
                else:
                    with col3:
                        st.image(img, width=200, caption=f"Signature {idx+1}")

            # Save uploaded file temporarily
            with open("temp_uploaded_signature.png", "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Compute similarity
            similarity_score = compute_similarity("temp_uploaded_signature.png", user_folder)
            st.write(f"🔍 Similarity Score: {similarity_score:.2f}")
            st.session_state['similarity_score'] = similarity_score

            threshold = 0.75
            phone_number = get_user_phone(user_name)

            if similarity_score >= threshold:
                st.success("✅ Signature seems valid.")
            else:
                st.warning("⚠️ Signature may be forged.")

            if phone_number:
                result = send_otp_with_verify(phone_number)
                st.session_state['otp_ready'] = True
                st.session_state['phone_number'] = phone_number
                st.info(f"📲 {result}")
            else:
                st.warning("⚠️ No phone number found.")

# ========== OTP Verification ==========
if st.session_state.get('otp_ready', False):
    st.markdown("---")
    st.subheader("🔐 Enter OTP to Confirm Identity")

    otp_input = st.text_input("Enter OTP received on your phone", key="otp_field")

    if st.button("Submit OTP"):
        status = check_otp(st.session_state['phone_number'], otp_input)

        if status:
            st.success("✅ OTP Verified Successfully!")

            similarity_score = st.session_state.get('similarity_score', 0.0)
            threshold = 0.75
            if similarity_score >= threshold:
                st.info("📝 Signature is Verified.")
            else:
                st.warning("🚨 Signature is a Forgery.")
        else:
            st.error("❌ OTP Verification Failed.")
