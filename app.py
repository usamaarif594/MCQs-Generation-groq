import os
import streamlit as st
import PyPDF2
from groq import Groq  # Ensure Groq API is installed
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO


# Helper function to extract text from a PDF
def extract_text_from_pdf(pdf_file, max_pages=6):
    """
    Extracts text from a PDF file up to a maximum number of pages.
    
    Args:
    - pdf_file: File-like object of the uploaded PDF.
    - max_pages: int, number of pages to extract from.
    
    Returns:
    - str: Extracted text from the first `max_pages` pages.
    """
    text = ""
    reader = PyPDF2.PdfReader(pdf_file)
    for page_num in range(min(max_pages, len(reader.pages))):
        page = reader.pages[page_num]
        text += page.extract_text()
    return text

# Function to save text as a PDF
def save_text_as_pdf(text):
    """
    Saves the given text to a PDF file.
    
    Args:
    - text: The text to save.
    
    Returns:
    - BytesIO object containing the PDF data.
    """
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    y = height - 40  # Start position for text

    for line in text.split("\n"):
        if y < 40:  # If at the bottom of the page, create a new page
            c.showPage()
            y = height - 40
        c.drawString(40, y, line)
        y -= 15  # Move to the next line

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# Streamlit app setup
GROQ_API_KEY = st.sidebar.text_input('Paste your API key here', type='password')

groq_client = Groq(
    api_key=GROQ_API_KEY
)

# st.set_page_config(page_title="MCQ Generator", page_icon="📄", layout="centered")

# Initialize session state variables
if "responses" not in st.session_state:
    st.session_state.responses = []
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

# File upload
uploaded_file = st.sidebar.file_uploader("Upload a PDF file", type=["pdf"])

# Input for user question
question = st.text_input("Enter your query (e.g., 'Generate MCQs')")

# Generate response button
if st.button("Generate Response") and uploaded_file and question:
    # Extract text from the uploaded PDF
    with st.spinner("Extracting text from PDF..."):
        pdf_text = extract_text_from_pdf(uploaded_file, max_pages=9)

    if not pdf_text:
        st.error("Failed to extract text from the uploaded PDF.")
    else:
        # Call Groq or OpenAI API to generate response
        with st.spinner("Generating response from the model..."):
            try:
                # Groq API request
                completion = groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[
                        {
                            "role": "user",
                            "content": f"The following is the text extracted from the PDF:\n{pdf_text}\n\n{question}"
                        }
                    ],
                    temperature=1,
                    max_tokens=1024,
                    top_p=1,
                    stream=False,
                    stop=None,
                )

                # Extract response content
                response = completion.choices[0].message.content.strip()
                st.session_state.responses.append({"user": question, "bot": response})

                # Save the response as a PDF in session state
                st.session_state.pdf_data = save_text_as_pdf(response)

                st.success("Response generated successfully! You can now download it as a PDF.")

            except Exception as e:
                st.error(f"An error occurred: {e}")

# Download button
if st.session_state.pdf_data:
    st.download_button(
        label="Download Response as PDF",
        data=st.session_state.pdf_data,
        file_name="Generated_Response.pdf",
        mime="application/pdf",
    )

# # Display chat-like interface
# st.write("### Chat")
# for chat in st.session_state.responses:
#     st.markdown(
#         f"""
#         <div style="background-color: #DCF8C6; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
#             <b>You:</b> {chat['user']}
#         </div>
#         <div style="background-color: #E1E1E1; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
#             <b>AI:</b> {chat['bot']}
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )
