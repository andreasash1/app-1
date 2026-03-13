import streamlit as st
import pandas as pd
from groq import Groq

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="PDA AI Assistant", page_icon="🚢", layout="centered")

# --- SECURITY: PASSWORD LOGIN ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # delete password from memory
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 Private PDA Portal")
        st.text_input("Enter Access Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔒 Private PDA Portal")
        st.text_input("Enter Access Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    return True

# --- MAIN APP LOGIC ---
if check_password():
    st.title("🚢 Secure PDA AI Assistant")
    st.info("Upload a PDA spreadsheet to chat with it. Data is erased when you close the app.")
    
    # Initialize Groq AI Client
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    # File Uploader - NOW ACCEPTS BOTH CSV AND XLSX
    uploaded_file = st.file_uploader("Upload PDA (CSV or Excel)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            # Check the file extension and read appropriately
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                # Try standard CSV, if it fails due to Excel's weird encoding, try latin1
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(uploaded_file, encoding='latin1')
            
            pda_data_string = df.to_string() # Convert spreadsheet to text for the AI
            
            st.success(f"Successfully loaded: {uploaded_file.name}")
            
            # Chat Interface
            st.subheader("💬 Ask about this PDA")
            
            # Keep track of chat history
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # User Input
            if prompt := st.chat_input("E.g., What is the total ISPS cost?"):
                # Add user message to UI
                st.chat_message("user").markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})

                # System instructions instructing Llama 3 how to behave
                system_prompt = f"""
                You are a maritime shipping expert. Answer the user's question using ONLY the following PDA data.
                Provide calculations if requested.
                
                PDA DATA:
                {pda_data_string}
                """

                # Call Groq / Llama 3 Open Source AI
                with st.spinner("Analyzing PDA..."):
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        model="llama3-70b-8192", 
                        temperature=0.2, 
                    )
                    
                    reply = chat_completion.choices[0].message.content
                    
                    # Show AI reply
                    with st.chat_message("assistant"):
                        st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    
        except Exception as e:
            st.error(f"Error reading file: {e}. Please ensure it is a valid, uncorrupted spreadsheet.")
