import streamlit as st
import requests
import base64
from PIL import Image
import io
import os

# Page configuration
st.markdown("""
<style>
/* App background */
.stApp {
    background-color: #0f172a;
    color: #e5e7eb;
}

/* Title container */
.title-container {
    background-color: #111827;
    border-radius: 14px;
    padding: 2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
}

.title-container h1 {
    color: #e5e7eb;
}

.title-container p {
    color: #9ca3af;
}

/* Chat bubbles */
.chat-message {
    padding: 1.3rem;
    border-radius: 14px;
    margin-bottom: 1rem;
    font-size: 1rem;
}

/* User message */
.user-message {
    background-color: #1e293b;
    color: #e5e7eb;
    margin-left: 22%;
    border-left: 4px solid #38bdf8;
}

/* Assistant message */
.assistant-message {
    background-color: #020617;
    color: #e5e7eb;
    margin-right: 22%;
    border-left: 4px solid #22c55e;
}

/* Input box */
.stTextInput input {
    background-color: #020617;
    border-radius: 12px;
    border: 1px solid #334155;
    color: #e5e7eb;
}

/* Buttons */
.stButton button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 600;
}

.stButton button:hover {
    background-color: #1d4ed8;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #020617;
}

/* Sidebar text */
section[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

/* Footer */
.footer {
    background: none;
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Try to load API key from secrets, otherwise use empty string
if "api_key" not in st.session_state:
    try:
        # Try to get API key from Streamlit secrets
        st.session_state.api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    except:
        # If secrets not available, use empty string
        st.session_state.api_key = ""

# System prompt for the math tutor
SYSTEM_PROMPT = """You are an expert mathematics tutor with years of experience helping students of all levels. Your teaching style is:

1. **Patient and Encouraging**: You understand that math can be challenging, so you always remain supportive and positive.

2. **Step-by-Step Approach**: You break down complex problems into simple, manageable steps. You explain each step clearly before moving to the next.

3. **Clear Formatting**: 
   - Use **bold** for important concepts
   - Use bullet points for lists
   - Number your steps clearly (Step 1, Step 2, etc.)
   - Use simple mathematical notation that students can easily read
   - For equations, write them clearly on separate lines
   - Avoid excessive LaTeX formatting - use simple math notation instead
   - Example: Write "x^2 + 5x + 6" instead of complex LaTeX
   - For fractions, write "1/2" or "numerator/denominator"
   - Use ** for exponents: x**2 means x squared

4. **Visual and Intuitive**: Whenever possible, you help students visualize concepts and build intuition rather than just memorizing formulas.

5. **Interactive**: You ask guiding questions to help students think through problems themselves, promoting deeper understanding.

6. **Comprehensive**: You cover:
   - Arithmetic and basic operations
   - Algebra (equations, inequalities, polynomials)
   - Geometry and trigonometry
   - Calculus (derivatives, integrals, limits)
   - Statistics and probability
   - Linear algebra and matrices
   - Discrete mathematics
   - And any other mathematical topic students need help with

7. **Mistake-Friendly**: When students make errors, you gently point them out and explain the correct approach without making them feel bad.

8. **Multiple Methods**: You show different ways to solve problems when applicable, helping students find the approach that works best for them.

9. **Real-World Connections**: You connect mathematical concepts to real-world applications to make learning more meaningful.

FORMATTING GUIDELINES:
- Use clear, readable text formatting
- Avoid complex LaTeX - students find it confusing
- Write equations simply: x^2 + 5x + 6 = 0
- Use line breaks to separate steps
- Box final answers using: **Answer: x = 5**
- Use simple symbols: √ for square root, ÷ for division, × for multiplication

When a student shares an image of a math problem, carefully analyze it and provide a detailed, step-by-step solution. Always check your work and ensure accuracy in your calculations and explanations."""

def encode_image(image_file):
    """Convert image to base64 string"""
    if image_file is not None:
        bytes_data = image_file.getvalue()
        return base64.b64encode(bytes_data).decode('utf-8')
    return None

def call_openrouter_api(messages, api_key, has_image=False):
    """Call OpenRouter API with the messages"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://math-tutor-ai.streamlit.app",
        "X-Title": "Math Tutor AI"
    }
    
    # Use vision model if image is present, otherwise use DeepSeek R1
    model = "openai/gpt-4.1-mini" if has_image else "deepseek/deepseek-r1-0528:free"
    
    data = {
        "model": model,
        "messages": messages
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}\n\nPlease check your API key and internet connection."

# Sidebar
with st.sidebar:
    st.markdown("### 🔐 API Configuration")
    
    # Check if API key is loaded from secrets
    if st.session_state.api_key and not st.session_state.get("api_key_from_user", False):
        st.success("✅ API Key loaded from secrets!")
        st.info("💡 Your API key is configured in secrets.toml")
        if st.button("🔄 Use Different Key"):
            st.session_state.api_key = ""
            st.session_state.api_key_from_user = True
            st.rerun()
    else:
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=st.session_state.api_key if st.session_state.get("api_key_from_user", False) else "",
            help="Get your free API key from https://openrouter.ai"
        )
        
        if api_key:
            st.session_state.api_key = api_key
            st.session_state.api_key_from_user = True
            st.success("✅ API Key set!")
        else:
            st.warning("⚠️ Please enter your OpenRouter API key")
    
    st.markdown("---")
    
    st.markdown("### 🤖 AI Models")
    st.markdown("""
    **Smart Model Switching:**
    - 📝 Text Questions → DeepSeek R1  
    - 📸 Image Questions → Gemini 2.0 Flash
    
    Both are **FREE**! 🎉
    """)
    
    st.markdown("---")
    
    st.markdown("### 📚 How to Use")
    st.markdown("""
    1. Enter your OpenRouter API key above
    2. Type your math question or upload an image
    3. Click 'Send' or press Enter
    4. Get detailed, step-by-step solutions!
    """)
    
    st.markdown("---")
    
    st.markdown("### 💡 Tips")
    st.markdown("""
    - Be specific about what you're struggling with
    - Upload clear images of problems
    - Ask follow-up questions if you need clarification
    - Request different solution methods
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎓 Subjects Covered")
    st.markdown("""
    - ➕ Arithmetic
    - 📐 Geometry
    - 📊 Algebra
    - 📈 Calculus
    - 📉 Statistics
    - 🔢 Trigonometry
    - 🧮 And more!
    """)

# Main content
st.markdown("""
    <div class="title-container">
        <h1>🧮 AI Math Tutor </h1>
        <p style="color: #666; font-size: 1.2rem;">Your Personal Mathematics Learning Companion</p>
        <p style="color: #888;">Struggling with math? I'm here to help you understand every step!</p>
    </div>
    """, unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {message["content"] if isinstance(message["content"], str) else message["content"][0]["text"]}
            </div>
            """, unsafe_allow_html=True)
        
        # Display image if present
        if not isinstance(message["content"], str):
            for content in message["content"]:
                if content["type"] == "image_url":
                    st.image(base64.b64decode(content["image_url"]["url"].split(",")[1]))
    else:
        # Display assistant message with LaTeX support
        st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Math Tutor:</strong>
            </div>
            """, unsafe_allow_html=True)
        # Render the content with LaTeX support
        st.markdown(message["content"], unsafe_allow_html=True)

# Input area
col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.text_input(
        "Ask your math question here...",
        placeholder="e.g., How do I solve 2x + 5 = 15?",
        key="user_input",
        label_visibility="collapsed"
    )

with col2:
    uploaded_file = st.file_uploader(
        "📷 Upload Image",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed"
    )

# Display uploaded image preview
if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Math Problem", width=300)

# Send button
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    send_button = st.button("📤 Send", use_container_width=True)

# Process input
if send_button and (user_input or uploaded_file):
    if not st.session_state.api_key:
        st.error("⚠️ Please enter your OpenRouter API key in the sidebar!")
    else:
        # Prepare message content
        if uploaded_file and user_input:
            # Both text and image
            user_message_content = [
                {"type": "text", "text": user_input},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encode_image(uploaded_file)}"
                    }
                }
            ]
        elif uploaded_file:
            # Only image
            user_message_content = [
                {"type": "text", "text": "Please help me solve this math problem from the image."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encode_image(uploaded_file)}"
                    }
                }
            ]
        else:
            # Only text
            user_message_content = user_input
        
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": user_message_content
        })
        
        # Check if there's an image in the message
        has_image = not isinstance(user_message_content, str)
        
        # Prepare messages for API call
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        for msg in st.session_state.messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Show loading spinner
        with st.spinner("🤔 Thinking and solving..."):
            response = call_openrouter_api(api_messages, st.session_state.api_key, has_image)
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
        
        # Rerun to update chat display
        st.rerun()

# Footer
st.markdown("""
    <div class="footer">
        <p><strong>Made by Junaid</strong></p>
        <p style="font-size: 0.9rem;">Empowering students to master mathematics, one problem at a time.</p>
       
    </div>
    """, unsafe_allow_html=True)

# Welcome message if no messages yet
if len(st.session_state.messages) == 0:
    st.markdown("""
        <div style="text-align: center; padding: 3rem; background: rgba(255, 255, 255, 0.9); border-radius: 15px; margin: 2rem auto; max-width: 800px;">
            <h2 style="color: #667eea;">👋 Welcome to AI Math Tutor !</h2>
            <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                I'm here to help you understand and solve any math problem you're struggling with.
                Whether it's basic arithmetic or advanced calculus, I'll guide you through every step.
            </p>
            <p style="color: #888; margin-top: 1rem;">
                💡 <strong>Tip:</strong> You can type your question or upload a photo of your math problem!
            </p>
        </div>
        """, unsafe_allow_html=True)
