from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Evolution API configuration
EVOLUTION_API_URL = "http://localhost:8081"
INSTANCE_NAME = "testing"
API_KEY = "Hrqp38CqMnDMw39c5g7k"

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
            
            # Check for "hello" anywhere in the message
            if "hello" in text:
                reply_text = "YOU JUST LOST THE GAME"
                # reply_text = "Hello! I received your message and my Python script is working!"
                print(f"✅ Triggering reply: {reply_text}")
                send_message(sender, reply_text)
            else:
                print(f"🔶 Message ignored, no 'hello' found")
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)