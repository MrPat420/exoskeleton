import os
import uuid
from datetime import datetime
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from config.schemas import DS00Record
from core.ds00_state_engine import DS00Manager

class MobileBridge:
    def __init__(self, telegram_token: str, gemini_api_key: str = None):
        self.token = telegram_token
        self.client = genai.Client(api_key=gemini_api_key)
        self.manager = DS00Manager()
        
    async def _process_payload(self, contents: list, update: Update):
        try:
            response = self.client.models.generate_content(
                model="gemini-3.7-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction="Extract the core logic from this wetware dump into strict spatial RCA schemas.",
                    response_mime_type="application/json",
                    response_schema=DS00Record,
                    temperature=0.1
                )
            )
            
            record = DS00Record.model_validate_json(response.text)
            
            # Enforce deterministic tracking
            record.record_id = f"MOB-{uuid.uuid4().hex[:8].upper()}"
            record.timestamp = datetime.utcnow().isoformat() + "Z"
            record.origin_source = "Telegram_Mobile_Bridge"
            record.technical_metadata.append(f"chat_id_{update.message.chat_id}")
            
            # Write to disk and trigger Git push
            filepath = self.manager.write_record(record)
            sync_status = self.manager.sync_state(f"AUTO-SYNC: Mobile Ingress {record.record_id}")
            
            status_indicator = "🟢 Synced" if sync_status else "🟡 Local Only"
            
            await update.message.reply_text(
                f"✅ **DS-00 COMMITTED**\n"
                f"`{filepath}`\n"
                f"**Network State:** {status_indicator}",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ **INGRESS FAILURE:**\n`{str(e)}`", parse_mode="Markdown")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("[*] Processing Text Dump...")
        contents = [
            "EXTRACT DROPPED BLUEPRINTS AND ARCHITECTURE FROM THIS TEXT DUMP:\n",
            update.message.text
        ]
        await self._process_payload(contents, update)

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("[*] Downloading Audio Node...")
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        local_path = f"/tmp/{update.message.voice.file_id}.ogg"
        await voice_file.download_to_drive(local_path)
        
        await update.message.reply_text("[*] Uploading to Gemini Multimodal Engine...")
        uploaded_file = self.client.files.upload(file=local_path)
        
        contents = [
            uploaded_file,
            "EXTRACT DROPPED BLUEPRINTS AND ARCHITECTURE FROM THIS VOICE AUDIO DUMP:"
        ]
        await self._process_payload(contents, update)
        
        os.remove(local_path)
        # The file remains in Google's temporary storage linked to the API key for 48 hours.
        # Can be explicitly deleted via self.client.files.delete(name=uploaded_file.name) if strict OPSEC required.

    def run(self):
        app = ApplicationBuilder().token(self.token).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_text))
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        app.run_polling()
