import os
import streamlit as st
import PyPDF2
import textwrap
from groq import Groq  # Ensure Groq API is installed
from reportlab.lib.pagesizes import letter,A4
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

# Function to save text as a PDF with wrapping
def save_text_as_pdf(text, font_size=12, margin=15):
    """
    Saves the given text to a PDF file, wrapping lines dynamically based on the page width.

    Args:
    - text: The text to save.
    - font_size: The font size for the text.
    - margin: Margin for the text in points.

    Returns:
    - BytesIO object containing the PDF data.
    """
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4
    y = height - margin  # Start position for text

    # Set font and size
    c.setFont("Helvetica", font_size)

    # Calculate maximum characters per line based on page width
    max_chars_per_line = int((width - 2 * margin) / (font_size * 0.6))  # Approximation

    for line in text.split("\n"):
        wrapped_lines = textwrap.wrap(line, width=max_chars_per_line)
        for wrapped_line in wrapped_lines:
            if y < margin:  # If at the bottom of the page, create a new page
                c.showPage()
                y = height - margin
            c.drawString(margin, y, wrapped_line)
            y -= font_size + 5 # Line spacing

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# Streamlit app setup
GROQ_API_KEY = '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'
groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize session state variables
if "responses" not in st.session_state:
    st.session_state.responses = []
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

# File upload
uploaded_file = st.sidebar.file_uploader("Upload a PDF file", type=["pdf"])

# User query input
question = st.chat_input("Ask something...")

# Check if the user entered a question
if question:
    if uploaded_file:
        with st.spinner("Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file, max_pages=9)

        if not pdf_text:
            st.error("Failed to extract text from the uploaded PDF.")
        else:
            with st.spinner("Generating response from the model..."):
                try:
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
                    response = completion.choices[0].message.content.strip()
                    st.session_state.responses.append({"user": question, "bot": response})

                    # Save the response as a PDF
                    st.session_state.pdf_data = save_text_as_pdf(response)

                    st.sidebar.success("Response generated successfully! You can now download it as a PDF.")

                except Exception as e:
                    st.error(f"An error occurred: {e}")
    else:
        st.error("Please upload a PDF file before asking a question.")


# Display previous responses
for chat in st.session_state.responses:
    st.markdown(
        f"""
        <div style="background-color: #DCF8C6; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
            <b>You:</b> {chat['user']}
        </div>
        <div style="background-color: #E1E1E1; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
            <b>AI:</b> {chat['bot']}
        </div>
        """,
        unsafe_allow_html=True,
    )

# Sidebar download button for the response PDF
if st.session_state.pdf_data:
    st.sidebar.download_button(
        label="Download Response as PDF",
        data=st.session_state.pdf_data,
        file_name="Generated_Response.pdf",
        mime="application/pdf",
    )
