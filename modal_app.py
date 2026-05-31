import os
import io
import tempfile
import modal

# Define the Modal App
app = modal.App("voice-researcher-agent")

# Create a container image with all necessary dependencies for audio processing, STT, and TTS.
# Pre-download models during image build to eliminate startup cold-start delays.
image = (
    modal.Image.debian_slim()
    .apt_install("ffmpeg")
    .pip_install(
        "faster-whisper==1.0.3",
        "transformers==4.38.2",
        "torch==2.2.1",
        "soundfile==0.12.1",
        "numpy==1.26.4",
        "scipy==1.12.0"
    )
    .run_commands(
        # Pre-download Whisper base model
        "python3 -c 'from faster_whisper import WhisperModel; WhisperModel(\"base\", device=\"cpu\", compute_type=\"float32\")'",
        # Pre-download Facebook MMS-TTS English model
        "python3 -c 'from transformers import VitsModel, AutoTokenizer; VitsModel.from_pretrained(\"facebook/mms-tts-eng\"); AutoTokenizer.from_pretrained(\"facebook/mms-tts-eng\")'"
    )
)

@app.cls(image=image, keep_warm=1)
class AudioService:
    def __init__(self):
        # Initialize Whisper
        from faster_whisper import WhisperModel
        self.whisper_model = WhisperModel("base", device="cpu", compute_type="float32")
        
        # Initialize TTS
        from transformers import VitsModel, AutoTokenizer
        self.tts_model = VitsModel.from_pretrained("facebook/mms-tts-eng")
        self.tts_tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-eng")

    @modal.method()
    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribes voice input audio bytes into text using Whisper.
        """
        try:
            # Write audio bytes to a temporary file because Whisper expects a file path
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name

            segments, info = self.whisper_model.transcribe(temp_audio_path, beam_size=5)
            transcription = " ".join([segment.text for segment in segments]).strip()
            
            # Clean up temp file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
                
            return transcription
        except Exception as e:
            return f"Transcription error: {str(e)}"

    @modal.method()
    def text_to_speech(self, text: str) -> bytes:
        """
        Generates spoken audio (WAV bytes) from text using Facebook MMS-TTS.
        """
        import torch
        import soundfile as sf
        import numpy as np

        try:
            # MMS-TTS is trained on lowercase text without punctuation for some languages, 
            # but for English it handles standard text fine. Clean up a little to be safe.
            cleaned_text = text.replace("\n", " ").replace("*", "").replace("#", "").strip()
            # Truncate text if it is extremely long to prevent OOMs or long waits
            cleaned_text = cleaned_text[:400]  # Let's say 400 chars (approx. 2-3 sentences of briefing summary)

            inputs = self.tts_tokenizer(cleaned_text, return_tensors="pt")
            
            with torch.no_grad():
                output = self.tts_model(**inputs)
                
            # Extract waveform and convert to float32 numpy array
            waveform = output.waveform[0].cpu().numpy()
            sampling_rate = self.tts_model.config.sampling_rate

            # Write waveform to WAV bytes
            out_bio = io.BytesIO()
            sf.write(out_bio, waveform, sampling_rate, format="WAV", subtype="PCM_16")
            
            return out_bio.getvalue()
        except Exception as e:
            print(f"TTS Error: {e}")
            # Return an empty bytes or handle gracefully
            return b""
