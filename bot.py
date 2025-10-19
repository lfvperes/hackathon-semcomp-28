from uniao_noticias_request import AlphaVantageNewsProcessor

processor = AlphaVantageNewsProcessor()

from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Evolution API configuration
EVOLUTION_API_URL = "http://localhost:8081"
INSTANCE_NAME = "testing"
API_KEY = "Hrqp38CqMnDMw39c5g7k"

# A simple in-memory dictionary to store user conversation states
# In a real app, you'd use a database like Redis for this
user_states = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # Debugging: Always print the received data
    print("✅ Raw webhook received:")
    print(json.dumps(data, indent=2))
    
    # Basic validation - check if data exists
    if not data:
        print("❌ Error: No JSON data received")
        return jsonify({"status": "error", "message": "No data"}), 400
    
    # Check if it's a message event
    if data.get('event') == 'messages.upsert':
        message_data = data.get('data', {})
        
        print("🟡 Processing 'messages.upsert' event")
        print(f"🟡 Full message data: {json.dumps(message_data, indent=2)}")
        
        # SAFELY check if this is a conversation message with text
        # Using get() with defaults to avoid 'undefined' errors
        message_type = message_data.get('messageType', '')
        remote_jid = message_data.get('key', {}).get('remoteJid', '')
        message_content = message_data.get('message', {})
        conversation_text = message_content.get('conversation', '') if message_content else ''
        
        print(f"🟡 Message type: {message_type}")
        print(f"🟡 From: {remote_jid}")
        print(f"🟡 Text: '{conversation_text}'")
        
        # Only process if we have a conversation message with text
        if (message_type == 'conversation' and 
            remote_jid and 
            conversation_text):
            
            text = conversation_text.lower()
            sender = remote_jid
            
            print(f"✅ Valid message from {sender}: {text}")
            
            # --- CONVERSATION LOGIC ---

            # 1. Check if the user is in a known state (e.g., we're waiting for their reply)
            state = user_states.get(sender)
            if state == 'awaiting_investment_choice':
                if text == '1' or 'option 1' in text:
                    updated_stocks(sender)
                    del user_states[sender]  # Clear the state
                elif text == '2' or 'option 2' in text:
                    see_portfolio(sender)
                    del user_states[sender]  # Clear the state
                elif text == '3' or 'option 2' in text:
                    recommendations(sender)
                    del user_states[sender]  # Clear the state
                else:
                    send_message(sender, "Sorry, I didn't understand that. Please reply with '1' or '2'.")

            # 2. If the user is not in a state, check for trigger words
            elif "investimento" in text:
                # Set the user's state
                user_states[sender] = 'awaiting_investment_choice'

                # Ask the question
                reply_text = (
                    "Você está interessado em investimentos! Por favor escolha uma opção e responda com o número:\n\n"
                    "1. Ver cotações atualizadas\n"
                    "2. Ver minha carteira\n"
                    "3. Ver recomendações"
                )
                send_message(sender, reply_text)

            # 3. A simple fallback for testing
            elif "oi" in text:
                reply_text = "Oi! Responda com a palavra \"investimento\" para continuar."
                print(f"✅ Triggering reply: {reply_text}")
                send_message(sender, reply_text)

            else:
                print(f"🔶 Message ignored, no trigger words found")
        else:
            print("🔶 Not a standard conversation message, ignoring")
    else:
        print(f"🔶 Other event type: {data.get('event')}")
    
    return jsonify({"status": "ok"})

def send_message(to, text):
    """Send a message via Evolution API"""
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    data = {
        "number": to.split('@')[0],  # Remove the @s.whatsapp.net part
        "text": text
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"Sent message response: {response.status_code}")
    return response

def send_list(to, title, description, button_text, footer_text, sections):
    """Send a list message via Evolution API"""
    url = f"{EVOLUTION_API_URL}/message/sendList/{INSTANCE_NAME}"
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    
    # The 'values' key in the API corresponds to our 'sections'
    data = {
        "number": to.split('@')[0],
        "title": title,
        "description": description,
        "buttonText": button_text,
        "footerText": footer_text,
        "sections": sections
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"Sent list response: {response.status_code}")
    print(f"Response body: {response.text}") # Added for more detailed debugging
    return response
def updated_stocks(sender):
    """Placeholder function for when the user chooses option 1."""
    print(f"✅ Handling 'See stock news' for {sender}")
    # Here you would call your method from uniao_noticias_request
    result = ""
    if processor.fazer_requisicao_api():
        # 2. Salvar dados brutos
        processor.salvar_dados_brutos()
        
        # 3. Processar dados
        if processor.processar_dados():
            # 4. Mostrar resumo
            result = processor.mostrar_resumo()
            
            # 5. Exportar resultados
            processor.exportar_resultados()
        
    send_message(sender, result)
    # Add your news fetching logic here

def see_portfolio(sender):
    """Placeholder function for when the user chooses option 2."""
    print(f"✅ Handling 'Check my portfolio' for {sender}")
    # Here you would add your portfolio logic
    reply_text = "You chose to check your portfolio! Looking that up for you..."
    send_message(sender, reply_text)
    # Add your portfolio logic here

def recommendations(sender):
    print(f"✅ Handling 'See recommendations' for {sender}")

    reply_text = "Você escolheu recomendações. Aqui estão: "
    send_message(sender, reply_text)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)