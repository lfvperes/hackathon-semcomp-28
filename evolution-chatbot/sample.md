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