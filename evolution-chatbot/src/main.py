from flask import Flask, request, jsonify
import requests
import os

# --- Configuration ---
# It's best practice to use environment variables for sensitive data.
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "your_super_secret_api_key")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "my-instance")

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Listens for incoming messages from the Evolution API."""
    data = request.json
    print("Received webhook:", data)

    # We are interested in new text messages
    if data.get('event') == 'messages.upsert' and data['data'].get('message'):
        message_data = data['data']
        message = message_data.get('message', {})
        
        # Extract sender and text from the message payload
        sender = message_data.get('key', {}).get('remoteJid')
        text_content = message.get('conversation') or message.get('extendedTextMessage', {}).get('text')

        # Ensure we have a sender and a message, and it's not from us
        if sender and text_content and not message_data.get('key', {}).get('fromMe'):
            print(f"Received message '{text_content}' from {sender}")
            
            # --- Your chatbot logic starts here ---
            # For now, we'll just echo the message back.
            reply_text = f"You said: {text_content}"
            
            send_message(sender, reply_text)
            # --- Your chatbot logic ends here ---

    return jsonify({"status": "ok"}), 200

def send_message(recipient, message):
    """Sends a text message using the Evolution API."""
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": recipient,
        "options": {
            "delay": 1200,
            "presence": "composing"
        },
        "textMessage": {
            "text": message
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        print("Message sent successfully:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

if __name__ == '__main__':
    # You can change the port as needed
    app.run(port=5001, debug=True)