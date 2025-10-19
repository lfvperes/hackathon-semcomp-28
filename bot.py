from teste_unificado_V3 import AlphaVantageProcessor, demo_mostrar_carteira, demo_gerar_recomendacoes
# from uniao_noticias_request import AlphaVantageNewsProcessor

# This processor instance is now only used for the simple news lookup.
# The recommendation engine uses its own internal instance.
processor = AlphaVantageProcessor()

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
                elif text == '3' or 'recomenda' in text:
                    recommendations(sender)
                    del user_states[sender]  # Clear the state
                else:
                    send_message(sender, "Opção inválida. Por favor, responda com '1', '2' ou '3'.")
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
    """Asks for a ticker, but for the demo, uses a hardcoded list."""
    print(f"✅ Handling 'See updated stocks' for {sender}")

    # In a real app, you would ask the user for a stock ticker.
    # For this demo, we'll just show news for a few popular ones.
    send_message(sender, "Buscando notícias para as ações mais populares (AAPL, MSFT, GOOGL)...")

    tickers = "AAPL,MSFT,GOOGL"
    sucesso, msg = processor.buscar_noticias(tickers)
    if sucesso:
        processor.processar_noticias()
        # We'll just show the summary for the first ticker as an example
        resumo = processor.mostrar_resumo_noticias(tickers.split(',')[0])
        send_message(sender, resumo)
    else:
        send_message(sender, f"Não foi possível buscar as notícias no momento: {msg}")
def see_portfolio(sender):
    """Shows the user's hardcoded portfolio by calling the demo function."""
    print(f"✅ Handling 'Check my portfolio' for {sender}")

    # For this demo, we'll assume the user is client '0001'
    cliente_id = '0001'

    # Call the refactored function from the other script
    portfolio_info = demo_mostrar_carteira(cliente_id)
    send_message(sender, portfolio_info)


def recommendations(sender):
    """Generates and shows recommendations by calling the demo function."""
    print(f"✅ Handling 'See recommendations' for {sender}")

    # For this demo, we'll assume the user is client '0001'
    cliente_id = '0001'

    # Send a waiting message because this can take a long time due to API calls
    send_message(sender, "Estou preparando suas recomendações personalizadas. Isso pode levar um momento...")

    # Call the refactored, long-running function
    recommendation_summary = demo_gerar_recomendacoes(cliente_id)

    # Note: This message might be very long for WhatsApp.
    # In a real app, you might need to split it into multiple messages.
    send_message(sender, recommendation_summary)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)