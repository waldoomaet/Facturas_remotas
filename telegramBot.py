import logging
import magic
from pathlib import Path
import sys
import json
from Printer import Printer
from imageToPdf import imageToPdf
from camScan import camScan
from datetime import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# Enable logging
logging.basicConfig(
    filename='logs.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s \n\n',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

jsonData = open("configFile.json", 'r')
jsonData = json.loads(jsonData.read())
token = jsonData["token"]
allowedUsers = jsonData["Allowed_Users"]
docPath = Path(jsonData["Document_Folder_Path"])
imgPath = Path(jsonData["Image_Folder_Path"])
procImgPath = Path(jsonData["Processed_Image_Folder_Path"])
genPdf = Path(jsonData["Generated_PDF_Path"])
filesTypes = jsonData["File_Types"]
printerName = jsonData["Printer_name"]

genPdfLocal = ''
docPathLocal = ''

today = ''

FILE, COLOR, PICKPHOTO = range(3)

def printing(update, context):

    user = update.message.from_user

    if user.id in allowedUsers:
        update.message.reply_text(
            '¡Hola! Envia lo que deseas imprimir...'
        )
        return FILE

    else:
        update.message.reply_text("¡Usuario de Telegram invalido!")


def photo(update, context):

    user = update.message.from_user

    if user.id in allowedUsers:

        global today
        today = (datetime.now()).strftime("%d-%m-%Y %H-%M-%S")

        photo_file = update.message.photo[-1].get_file()
        if not imgPath.exists():
            imgPath.mkdir()
        
        imgPathLocal = imgPath / f"{today}.jpg"
        photo_file.download(imgPathLocal)
        logger.info(f"Photo of {user.full_name}: {today}.jpg")

        if not procImgPath.exists():
            procImgPath.mkdir()

        try:
            camScan(f"{today}.jpg", procImgPath, imgPathLocal)
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(procImgPath / f"{today}.jpg",'rb'))
        
        except Exception as err:
            logger.exception(f"Image {imgPathLocal} sended by {user.full_name} failed to process \n Exception message: {str(err)}")
            update.message.reply_text("Algo salio mal... Trata de volver a tomar la foto y enviala una vez mas.")
            return FILE
        
        reply_decision = [['Si', 'No']]
        update.message.reply_text("¡Bien! Esta es la foto que se va a imprimir, ¿te parece bien?",
        reply_markup=ReplyKeyboardMarkup(reply_decision, 
        resize_keyboard=True, 
        one_time_keyboard=True), )
        return PICKPHOTO
    
    else:
        update.message.reply_text("¡Usuario de Telegram invalido!")
        logger.error(f"Invalid user {user.full_name} tried to use bot")
        return ConversationHandler.END


def document(update, context):

    user = update.message.from_user

    if user.id in allowedUsers:

        global docPathLocal
        global today
        today = (datetime.now()).strftime("%d-%m-%Y %H-%M-%S")

        newFile = update.message.effective_attachment.get_file()

        if not docPath.exists():
            docPath.mkdir()
        
        docPathLocal = docPath / f"{today}.fil"
        newFile.download(docPathLocal)
        fileType = magic.from_file(str(docPathLocal))
        comma = fileType.find(',')

        try:
            extension = filesTypes[fileType[:comma]]
            logger.info(f"File type was {fileType[:comma]}")
            docPathLocal = Path(docPathLocal.replace(docPathLocal.with_suffix(extension)))
            logger.info(f"File of {user.full_name}: {docPathLocal}")
            reply_keyboard = [['Color', 'Blanco/negro']]
            update.message.reply_text("¡Perfecto! Ahora, ¿quieres imprimir a color o en blanco y negro?", 
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, 
            resize_keyboard=True, 
            one_time_keyboard=True), )
            return COLOR

        except(KeyError):
            logger.exception(f"Doc {docPathLocal} sended by {user.full_name} was an invalid file. File type: {fileType}")
            update.message.reply_text("Tipo de archivo invalido...")
        
        except Exception as err:
            logger.exception(f"Unknown error happened: {str(err)}")
            update.message.reply_text("Algo salio mal... Trata de volver a enviar el documento.")
            
    
    else:
        update.message.reply_text("¡Usuario de Telegram invalido!")
        logger.error(f"Invalid user {user.full_name} tried to use bot")
    
    return ConversationHandler.END


def pickPhoto(update, context):

    if update.message.text == 'Si':
        
        try:
            global genPdfLocal
            if not genPdf.exists():
                genPdf.mkdir()
            genPdfLocal = genPdf / f"{today}.pdf"
            imageToPdf(genPdfLocal, procImgPath / f"{today}.jpg")
            reply_color = [['Color', 'Blanco/negro']]
            update.message.reply_text("¡Perfecto! Ahora, ¿quieres imprimir a color o en blanco y negro?", 
            reply_markup=ReplyKeyboardMarkup(reply_color, 
            resize_keyboard=True, 
            one_time_keyboard=True), )
            return COLOR

        except Exception as err:
            logger.exception(f"Unknown error happened (prolly trying to create {genPdfLocal}): {str(err)}")
            update.message.reply_text("Algo salio mal... Trata de volver a tomar la foto y enviala una vez mas.")

    elif update.message.text == 'No':
        update.message.reply_text("Ups, en ese caso, por favor trata de volver a tomar la foto y enviala una vez mas.")
        return FILE
    
    return ConversationHandler.END


def color(update, context):
    try:
        user = update.message.from_user
        # printer = Printer(printerName)
        toPrintPath = ''

        global genPdfLocal
        global docPathLocal

        if genPdfLocal != '':
            toPrintPath = genPdfLocal
            genPdfLocal = ''
        
        else:
            toPrintPath = docPathLocal
            docPathLocal = ''

        if update.message.text == 'Color':
            logger.info(f"User {user.full_name} printed {toPrintPath} in color")
            # printer.setPrintColor("Color")

        elif update.message.text == 'Blanco/negro':
            logger.info(f"User {user.full_name} printed {toPrintPath} in black and white")
            # printer.setPrintColor("Blanco/negro")
        
        update.message.reply_text("¡Genial! Espera un momento a que termine el proceso de impresion...",
        reply_markup=ReplyKeyboardRemove(),)
        # printer.print(toPrintPath)

    except Exception as err:
        logger.exception(f"Unknown error happened: {str(err)}")

    return ConversationHandler.END


def cancel(update, context):

    user = update.message.from_user

    if user.id in allowedUsers:
        logger.info(f"User {user.full_name} canceled the conversation.")
        update.message.reply_text('¡Proceso cancelado!', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    else:
        update.message.reply_text("¡Usuario de Telegram invalido!")
        logger.error(f"Invalid user {user.full_name} tried to use bot")


def echo(update, context):

    user = update.message.from_user

    if user.id in allowedUsers:
        update.message.reply_text(
        '¡Hola! Recuerda que puedes imprimir lo que quieras al pulsar aqui (/Imprimir),'
        ' o al escribir el comando "/Imprimir"'
    )

    else:
        update.message.reply_text("¡Usuario de Telegram invalido!")


def main():
    updater = Updater(token)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('Imprimir', printing), CommandHandler('Start', printing),
        MessageHandler(Filters.document, document), MessageHandler(Filters.photo, photo)],
        states={
            FILE: [MessageHandler(Filters.document, document), MessageHandler(Filters.photo, photo)],
            COLOR: [MessageHandler(Filters.regex('^(Color|Blanco/negro)$'), color),],
            PICKPHOTO: [MessageHandler(Filters.regex('^(Si|No)$'), pickPhoto)],
        },
        fallbacks=[CommandHandler('Cancelar', cancel)],
    )
    dp.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    updater.start_polling()
    print("Ready")
    updater.idle()


if __name__ == '__main__':
    main()
