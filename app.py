import streamlit as st
import pandas as pd
import os
from PIL import Image

# =============== Helper Functions ===============

def create_dataset_folders():
    """Ensure dataset folders exist."""
    if not os.path.exists('dataset'):
        os.makedirs('dataset')
    if not os.path.exists('dataset/images'):
        os.makedirs('dataset/images')
    if not os.path.exists('dataset/users.csv'):
        df = pd.DataFrame(columns=["name", "phone", "email", "secondary_phone"])
        df.to_csv('dataset/users.csv', index=False)

def register_new_user(user_name, phone, email, secondary_phone, signature_files):
    """Register user and save signatures."""
    users_csv_path = 'dataset/users.csv'
    
    users_df = pd.read_csv(users_csv_path)
    for col in ["name", "phone", "email", "secondary_phone"]:
        if col not in users_df.columns:
            users_df[col] = ""

    # Check if user exists
    if user_name not in users_df['name'].values:
        new_entry = pd.DataFrame({
            "name": [user_name],
            "phone": [phone],
            "email": [email],
            "secondary_phone": [secondary_phone]
        })
        users_df = pd.concat([users_df, new_entry], ignore_index=True)
        users_df.to_csv(users_csv_path, index=False)
        st.success(f"✅ User '{user_name}' registered successfully!")
    else:
        st.warning(f"⚠️ User '{user_name}' already exists. Updating signatures only.")

    # Save signature images
    user_folder = f'dataset/images/{user_name}'
    os.makedirs(user_folder, exist_ok=True)

    for idx, file in enumerate(signature_files):
        img = Image.open(file).convert('L')
        img.save(os.path.join(user_folder, f"signature_{idx+1}.png"))

    st.success(f"✅ {len(signature_files)} signatures saved for {user_name}!")

# =============== Streamlit UI ===============

st.set_page_config(page_title="User Registration - Signature Verification", layout="centered")

st.title("✍️ Register New User")
st.markdown("Fill in user details and upload 5 signature images.")

# Ensure folders exist
create_dataset_folders()

# User form
with st.form("registration_form"):
    name = st.text_input("Name")
    phone = st.text_input("Phone Number (US only)", max_chars=15)
    email = st.text_input("Email Address")
    secondary_phone = st.text_input("Secondary Phone Number", max_chars=15)

    st.markdown("### Upload 5 Signature Images")
    uploaded_signatures = st.file_uploader("Upload Signatures", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

    submit_btn = st.form_submit_button("Register User")

    if submit_btn:
        if not name or not phone or not email or not secondary_phone:
            st.error("❌ Please fill in all fields.")
        elif len(uploaded_signatures) != 5:
            st.error("❌ Please upload exactly 5 signature images.")
        else:
            register_new_user(name.strip(), phone.strip(), email.strip(), secondary_phone.strip(), uploaded_signatures)
