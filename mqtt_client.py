from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))

# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)

def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))

# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    # global received_count
    # received_count += 1
    # if received_count == cmdData.input_count:
    #     received_all_event.set()

# Callback when the connection successfully connects
def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print("Connection Successful with return code: {} session present: {}".format(callback_data.return_code, callback_data.session_present))

# Callback when a connection attempt fails
def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print("Connection failed with error code: {}".format(callback_data.error))

# Callback when a connection has been disconnected or shutdown successfully
def on_connection_closed(connection, callback_data):
    print("Connection closed")

class mqtt_client:
    def __init__(self, endpoint, cert, key, ca_file, client_id, on_connection_interrupted=on_connection_interrupted, on_connection_resumed=on_connection_resumed, proxy_options=None, on_connection_success=on_connection_success, on_connection_failure=on_connection_failure, on_connection_closed=on_connection_closed):
        # Connection parameters
        self.endpoint = endpoint
        self.port = None
        self.cert = cert
        self.key = key
        self.ca_file = ca_file
        self.on_connection_interrupted = on_connection_interrupted
        self.on_connection_resumed = on_connection_resumed
        self.client_id = client_id
        self.proxy_options = proxy_options
        self.on_connection_success = on_connection_success
        self.on_connection_failure = on_connection_failure
        self.on_connection_closed = on_connection_closed
        # MQTT Connection
        self.connection = None


    def connect(self):
        self.connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            port=self.port,
            cert_filepath=self.cert,
            pri_key_filepath=self.key,
            ca_filepath=self.ca_file,
            client_id=self.client_id,
            clean_session=False,
            keep_alive_secs=30,
            on_connection_interrupted=self.on_connection_interrupted,
            on_connection_resumed=self.on_connection_resumed,
            http_proxy_options=self.proxy_options,
            on_connection_success=self.on_connection_success,
            on_connection_failure=self.on_connection_failure,
            on_connection_closed=self.on_connection_closed
        )
        print(f"Connecting to {self.endpoint} with client ID '{self.client_id}'...")
        connect_future = self.connection.connect()
        connect_future.result()  # Wait until a connection result is available.
        print("Connected to {}".format(self.endpoint))
    
    def subscribe(self, topic, on_message_received=on_message_received):
        print("Subscribing to topic '{}'...".format(topic))
        subscribe_future, _ = self.connection.subscribe(
            topic=topic,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=on_message_received
        )
        subscribe_result = subscribe_future.result() # Wait for subscription to complete
        print("Subscribed with {}".format(subscribe_result['qos']))
    
    def publish(self, message, topic, message_count=1):
        print("Sending message '{}' to topic '{}'...".format(message, topic))
        for _ in range(message_count):
            publish_future, packet_id = self.connection.publish(
                topic=topic,
                payload=message,
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            if 'packet_id' in publish_future.result(): # Wait for publish to complete
                print("Message published to topic '{}'".format(topic))

    def disconnect(self):
        print("Disconnecting from {}".format(self.endpoint))
        disconnect_future = self.connection.disconnect()
        disconnect_future.result()
        print("Disconnected!")
