import streamlit as st     
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import smtplib
import ssl
from email.message import EmailMessage
import io  
import time  
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# ✅ Load environment variables
load_dotenv()

# ✅ Secure credentials (No hardcoding)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  
SENDER_EMAIL = os.getenv("EMAIL_SENDER")  
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")  

# ✅ Use correct paths based on the folder structure
TEMPLATE_PATH = "templates/certificate_template1.png"
FONT_NAME_PATH = "fonts/PlayfairDisplay-VariableFont_wght.ttf"
FONT_DATE_PATH = "fonts/Cardo-Regular.ttf"
BACKGROUND_IMAGE = "assets/future.jpg"  # High-resolution futuristic background
LOGO_PATH = "assets/logo.svg"  # ✅ Added for Page Icon

# ✅ Font Settings
FONT_SIZE_NAME = 90
FONT_SIZE_DATE = 45
FONT_SIZE_COURSE = 40
TEXT_POSITION_NAME = (510, 500)  
TEXT_POSITION_DATE = (840, 950)
TEXT_POSITION_COURSE = (490, 705)  
TEXT_COLOR = "black"

EMAIL_SUBJECT = "🎓 Your Certificate of Achievement!"
EMAIL_BODY = """Dear {name},

🎉 Congratulations! You have successfully completed the **{course}** program on {date}.
Please find attached your personalized certificate.

Best regards,  
Your Organization  
"""

# ---- STREAMLIT UI ----
st.set_page_config(page_title="Certificate Generator", page_icon=LOGO_PATH, layout="wide")  # ✅ Updated with logo.svg

# 🔥 **Apply Futuristic Background to the Entire Web App**
background_style = f"""
    <style>
    .stApp {{
        background: url('{BACKGROUND_IMAGE}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .title-container {{
        background: rgba(30, 60, 114, 0.8); /* Semi-transparent background */
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
    }}
    .subtext {{
        font-size: 18px;
        font-weight: 500;
        color: #f0f0f0;
        text-align: center;
    }}
    .success-message {{
        font-size: 20px;
        font-weight: bold;
        color: lime;
        text-align: center;
        margin-top: 10px;
    }}
    </style>
"""

st.markdown(background_style, unsafe_allow_html=True)

# 🎓 **Title Section**
st.markdown("<div class='title-container'><h1>🎓 CP-T Automated Certificate Generator & Sender</h1></div>", unsafe_allow_html=True)
st.markdown("<p class='subtext'>Now you can send a certificate to a specific also, Just pull the arrow at left hand.</p>", unsafe_allow_html=True)

# ✅ **Success Message Placeholder (Initially Empty)**
success_message = st.empty()

st.markdown("<hr>", unsafe_allow_html=True)

# ---- SIDEBAR CONFIG ----
st.sidebar.image(TEMPLATE_PATH, width=250)
st.sidebar.title("🔧 Settings")

# 📂 **CSV Upload Option**
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV File", type=["csv"])

# 📌 **Send to an Individual**
st.sidebar.markdown("### 🎯 Send to a Specific Person")
individual_name = st.sidebar.text_input("👤 Enter Name")
individual_email = st.sidebar.text_input("📧 Enter Email")

course_name = st.sidebar.text_input("📘 Enter Course Name", value="DSA Using C++")
selected_date = st.sidebar.date_input("📅 Select Certificate Date")

generate_button = st.sidebar.button("🚀 Generate & Send Certificates")
send_individual_button = st.sidebar.button("📩 Send to Individual")

# ---- FUNCTION TO GENERATE CERTIFICATE ----
def generate_certificate(name, date, course):
    """Generates certificate in memory (No Disk Writes)"""
    try:
        image = Image.open(TEMPLATE_PATH)
        draw = ImageDraw.Draw(image)

        font_name = ImageFont.truetype(FONT_NAME_PATH, FONT_SIZE_NAME)
        font_date = ImageFont.truetype(FONT_DATE_PATH, FONT_SIZE_DATE)
        font_course = ImageFont.truetype(FONT_NAME_PATH, FONT_SIZE_COURSE)

        draw.text(TEXT_POSITION_NAME, name, fill=TEXT_COLOR, font=font_name)
        draw.text(TEXT_POSITION_DATE, date, fill=TEXT_COLOR, font=font_date)
        draw.text(TEXT_POSITION_COURSE, course, fill=TEXT_COLOR, font=font_course)

        cert_io = io.BytesIO()
        image.save(cert_io, format="PNG")
        cert_io.seek(0)
        return cert_io
    except Exception as e:
        st.error(f"❌ Certificate generation failed for {name}: {e}")
        return None

# ---- FUNCTION TO SEND EMAIL ----
def send_email(name, recipient_email, date, course, cert_io):
    """Sends an email with the generated certificate & prevents Gmail blocking"""
    if cert_io is None:
        return f"❌ Certificate for {name} could not be generated."

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as smtp_server:
            smtp_server.login(SENDER_EMAIL, SENDER_PASSWORD)

            msg = EmailMessage()
            msg["From"] = SENDER_EMAIL
            msg["To"] = recipient_email
            msg["Subject"] = f"🎓 Your Certificate for {course}"
            msg.set_content(f"Dear {name},\n\nCongratulations! Your certificate for {course} on {date} is attached.\n\nBest regards,\nCipheren Technology")
            msg.add_attachment(cert_io.getvalue(), maintype="image", subtype="png", filename=f"{name}.png")

            smtp_server.send_message(msg)
            time.sleep(1)
            return f"✅ Sent certificate to {name} ({recipient_email})"
    except Exception as e:
        return f"❌ Failed to send certificate to {name}: {e}"

# 📌 **SEND CERTIFICATE TO ONE INDIVIDUAL**
if send_individual_button:
    if not individual_name or not individual_email:
        st.sidebar.error("❌ Please enter both name and email.")
    else:
        cert_io = generate_certificate(individual_name, selected_date.strftime("%d-%m-%Y"), course_name)
        result = send_email(individual_name, individual_email, selected_date.strftime("%d-%m-%Y"), course_name, cert_io)
        success_message.markdown(f"<p class='success-message'>{result}</p>", unsafe_allow_html=True)

# 📂 **PROCESS CSV FILE & SEND CERTIFICATES**
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.lower()

    if not {"name", "email"}.issubset(df.columns):
        st.error("❌ CSV must contain 'name' and 'email' columns!")
    else:
        df = df[["name", "email"]]
        df["name"] = df["name"].str.title()
        df["email"] = df["email"].str.lower()
        df = df.drop_duplicates(subset=["name", "email"], keep="first")

        st.write("📜 **Uploaded Data Preview:**")
        st.dataframe(df)

        if generate_button:
            progress_bar = st.progress(0)
            results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(send_email, row["name"], row["email"], selected_date.strftime("%d-%m-%Y"), course_name, generate_certificate(row["name"], selected_date.strftime("%d-%m-%Y"), course_name)): row for _, row in df.iterrows()}
                
                for i, future in enumerate(as_completed(futures)):
                    result = future.result()
                    results.append(result)
                    progress_bar.progress((i + 1) / len(df))

            for res in results:
                st.write(res)

            st.balloons()
            st.sidebar.success("🎉 All certificates sent successfully!")
