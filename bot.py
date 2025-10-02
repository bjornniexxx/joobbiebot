import logging
# --- Selenium Imports (NUEVO) ---
# Estas son las herramientas para controlar el navegador
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuración del Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Sistema de Autorización ---
# El ID del propietario. Las personas deberán enviar este número para acceder.
OWNER_ID = 6731555880

# Usaremos "sets" para guardar los IDs de los usuarios. Es más eficiente.
# authorized_users: Guarda a quienes ya tienen acceso. El propietario siempre tiene acceso.
authorized_users = {OWNER_ID}
# pending_authorization: Guarda a quienes han usado /start y deben enviar el ID.
pending_authorization = set()

# --- LÓGICA DE GENERACIÓN DE CUENTAS (NUEVO) ---

def generar_password(longitud=12):
    """Genera una contraseña segura y aleatoria."""
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
    """
    Automatiza la creación de una cuenta en Tidal usando Selenium.
    Retorna (email, password) si tiene éxito, o (None, None) si falla.
    """
    logging.info("Iniciando la creación de cuenta de Tidal...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Esta ruta es estándar en VPS con Linux
    service = Service(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # 1. Obtener correo temporal de 1secmail.com
        response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        temp_email = response.json()[0]
        logging.info(f"Correo temporal obtenido: {temp_email}")

        # 2. Navegar a la página de registro de Tidal
        driver.get("https://tidal.com/try-now")
        time.sleep(4)

        # 3. Rellenar formulario
        driver.find_element(By.ID, "email").send_keys(temp_email)
        time.sleep(1)
        driver.find_element(By.XPATH, '//*[@id="layout-content"]/div/div/div/div/div/form/button').click()
        time.sleep(6) # Espera crucial para que cargue la siguiente página

        new_password = generar_password()
        driver.find_element(By.ID, "password").send_keys(new_password)
        time.sleep(1)
        
        driver.find_element(By.ID, "birth-date-month").send_keys("08")
        driver.find_element(By.ID, "birth-date-day").send_keys("12")
        driver.find_element(By.ID, "birth-date-year").send_keys("1994")
        time.sleep(1)

        driver.find_element(By.XPATH, '//*[@id="layout-content"]/div/div/div[2]/div/div/form/button').click()
        logging.info("Formulario de registro enviado.")
        time.sleep(10) # Espera para asegurar que la cuenta se procese

        # Verificación final (opcional pero recomendado)
        if "browse" in driver.current_url:
             logging.info("Registro exitoso, URL de navegación detectada.")
             return temp_email, new_password
        else:
             logging.warning("El registro podría haber fallado, no se redirigió a la página principal.")
             # Aún así devolvemos los datos, puede que haya funcionado.
             return temp_email, new_password

    except Exception as e:
        logging.error(f"Error drástico en Selenium: {e}")
        driver.save_screenshot('error_tidal.png') # Guarda una foto del error
        return None, None
    finally:
        driver.quit()
        logging.info("Navegador de Selenium cerrado.")

# --- Definición de Comandos ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función que se ejecuta cuando un usuario envía /start."""
    user = update.effective_user

    # 1. Primero, revisamos si el usuario ya está autorizado.
    if user.id in authorized_users:
        await update.message.reply_html(f"¡Hola de nuevo, {user.mention_html()}! Ya tienes acceso a mis funciones :3")
        return

    # 2. Si no está autorizado, le pedimos el ID y lo añadimos a la lista de espera.
    pending_authorization.add(user.id)
    mensaje_bienvenida = (
        f"Bienvenido {user.mention_html()} (★＞∇＜)ﾉ\n\n"
        "Antes de continuar con mis funciones, envíame el id de mi propietario en tu siguiente mensaje para verificar que tienes permiso, por favor y gracias."
    )
    await update.message.reply_html(mensaje_bienvenida)

async def tidal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para el comando /tidal (NUEVO)"""
    if update.effective_user.id not in authorized_users: return

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
            "Una captura de pantalla del error (`error_tidal.png`) se ha guardado en el servidor para depuración."
        )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra los comandos disponibles solo a usuarios autorizados."""
    user = update.effective_user

    # Este es el "guardia". Si el usuario no está en la lista, el comando no hace nada.
    if user.id not in authorized_users:
        return

    mensaje_ayuda = (
        "<b>Comandos Disponibles:</b>\n\n"
        "<code>/ayuda</code> - Muestra este mensaje de ayuda.\n"
        "<code>/tidal</code> - Inicia la creación de una cuenta de Tidal."
    )
    await update.message.reply_html(mensaje_ayuda)


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja los mensajes de texto para la verificación."""
    user = update.effective_user
    text = update.message.text

    # Solo procesamos el mensaje si el usuario está en la lista de espera.
    if user.id in pending_authorization:
        # Verificamos si el mensaje es el ID correcto.
        if text.strip() == str(OWNER_ID):
            # ¡Correcto! Lo añadimos a los usuarios autorizados.
            authorized_users.add(user.id)
            # Y lo quitamos de la lista de espera.
            pending_authorization.remove(user.id)
            
            mensaje_exito = "Correcto! ✅️ Ya puedes utilizar mis funciones, cuando necesites ayuda para saber mis comandos solo ejecuta '/ayuda'."
            await update.message.reply_text(mensaje_exito)
        # Si el ID es incorrecto, no hacemos nada, tal como pediste.


# --- Función Principal (main) ---

def main() -> None:
    """Esta función inicia el bot."""
    TOKEN = "8390821993:AAHk5hZ7FuH6Gq2335o7ru_vCWRC83IoqEE"
    
    application = Application.builder().token(TOKEN).build()

    # Registramos los comandos.
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
        application.add_handler(CommandHandler("tidal", tidal_command))


    # Añadimos un manejador de mensajes. Este escuchará por texto normal (no comandos).
    # Le damos una prioridad más baja (10) para que los comandos se revisen primero.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages), group=10)

    print("El bot está iniciando...")
    application.run_polling()
    print("El bot se ha detenido.")

if __name__ == '__main__':
    main()