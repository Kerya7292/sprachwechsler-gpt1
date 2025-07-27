import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InputFile
from openai import OpenAI
from tempfile import NamedTemporaryFile

logging.basicConfig(level=logging.INFO)

# Токены
BOT_TOKEN = "7344998076:AAEt-Yv0YPexiH44lW9HCZ1FevE18tNpBhw"
OPENAI_API_KEY = "sk_42cacd4ab7a890e56a0f6203f31e6fee5e6a2787d3e9f9a1"

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
client = OpenAI(api_key=OPENAI_API_KEY)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("Привет! Отправь голосовое сообщение — я переведу и озвучу на немецком.")

@dp.message_handler(content_types=types.ContentType.VOICE)
async def voice_handler(message: types.Message):
    file_id = message.voice.file_id
    voice_file = await bot.get_file(file_id)
    file_path = voice_file.file_path
    file = await bot.download_file(file_path)

    with NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        text = transcript.strip()

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Отвечай на немецком языке."},
                {"role": "user", "content": text}
            ]
        )
        reply = completion.choices[0].message.content

        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=reply
        )

        with NamedTemporaryFile(suffix=".mp3", delete=False) as audio_out:
            speech_response.stream_to_file(audio_out.name)
            await message.reply_audio(audio=InputFile(audio_out.name), caption=reply)

    except Exception as e:
        await message.reply(f"Ошибка: {e}")
    finally:
        os.remove(tmp_path)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)