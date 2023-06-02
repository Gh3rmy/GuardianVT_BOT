import os
import requests
import hashlib
from telegram.ext import Updater, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup

if not os.path.exists('downloads'):
    os.makedirs('downloads')


TOKEN = '<TU TOKEN DEL BOT DE TELEGRAM AQUI>'


VT_API_KEY = '<TU API DE VIRUS TOTAL AQUI>'



updater = Updater(TOKEN, use_context=True)

options_keyboard = ReplyKeyboardMarkup([['Sí', 'No']], one_time_keyboard=True)


respuestas = {
    'HOLA': '¡Hola que tal!', # primero el mensaje que quieres que el BOT encuentre y lo demas es lo que quieras que responda
}

def analyze_file(update, context):
    
    file_object = context.bot.get_file(update.message.document.file_id)

    
    file_path = f'downloads/{file_object.file_unique_id}'
    file_object.download(file_path)

    
    print("Ruta del archivo:", file_path)

    
    context.bot.send_message(chat_id=update.message.chat_id, text="¿Deseas analizar este archivo?", reply_markup=options_keyboard)

    
    context.chat_data['file_path'] = file_path
    context.chat_data['file_name'] = file_object.file_path.rsplit('/', 1)[-1]

def analyze_url(update, context):

    
    url = update.message.text

    
    url_scan_endpoint = 'https://www.virustotal.com/vtapi/v2/url/scan'
    params = {'apikey': VT_API_KEY, 'url': url}
    response = requests.post(url_scan_endpoint, params=params)

    if response.status_code == 200:
        
        response_json = response.json()
        permalink = response_json['permalink']
        scan_result = response_json['verbose_msg']

        
        message = f"URL: {url}\nResultado: {scan_result}\nVer más: {permalink}"
        context.bot.send_message(chat_id=update.message.chat_id, text=message)



def handle_message(update, context):
    if context.chat_data.get('file_path'):
        
        analyze_decision(update, context)
    else:
        
        if update.message.text.startswith('http://') or update.message.text.startswith('https://') or update.message.text.startswith('www.'):
            analyze_url(update, context)
        else:
            
            responder_mensaje(update, context)

def analyze_decision(update, context):
    
    decision = update.message.text

    if decision == 'Sí':
        
        file_path = context.chat_data.get('file_path', '')
        file_name = context.chat_data.get('file_name', '')

        
        if os.path.exists(file_path):
            
            md5_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()

            
            url = 'https://www.virustotal.com/vtapi/v2/file/scan'
            params = {'apikey': VT_API_KEY}
            files = {'file': open(file_path, 'rb')}
            response = requests.post(url, files=files, params=params)

            if response.status_code == 200:
                
                response_json = response.json()
                permalink = response_json['permalink']
                scan_result = response_json['verbose_msg']

                
                message = f"Archivo: {file_name}\nHash MD5: {md5_hash}\nResultado: {scan_result}\nVer más: {permalink}"
                context.bot.send_message(chat_id=update.message.chat_id, text=message)

            
            try:
                os.remove(file_path)
            except PermissionError:
                print("No se pudo eliminar el archivo. Está siendo utilizado por otro proceso.")
        else:
            print("El archivo no existe.")
    else:
        
        file_path = context.chat_data.get('file_path', '')
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except PermissionError:
                print("No se pudo eliminar el archivo. Está siendo utilizado por otro proceso.")

    
    context.chat_data.pop('file_path', None)
    context.chat_data.pop('file_name', None)


def responder_mensaje(update, context):
    mensaje = update.message.text.lower()  

    for palabra, respuesta in respuestas.items():
        if palabra in mensaje:
            context.bot.send_message(chat_id=update.message.chat_id, text=respuesta)
            break


def main():
    print("BOT Corriendo...")
    
    updater.dispatcher.add_handler(MessageHandler(Filters.document, analyze_file))

    
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
