from flask import Flask, request, jsonify
import yt_dlp
import whisper
import ffmpeg
from googletrans import Translator
from gtts import gTTS
import os
import uuid

app = Flask(__name__)

# Load Whisper model
model = whisper.load_model("small")


@app.route("/convert", methods=["POST"])
def convert_video():
    try:
        data = request.json
        youtube_url = data.get("url")
        target_lang = data.get("target", "hi")

        if not youtube_url:
            return jsonify({"status": "error", "message": "URL missing"})

        job_id = str(uuid.uuid4())
        input_video = f"video_{job_id}.mp4"
        input_audio = f"audio_{job_id}.mp3"
        output_audio = f"new_audio_{job_id}.mp3"
        final_video = f"dubbed_{job_id}.mp4"

        # STEP 1 — Download video
        ydl_opts = {"outtmpl": input_video}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # STEP 2 — Extract audio
        ffmpeg.input(input_video).output(input_audio).run(overwrite_output=True)

        # STEP 3 — Speech-to-text (English)
        result = model.transcribe(input_audio)
        english_text = result["text"]

        # STEP 4 — Translate text
        translator = Translator()
        translated = translator.translate(english_text, dest=target_lang).text

        # STEP 5 — Text-to-speech
        tts = gTTS(text=translated, lang=target_lang)
        tts.save(output_audio)

        # STEP 6 — Merge new audio with video
        ffmpeg.input(input_video).input(output_audio).output(
            final_video, vcodec="copy", acodec="aac"
        ).run(overwrite_output=True)

        # STEP 7 — Store in output folder
        if not os.path.exists("output"):
            os.makedirs("output")

        final_path = f"output/{final_video}"
        os.rename(final_video, final_path)

        return jsonify({
            "status": "success",
            "download_url": f"https://YOUR_RENDER_DOMAIN/output/{final_video}"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/")
def home():
    return "Hindi Dub API is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
