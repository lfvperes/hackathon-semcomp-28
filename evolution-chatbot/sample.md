## Enviar mensagem simples
Exemplo de requisição:
```
curl -X POST http://localhost:8081/message/sendText/testing \
  -H "Content-Type: application/json" \
  -H "apikey: Hrqp38CqMnDMw39c5g7k" \
  -d '{"number": "5516997453521", "text": "oi teste"}'

```
Resposta:
```
{"key":{"remoteJid":"5516997453521@s.whatsapp.net","fromMe":true,"id":"3EB0EFD331EA140F004CA75141E8169B9EED7629"},"pushName":"Você","status":"PENDING","message":{"conversation":"oi teste"},"messageType":"conversation","messageTimestamp":1760859935,"instanceId":"c9482c80-d4f3-4582-a484-1b5af43db273","source":"unknown"}
```

## Checando URL do Webhook
```
curl -X GET http://localhost:8081/webhook/find/testing \
  -H "apikey: Hrqp38CqMnDMw39c5g7k"
```

## Configurando Evolution API para conectar ao Webhook usando ip local do Docker container
```
curl --request POST \
  --url http://localhost:8081/webhook/set/testing \
  --header 'Content-Type: application/json' \
  --header 'apikey: Hrqp38CqMnDMw39c5g7k' \
  --data '{
  "webhook": {
    "enabled": true,
    "url": "http://172.17.0.1:5000/webhook",
    "webhookByEvents": true,
    "webhookBase64": false,
    "events": [
      "MESSAGES_UPSERT"
    ]
  }
}'
```


curl --request POST \
  --url http://localhost:8081/message/sendList/testing \
  --header 'Content-Type: application/json' \
  --header 'apikey: Hrqp38CqMnDMw39c5g7k' \
  --data '{
  "number": "5516997453521",
  "title": "Direct API Test",
  "description": "This is a test message sent directly from the terminal.",
  "buttonText": "Show List",
  "footerText": "Sent via cURL",
  "sections": [
    {
      "title": "Test Section",
      "rows": [
        {
          "title": "Option A",
          "description": "This is the first choice.",
          "rowId": "option_a"
        },
        {
          "title": "Option B",
          "description": "This is the second choice.",
          "rowId": "option_b"
        }
      ]
    }
  ]
}'


curl --request POST \
  --url http://localhost:8081/message/sendList/testing \
  --header 'Content-Type: application/json' \
  --header 'apikey: Hrqp38CqMnDMw39c5g7k' \
  --data '{
  "number": "5516997453521",
  "title": "Direct API Test",
  "description": "This is a test message sent directly from the terminal.",
  "buttonText": "Show List",
  "footerText": "Sent via cURL",
  "sections": [
    {
      "title": "Test Section",
      "rows": [
        {
          "title": "Option A",
          "description": "This is the first choice.",
          "rowId": "option_a"
        }
      ]
    }
  ]
}'


curl --request POST \
  --url http://localhost:8081/message/sendButtons/testing \
  --header 'Content-Type: application/json' \
  --header 'apikey: Hrqp38CqMnDMw39c5g7k' \
  --data '{
  "number": "5516997453521",
  "title": "Button Message Test",
  "description": "If you receive this, buttons are working.",
  "footer": "Sent via cURL",
  "buttons": [
    {
      "title": "button 1",
      "displayText": "display Button 1",
      "id": "btn_1_id"
    },
    {
      "title": "button 2"s
      "displayText": "display Button 2",
      "id": "btn_2_id"
    }
  ]
}'


curl --request POST \
  --url http://localhost:8081/message/sendButtons/testing \
  --header 'Content-Type: application/json' \
  --header 'apikey: Hrqp38CqMnDMw39c5g7k' \
  --data '{
  "number": "5516997453521",
  "title": "Button Message Test",
  "description": "If you receive this, buttons are working.",
  "footer": "Sent via cURL",
  "buttons": [
    {
      "type": "reply",
      "displayText": "Button 1",
      "id": "btn_1_id"
    },
    {
      "type": "reply",
      "displayText": "Button 2",
      "id": "btn_2_id"
    }
  ]
}'