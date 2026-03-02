import os
import fitz
import asyncio
import logging
import google.genai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 1. CONFIGURACIÓN DE LOGS (Para ver qué pasa en la consola de Render)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# 2. VARIABLES DE ENTORNO (Se configuran en el panel de Render o Railway)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")

# 3. CONFIGURAR GEMINI

def leer_pdf(ruta_pdf):
    try:
        documento = fitz.open(ruta_pdf)
        texto_completo = ""
        for pagina in documento:
            texto_completo += pagina.get_text()
        return texto_completo
    except Exception as e:
        print(f"Error al leer el PDF: {e}")
        return ""

# Cargamos el contenido del PDF
contexto_pdf = leer_pdf("Hybrid Training Research.pdf")

# Aquí pegas la personalidad de tu Gem
SYSTEM_INSTRUCTION = """
You are Dr. Aris Thorne, a globally recognized expert in the highly specialized field of hybrid athletic development, with a unique focus on synergistic training across running (especially trail running), climbing, and supportive strength & conditioning. Your unparalleled expertise is sought by elite athletes and dedicated enthusiasts alike who aim to transcend traditional training boundaries and achieve peak performance in multi-disciplinary endeavors.
You are not merely a coach; you are a diagnostician of movement, a sculptor of resilience, and a master of performance optimization. Your approach is deeply rooted in your dual qualifications as a certified strength and conditioning specialist (CSCS) and a licensed physiotherapist (PT/DPT), allowing you to not only elevate athletic potential but also to meticulously prevent and rehabilitate injuries.
Your core philosophy revolves around the principle that while running (particularly trail running) and climbing are the primary performance objectives, intelligent, sport-specific weightlifting is the foundational bedrock that enhances endurance, power, injury resilience, and overall athletic longevity in both disciplines. You eschew generic routines, instead crafting bespoke programs that interweave these modalities into a seamless, progressive, and highly effective training tapestry.
Your ideal client is someone who:
Aspires to significant improvements in trail running performance (speed, endurance, technical proficiency).
Seeks to elevate their climbing ability (strength, technique, endurance, injury prevention).
Understands the crucial role of targeted strength training as a catalyst for these primary goals.
Is committed to a holistic, intelligent, and progressive training journey.
Values a coach who can not only push them to their limits but also safeguard their physical well-being.
When providing advice or crafting a plan, you will demonstrate:
Deep understanding of biomechanics: How running mechanics impact climbing, and vice-versa, with an eye on efficiency and injury prevention.
Physiological expertise: Tailoring cardiovascular and strength adaptations for both endurance running and power/endurance climbing.
Injury prevention and rehabilitation mastery: Integrating prehab, mobility, and recovery strategies as core components, and providing expert guidance on managing common running and climbing-related issues.
Advanced periodization strategies: Designing long-term plans that strategically ebb and flow, allowing for peak performance at specific events while preventing overtraining.
Nutritional and recovery insights: Providing guidance on fueling multi-disciplinary training and optimizing recovery.
Mental fortitude development: Understanding the psychological demands of both running and climbing and incorporating strategies for mental resilience.
Data-driven approach: Utilizing metrics (when available) to inform training adjustments and monitor progress.
Your ultimate goal is to create "Peak Performance Hybrids" – athletes who are robust, adaptable, and excel in the unique demands of combined running and climbing pursuits, all while maintaining optimal physical health and longevity.
"""

client = genai.Client(api_key=GEMINI_API_KEY)

# 4. FUNCIÓN: RESPONDER A TUS MENSAJES
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id
    
    # Esto te servirá para saber tu ID la primera vez
    if str(chat_id) != MY_CHAT_ID:
        print(f"⚠️ ATENCIÓN: Tu Chat ID es {chat_id}. Cópialo y ponlo en tus variables de entorno.")

    try:
        # Generar respuesta con Gemini usando la nueva librería genai
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
            config={'system_instruction': SYSTEM_INSTRUCTION}
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error en Gemini: {e}")
        await update.message.reply_text("Ups, mi cerebro se ha colgado un segundo. ¿Me repites eso?")

# 5. FUNCIÓN: PROACTIVIDAD (EL BOT TOMA LA INICIATIVA)
async def proactivity_loop(app: Application):
    logging.info("Bucle de proactividad iniciado.")
    while True:
        # Espera 6 horas entre chequeos (21600 segundos)
        # Para probarlo rápido en tu PC, cámbialo a 30 segundos
        await asyncio.sleep(21600) 
        
        prompt_iniciativa = (
            "No hemos hablado en horas. Basado en tu personalidad, "
            "escríbeme un mensaje corto para retomar la conversación o "
            "aportarme algo de valor ahora mismo."
        )
        
        try:
            check = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt_iniciativa,
                config={'system_instruction': SYSTEM_INSTRUCTION}
            )
            if MY_CHAT_ID:
                await app.bot.send_message(chat_id=MY_CHAT_ID, text=check.text)
                logging.info("Mensaje proactivo enviado con éxito.")
        except Exception as e:
            logging.error(f"Error en el bucle proactivo: {e}")

# 6. INICIO DEL BOT
if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        print("❌ ERROR: No se encontró el TELEGRAM_TOKEN.")
    else:
        # Construir la aplicación de Telegram
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Añadir el manejador de mensajes de texto
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # IMPORTANTE: Render exige que abramos el puerto para Web Services antes de que empiece el Bot (porque run_polling es bloqueante)
        port = int(os.environ.get("PORT", "8080"))

        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Bot is alive!")

        def run_dummy_server():
            httpd = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
            print(f"🌍 Falso servidor web escuchando en el puerto {port}")
            httpd.serve_forever()

        # Arrancamos el falso servidor en un hilo (thread) separado, así no bloquea a Telegram
        server_thread = threading.Thread(target=run_dummy_server, daemon=True)
        server_thread.start()

        async def on_startup(app: Application):
            asyncio.create_task(proactivity_loop(app))
            print("🚀 Tarea de proactividad iniciada en el fondo...")
            
        app.post_init = on_startup

        print("🚀 Bot encendido y escuchando a Telegram...")
        app.run_polling()