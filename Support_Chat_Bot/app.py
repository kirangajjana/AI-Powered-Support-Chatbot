import streamlit as st
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.schema.runnable import RunnableBranch, RunnableLambda
from pydantic import BaseModel, Field
from typing import Literal
import os

# Load API Keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI model
model = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0)

# -----------------------------
# 🏷 Pydantic Schema for Issue Classification
# -----------------------------
class SupportTicketClassification(BaseModel):
    category: str = Field(..., description="Classified support category")

# -----------------------------
# 📜 AI Prompt for Classification (Fixed JSON Output)
# -----------------------------
parser = PydanticOutputParser(pydantic_object=SupportTicketClassification)

classification_prompt = PromptTemplate(
    template="""
    You are an AI support assistant trained to classify customer issues accurately.
    Your task is to determine if a user’s request falls into one of these categories:

    1️⃣ **Billing & Payments Issue** (charges, invoices, refunds)
    2️⃣ **Account & Access Issue** (login, security, account management)
    3️⃣ **Technical Support Issue** (software, hardware, performance issues)
    4️⃣ **Needs Clarification** (if unclear)

    ⚠️ STRICT INSTRUCTIONS:
    - **Return JSON output ONLY**, following this format:
      {format_instructions}
    - **Do NOT add explanations, text, or anything outside the JSON format.**
    
    User Request: "{feedback}"
    """,
    input_variables=["feedback"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# Classification Chain
classification_chain = classification_prompt | model | parser

# -----------------------------
# 🔀 Conditional Chains for Response
# -----------------------------
def generate_response(category):
    """Generate a user-friendly response after classification."""
    return f"✅ Thank you for reaching out! Your issue has been classified under '{category}'. Please enter your **Name** and **Phone Number** to proceed."

def confirm_ticket_creation():
    """Confirm ticket creation after user enters name & phone number."""
    user_name = st.session_state.get("user_name", "").strip()
    user_phone = st.session_state.get("user_phone", "").strip()
    category = st.session_state.get("category", "")

    if not user_name or not user_phone:
        st.warning("⚠️ Please enter both Name and Phone Number.")
    else:
        st.success(f"🎉 **Ticket Created!** Hello {user_name}, your support request under '{category}' has been recorded. Our team will contact you at {user_phone} soon.")
        st.subheader("🎉 Thank you for contacting us! Your ticket has been created.")

        # Hide form after confirmation
        st.session_state['show_user_details'] = False

# 🏗 Fix: Ensure correct structure in branching chain
branching_chain = RunnableBranch(
    (lambda x: x == "Billing & Payments Issue", RunnableLambda(lambda x: generate_response("Billing & Payments Issue"))),
    (lambda x: x == "Account & Access Issue", RunnableLambda(lambda x: generate_response("Account & Access Issue"))),
    (lambda x: x == "Technical Support Issue", RunnableLambda(lambda x: generate_response("Technical Support Issue"))),
    (lambda x: x == "Needs Clarification", RunnableLambda(lambda x: "Please provide more details.")),
    RunnableLambda(lambda x: "Unable to process your request.")
)

# -----------------------------
# 🚀 Streamlit UI
# -----------------------------
st.set_page_config(page_title="AI Support Chatbot", layout="wide")

st.title("🔧 AI Support Chatbot")
st.subheader("Describe your issue, and our AI will classify it.")

# ✅ Sidebar for test questions
st.sidebar.header("💡 Test the Chatbot")
sample_questions = {
    "🔹 I forgot my password and can't log in.": "I forgot my password and can't log in.",
    "🔹 My subscription was charged twice this month.": "My subscription was charged twice this month.",
    "🔹 The app crashes every time I open it.": "The app crashes every time I open it.",
    "🔹 I need help updating my billing address.": "I need help updating my billing address.",
    "🔹 My internet is not working.": "My internet is not working.",
}

selected_question = st.sidebar.radio("Click to test:", list(sample_questions.keys()))

if st.sidebar.button("Use Sample Question"):
    st.session_state['user_feedback'] = sample_questions[selected_question]

user_feedback = st.text_area("📩 Enter your support request:", value=st.session_state.get('user_feedback', ''))

if st.button("Submit Issue"):
    if not user_feedback.strip():
        st.warning("⚠️ Please enter your issue before submitting.")
    else:
        try:
            category = classification_chain.invoke({"feedback": user_feedback}).category
            response_text = branching_chain.invoke(category)
            st.success(response_text)

            # Store classification result in session state
            st.session_state['category'] = category
            st.session_state['show_user_details'] = True

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ✅ Show Name & Phone Number input **only after classification**
if st.session_state.get('show_user_details', False):
    st.subheader("📝 Please enter your details to create a ticket.")

    # Store inputs in session_state to prevent reset
    st.session_state['user_name'] = st.text_input("👤 Enter your Name:", value=st.session_state.get('user_name', ''))
    st.session_state['user_phone'] = st.text_input("📞 Enter your Phone Number:", value=st.session_state.get('user_phone', ''))

    if st.button("Confirm Ticket Creation"):
        confirm_ticket_creation()

# -----------------------------
# 🎨 UI Enhancements
# -----------------------------
st.markdown("""
---
### 🔹 How It Works:
1. **Test the chatbot** using sample questions from the sidebar or enter your own issue.
2. Click **Submit Issue** to classify your request.
3. Enter your **Name** and **Phone Number**, then click **Confirm Ticket Creation**.
4. AI will handle your request and provide a response.

🚀 Created by Kiran Gajjana 
""")
