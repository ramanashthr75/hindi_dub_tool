from flask import Flask, request, jsonify
import os
import yt_dlp
import whisper
import requests
from gtts import gTTS
import subprocess
import uuid

app = Flask(__name__)

model = whisper.load_model("base")

def download_youtube_audio(url):
    id = str(uuid.uuid4())
    audio_file = f"audio_{id}.mp3"
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': audio_file}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return audio_file

@app.route("/dub", methods=["POST"])
def dub_video():
    data = request.json
    yt_url = data.get("youtube_url")

    audio_file = download_youtube_audio(yt_url)

    result = model.transcribe(audio_file)
    english_text = result["text"]

    translate_res = requests.post(
        "https://libretranslate.de/translate",
        data={"q": english_text, "source": "en", "target": "hi", "format": "text"}
    ).json()
    hindi_text = translate_res["translatedText"]

    hindi_audio = f"hindi_{uuid.uuid4()}.mp3"
    gTTS(hindi_text, lang="hi").save(hindi_audio)

    video_file = f"video_{uuid.uuid4()}.mp4"
    ydl_opts = {'format': 'mp4', 'outtmpl': video_file}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([yt_url])

    output_video = f"output_{uuid.uuid4()}.mp4"
    cmd = f"ffmpeg -i {video_file} -i {hindi_audio} -c:v copy -c:a aac -shortest {output_video} -y"
    subprocess.call(cmd, shell=True)

    return jsonify({
        "status": "success",
        "output_url": request.host_url + output_video
    })

@app.route("/<path:filename>")
def serve_file(filename):
    return app.send_static_file(filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
