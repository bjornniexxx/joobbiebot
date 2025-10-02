import logging
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

    # Añadimos un manejador de mensajes. Este escuchará por texto normal (no comandos).
    # Le damos una prioridad más baja (10) para que los comandos se revisen primero.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages), group=10)

    print("El bot está iniciando...")
    application.run_polling()
    print("El bot se ha detenido.")

if __name__ == '__main__':
    main()
