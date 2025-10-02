import logging
import time
import random
import string
import requests

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

OWNER_ID = 6731555880
authorized_users = {OWNER_ID}
pending_authorization = set()

# --- LÓGICA DE GENERACIÓN DE CUENTAS ---

def generar_password(longitud=12):
    caracteres = string.ascii_letters + string.digits + string.punctuation
    password_lista = [
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice(string.punctuation)
    ]
    password_lista.extend(random.choices(caracteres, k=longitud - 3))
    random.shuffle(password_lista)
    return ''.join(password_lista)

def crear_cuenta_tidal():
    logging.info("Dentro de crear_cuenta_tidal(): Iniciando proceso.") # <-- PRUEBA
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        temp_email = response.json()[0]
        logging.info(f"Dentro de crear_cuenta_tidal(): Correo temporal obtenido: {temp_email}") # <-- PRUEBA

        driver.get("https://tidal.com/try-now")
        time.sleep(4)

        driver.find_element(By.ID, "email").send_keys(temp_email)
        time.sleep(1)
        driver.find_element(By.XPATH, '//*[@id="layout-content"]/div/div/div/div/div/form/button').click()
        time.sleep(6)

        new_password = generar_password()
        driver.find_element(By.ID, "password").send_keys(new_password)
        time.sleep(1)
        
        driver.find_element(By.ID, "birth-date-month").send_keys("08")
        driver.find_element(By.ID, "birth-date-day").send_keys("12")
        driver.find_element(By.ID, "birth-date-year").send_keys("1994")
        time.sleep(1)

        driver.find_element(By.XPATH, '//*[@id="layout-content"]/div/div/div[2]/div/div/form/button').click()
        logging.info("Dentro de crear_cuenta_tidal(): Formulario de registro enviado.") # <-- PRUEBA
        time.sleep(10)
        
        if "browse" in driver.current_url:
             logging.info("Dentro de crear_cuenta_tidal(): Registro exitoso.") # <-- PRUEBA
             return temp_email, new_password
        else:
             logging.warning("Dentro de crear_cuenta_tidal(): El registro podría haber fallado.") # <-- PRUEBA
             return temp_email, new_password

    except Exception as e:
        logging.error(f"Dentro de crear_cuenta_tidal(): Error drástico en Selenium: {e}") # <-- PRUEBA
        driver.save_screenshot('error_tidal.png')
        return None, None
    finally:
        driver.quit()
        logging.info("Dentro de crear_cuenta_tidal(): Navegador de Selenium cerrado.") # <-- PRUEBA


# --- COMANDOS DEL BOT DE TELEGRAM ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id in authorized_users:
        await update.message.reply_html(f"¡Hola de nuevo, {user.mention_html()}! Ya tienes acceso a mis funciones. 😉")
        return
    
    pending_authorization.add(user.id)
    mensaje_bienvenida = (
        f"Bienvenido {user.mention_html()} (★＞∇＜)ﾉ\n\n"
        "Antes de continuar con mis funciones, envíame el id de mi propietario en tu siguiente mensaje para verificar que tienes permiso, por favor y gracias."
    )
    await update.message.reply_html(mensaje_bienvenida)


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in authorized_users: return
    mensaje_ayuda = (
        "<b>Comandos Disponibles:</b>\n\n"
        "<code>/ayuda</code> - Muestra este mensaje de ayuda.\n"
        "<code>/tidal</code> - Inicia la creación de una cuenta de Tidal."
    )
    await update.message.reply_html(mensaje_ayuda)


async def tidal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para el comando /tidal"""
    user_id = update.effective_user.id
    logging.info(f"Comando /tidal recibido del usuario {user_id}") # <-- PRUEBA

    if user_id not in authorized_users: 
        logging.warning(f"Acceso denegado para {user_id}. No está en la lista de autorizados.") # <-- PRUEBA
        return

    logging.info(f"Usuario {user_id} autorizado. Procediendo a llamar a crear_cuenta_tidal().") # <-- PRUEBA
    msg = await update.message.reply_text('⚙️ Creando tu cuenta de Tidal... Esto puede tardar hasta un minuto. Por favor, espera.')
    
    email, password = crear_cuenta_tidal()

    if email and password:
        texto_respuesta = (
            f"<b>¡Cuenta de Tidal creada con éxito!</b> ✅\n\n"
            f"✉️ <b>Correo:</b> <code>{email}</code>\n"
            f"🔑 <b>Contraseña:</b> <code>{password}</code>"
        )
        await msg.edit_text(texto_respuesta, parse_mode='HTML')
    else:
        await msg.edit_text(
            "❌ Hubo un error al crear la cuenta.\n\n"
            "Esto puede deberse a un cambio en la página de Tidal o a un CAPTCHA. "
            "Revisa los logs para más detalles."
        )


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = update.message.text
    if user.id in pending_authorization:
        if text.strip() == str(OWNER_ID):
            authorized_users.add(user.id)
            pending_authorization.remove(user.id)
            await update.message.reply_text("Correcto! ✅️ Ya puedes utilizar mis funciones, cuando necesites ayuda para saber mis comandos solo ejecuta '/ayuda'.")


# --- FUNCIÓN PRINCIPAL ---

def main() -> None:
    TOKEN = "TU_TOKEN_AQUI"
    logging.info("Función main() iniciada. Creando aplicación...") # <-- PRUEBA
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("tidal", tidal_command))
    logging.info("Handlers para /start, /ayuda, y /tidal registrados.") # <-- PRUEBA
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages), group=10)

    print("El bot está iniciando...")
    application.run_polling()


if __name__ == '__main__':
    main()