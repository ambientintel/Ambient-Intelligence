from mqtt_client import mqtt_client as client
import json

if __name__ == '__main__':

    endpoint = 'a2c23jts9lq6zy-ats.iot.eu-north-1.amazonaws.com'
    client_id = 'thing05'
    cert = f'./certs/{client_id}.cert.pem'
    key = f'./certs/{client_id}.private.key'
    ca_file = './certs/root-CA.crt'
    topic = 'dev/ambient-intelligence-poc-topic/global'

    # Load message from message.json
    with open('message.json', 'r') as f:
        message_data = json.load(f)
    message_data['device'] = client_id  # Ensure device ID is set
    message_data['data'][1]['fallAlert'] = True
    message_str = json.dumps(message_data)  # Convert to string for MQTT payload

    mqtt_client = client(endpoint, cert, key, ca_file, client_id)
    mqtt_client.connect()
    mqtt_client.subscribe(topic)
    mqtt_client.publish(message_str, topic, message_count=1)
    mqtt_client.disconnect()

