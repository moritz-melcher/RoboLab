#!/usr/bin/env python3

import unittest.mock
import paho.mqtt.client as mqtt
import uuid
import time

from communication import Communication
from planet import Planet
import json


class TestRoboLabCommunication(unittest.TestCase):
    @unittest.mock.patch('logging.Logger')
    def setUp(self, mock_logger):
        """
        Instantiates the communication class
        """
        client_id = 'YOURGROUPID-' + str(uuid.uuid4())  # Replace YOURGROUPID with your group ID
        client = mqtt.Client(client_id=client_id,  # Unique Client-ID to recognize our program
                             clean_session=False,  # We want to be remembered
                             protocol=mqtt.MQTTv311  # Define MQTT protocol version
                             )

        # Initialize your data structure here
        self.planet = Planet()
        self.communication = Communication(client, mock_logger, self.planet)
        self.test = None

    def on_message(self, client, data, message):
        """
        Handles the callback if any message arrived
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        payload = json.loads(message.payload.decode('utf-8'))
        self.logger.debug(json.dumps(payload, indent=2))
        self.test = payload


    def test_message_ready(self):
        """
        This test should check the syntax of the message type "ready"
        """
        self.fail('implement me!')

    def test_message_path(self):
        """
        This test should check the syntax of the message type "path"
        """
        self.communication.send_message("comtest/037", {"from": "client", "type": "path", "payload": {"startX": 0, "startY": 0, "startDirection": 0, "endX": 0, "endY": 0, "endDirection": 0, "pathStatus": "free"}})
        print("test message path")
        time.sleep(2)
        self.assertEqual({ "from": "debug", "type": "syntax", "payload": { "message": "Correct"}})

    def test_message_path_invalid(self):
        """
        This test should check the syntax of the message type "path" with errors/invalid data
        """
        self.fail('implement me!')

    def test_message_select(self):
        """
        This test should check the syntax of the message type "pathSelect"
        """
        self.fail('implement me!')

    def test_message_complete(self):
        """
        This test should check the syntax of the message type "explorationCompleted" or "targetReached"
        """
        self.fail('implement me!')


if __name__ == "__main__":
    unittest.main()
