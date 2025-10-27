import streamlit as st
import fitz # PyMuPDF library
from gtts import gTTS
import os
from io import BytesIO

# --- Configuration ---
st.set_page_config(
    page_title="PDF to Audiobook Converter",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Functions ---

def extract_text_from_pdf(pdf_file):
    """
    Step 1 & 2: Loads PDF from an uploaded file object and extracts/cleans text.
    Uses PyMuPDF (imported as fitz) to handle the PDF structure.
    """
    try:
        # Read the file data into a BytesIO object
        pdf_bytes = pdf_file.read()
        pdf_stream = BytesIO(pdf_bytes)

        # Open the PDF document using fitz (PyMuPDF)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        text = ""
        
        # Iterate through pages and extract text
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + " "
        
        # Clean text (Step 2: Clean text and handle empty pages)
        cleaned_text = text.replace('\n', ' ').replace('\r', ' ').strip()
        cleaned_text = " ".join(cleaned_text.split()) # Remove extra spaces
        
        if not cleaned_text:
            st.error("Error: Could not extract any readable text from the PDF.")
            return None

        return cleaned_text

    except Exception as e:
        st.error(f"An error occurred during PDF processing: {e}")
        return None

def convert_text_to_mp3(text, speed_rate, pitch):
    """
    Step 3 & 4: Converts cleaned text to an MP3 audio file using gTTS.
    Note: gTTS does not support pitch control, but the speed control is handled by the 'slow' parameter.
    We will map the 'rate' slider to the gTTS 'slow' parameter (True for slower, False for normal/faster).
    """
    try:
        # gTTS 'slow' parameter maps to speed. True is slow, False is normal/fast.
        # We will set 'slow' to True only if the user rate is below the default (1.0).
        is_slow = speed_rate < 1.0

        # Language code for English (default)
        tts = gTTS(text=text, lang='en', slow=is_slow)
        
        # Save the audio data to a BytesIO object in memory
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        return mp3_fp

    except Exception as e:
        st.error(f"An error occurred during audio conversion: {e}")
        return None

# --- Streamlit UI Components ---

st.title("📚 PDF to Audiobook Converter")
st.markdown("Upload a PDF file to convert its content into a downloadable MP3 audiobook.")
st.divider()

# --- File Upload (Step 5: Create file upload UI) ---
pdf_file = st.file_uploader(
    "Upload your PDF document",
    type=["pdf"],
    accept_multiple_files=False,
    help="Only single PDF files are supported."
)

# --- Controls (Step 6: Add control options (volume, speed)) ---

st.subheader("Audio Settings")

# Split controls into two columns for better layout
col1, col2 = st.columns(2)

with col1:
    # Reading Speed (Rate)
    # gTTS only supports two speeds (slow=True or slow=False)
    # We simplify the user experience by using a select box corresponding to the gTTS settings
    speed_option = st.selectbox(
        "Reading Speed (Rate)",
        options=[
            "Normal (1.0x)",
            "Slow (0.5x)"
        ],
        index=0,
        help="Controls the speed of the voice narration."
    )
    speed_rate = 0.5 if speed_option == "Slow (0.5x)" else 1.0


with col2:
    # Pitch Control - gTTS does not support pitch control, so this is displayed for UX consistency
    # but functionally does nothing in the gTTS implementation.
    pitch = st.slider(
        "Voice Pitch (Not functional with gTTS)",
        min_value=0.5,
        max_value=1.5,
        value=1.0,
        step=0.1,
        help="Note: The underlying gTTS library does not support dynamic pitch control."
    )

st.divider()

# --- Main Logic ---
if pdf_file:
    # Display processing status
    with st.spinner('Extracting text from PDF...'):
        # Step 1 & 2: Extract text
        pdf_text = extract_text_from_pdf(pdf_file)

    if pdf_text:
        st.success("✅ Text extraction complete!")
        
        # Provide a section to show the extracted text (optional but good for debugging)
        with st.expander("View Extracted Text"):
            st.code(pdf_text[:1000] + "..." if len(pdf_text) > 1000 else pdf_text)

        st.info("Converting text to MP3. This may take a moment for large files...")
        
        # Step 3 & 4: Convert text to MP3 file (in-memory)
        mp3_file = convert_text_to_mp3(pdf_text, speed_rate, pitch)

        if mp3_file:
            st.success("🎉 Audiobook created successfully!")
            
            # Use st.audio to allow playback and native browser download
            st.audio(mp3_file, format='audio/mp3')

            # --- Deliverable: Allow download of the audio file ---
            st.download_button(
                label="Download MP3 Audiobook",
                data=mp3_file,
                file_name=f"{os.path.splitext(pdf_file.name)[0]}_audiobook.mp3",
                mime="audio/mp3",
                type="primary"
            )

        else:
            st.error("Could not create the MP3 file.")
else:
    st.info("Please upload a PDF file above to begin the conversion process.")

# --- Footer ---
st.markdown("---")
st.caption("Built with Streamlit, PyMuPDF, and gTTS. Note: gTTS has limited control over speed and pitch.")
