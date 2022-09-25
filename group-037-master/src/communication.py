#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
from decimal import ExtendedContext
import json
import platform
from pydoc_data.topics import topics
import ssl
import paho.mqtt.client as mqtt
import time

# Fix: SSL certificate problem on macOS
if all(platform.mac_ver()):
    from OpenSSL import SSL


class Communication:
    """
    Class to hold the MQTT client communication
    Feel free to add functions and update the constructor to satisfy your requirements and
    thereby solve the task according to the specifications
    """

    def __init__(self, mqtt_client, logger, planet):
        """
        Initializes communication module, connect to server, subscribe, etc.
        :param mqtt_client: paho.mqtt.client.Client
        :param logger: logging.Logger
        """
        # DO NOT CHANGE THE SETUP HERE
        self.client = mqtt_client
        self.logger = logger
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.client.on_message = self.safe_on_message_handler
        # Add your client setup here
        self.client.on_connect = self.on_connect # callback to on_connect method
        
        
        self.client.username_pw_set('037', password='309gazKt3A') #group information 
        self.client.connect('mothership.inf.tu-dresden.de', port = 8883) #connection setup
        topic = 'explorer/037'
        self.topic = topic #topic variable to change subscription dynammically
        self.client.subscribe(topic, qos=2) #initial subscription 
        self.planet = planet #needed to use add_path method in communication.py
        self.explorationDone = False #variable to end big while loop in main.py 
        self.pathSelectFinished = False #variable to help wait for communication process to end on each node 

        self.pathSelect = { #declaration for path select message and to cache if path select message is received
                            "from": "client",
                            "type": "pathSelect",
                            "payload": {
                                "startX": 0,
                                "startY": 0,
                                "startDirection": 0
                            }
                        }
        self.path = { #declaration for path message and to cache if path message is received
                        "from": "client",
                        "type": "path",
                        "payload": {
                            "startX": 0,
                            "startY": 0,
                            "startDirection": 0,
                            "endX": None,
                            "endY": None,
                            "endDirection": None,
                            "pathStatus": "free",
                            "pathWeight": None
                        }
                    }
        self.target = { #declaration for target message and to cache if target message is received
                        "from": "server",
                        "type": "target",
                        "payload": {
                            "targetX": None,
                            "targetY": None
                        }
                    } 
        self.planetName = "" #variable to save planet name and to dynamically change planet subscription
        self.pathUnveiled = { #declaration for path unveiled messages
                                "from": "server",
                                "type": "pathUnveiled",
                                "payload": {
                                    "startX": None,
                                    "startY": None,
                                    "startDirection": None,
                                    "endX": None,
                                    "endY": None,
                                    "endDirection": None,
                                    "pathStatus": "free",
                                    "pathWeight": None
                                }
                            }
        
        #start receiving messages
        self.client.loop_start()
        
        

    def on_connect(self, client, userdata, flags, rc): # method to ensure that the connection process was succesfull
        if rc == 0:
            print("Connection established")
        else:
            print("connection lost") 
        

    # DO NOT EDIT THE METHOD SIGNATURE
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

        # YOUR CODE FOLLOWS (remove pass, please!)

        if payload["type"] == "pathSelect": #directions received from mothership
            self.pathSelect["payload"]["startDirection"] = payload["payload"]["startDirection"]
            self.pathSelectFinished = True
            print("New Direction from mothership")

        elif payload["type"] == "planet": #initial planet data provided by mothership
            self.planetName = payload["payload"]["planetName"]
            self.path["payload"]["startX"] = payload["payload"]["startX"]
            self.path["payload"]["startY"] = payload["payload"]["startY"]
            self.path["payload"]["startDirection"] = payload["payload"]["startOrientation"]
            self.path["payload"]["endDirection"] = payload["payload"]["startOrientation"]
            self.path["payload"]["endX"] = payload["payload"]["startX"]
            self.path["payload"]["endY"] = payload["payload"]["startY"]
            
            print("Your Planet: \n" + json.dumps(self.path, indent = 4, sort_keys= True))

        elif payload["type"] == "path": #shows confirmation by mothership and changes possible corrections for end-coordinates. Adds pathWeight  
            self.path["payload"]["startX"] = payload["payload"]["startX"]
            self.path["payload"]["startY"] = payload["payload"]["startY"]
            self.path["payload"]["startDirection"] = payload["payload"]["startDirection"]
            self.path["payload"]["endX"] = payload["payload"]["endX"]
            self.path["payload"]["endY"] = payload["payload"]["endY"]
            self.path["payload"]["pathWeight"] = payload["payload"]["pathWeight"]
            self.path["payload"]["endDirection"] = payload["payload"]["endDirection"]
 
            print("Recieved path message from mothership")

        elif payload["type"] == "done": #final message that ends while loop in main.py 
            self.explorationDone = True
            
            print("You're done. \n" + json.dumps(payload, indent = 4, sort_keys= True))

        elif payload["type"] == "target": #target-message from mothership
            self.target = payload  
            self.targetFinished = True
            
            print("Got a new target: " + str(self.target["payload"]["targetX"]) + "|" + str(self.target["payload"]["targetY"]))

        # elif payload["from"] == "debug" and payload["type"] == "syntax": #displays if either the synatx is correct or incorrect
        #     print(json.dumps(payload, indent = 4, sort_keys= True))

        # elif payload["type"] == "notice": #confirms active planet while testing BITTE ENTFERNEN VOR DER PRÜFUNG
        #     print(json.dumps(payload, indent = 4, sort_keys= True))

        elif payload["type"] == "pathUnveiled": 
            startX = payload["payload"]["startX"]
            startY = payload["payload"]["startY"]
            stdirection = payload["payload"]["startDirection"]
            endX = payload["payload"]["endX"]
            endY = payload["payload"]["endY"]
            enddirection = payload["payload"]["endDirection"]
            weight = payload["payload"]["pathWeight"]
            self.planet.add_path(((startX,startY), stdirection), ((endX, endY), enddirection), weight)
            self.pathUnveiledFinished = True
            
            print("A path has been unveiled")

         
        


        

    # DO NOT EDIT THE METHOD SIGNATURE
    #
    # In order to keep the logging working you must provide a topic string and
    # an already encoded JSON-Object as message.
    def send_message(self, topic, message):
        """
        Sends given message to specified channel
        :param topic: String
        :param message: Object
        :return: void
        """
        self.logger.debug('Send to: ' + topic)
        self.logger.debug(json.dumps(message, indent=2))

        # YOUR CODE FOLLOWS (remove pass, please!)
        self.client.publish(topic, payload = json.dumps(message), qos = 2)
        

    def readyMessage (self): #method to send ready messages
        message = {
                    "from": "client",
                    "type": "ready"
        }
        self.send_message('explorer/037', message)

    def pathMessage (self, eX, eY, eDirection, pStatus ): #method to send path messages
        message = {
                    "from": "client",
                    "type": "path",
                    "payload": {
                        "startX": self.path["payload"]["endX"],
                        "startY": self.path["payload"]["endY"],
                        "startDirection": self.pathSelect["payload"]["startDirection"],
                        "endX": eX,
                        "endY": eY,
                        "endDirection": eDirection,
                        "pathStatus": pStatus,
                        "pathWeight": None
                    }
        }
        self.topic = "planet/" + self.planetName + "/037"
        self.client.subscribe(self.topic)
        self.send_message(self.topic, message)
        self.path = message

    def pathSelectMessage (self, stDirect): #method to send path select messages
        message = {
            "from": "client",
            "type": "pathSelect",
            "payload": {
                "startX": self.path["payload"]["endX"],
                "startY": self.path["payload"]["endY"],
                "startDirection": stDirect
            }
        }
        self.topic = "planet/" + self.planetName + "/037"
        self.client.subscribe(self.topic)
        self.send_message(self.topic, message)
        self.pathSelect = message 
    
    def explorationCompletedMessage(self): #method to send exploration complete message
        message = {
                    "from": "client",
                    "type": "explorationCompleted",
                    "payload": {
                        "message": "The entire Planet has been discovered"
                    }
                }
        self.topic = 'explorer/037'
        self.client.subscribe(self.topic)
        self.send_message(self.topic, message)
    
    def targetReachedMessage(self): #method to send target reached message
        message = {
                    "from": "client",
                    "type": "targetReached",
                    "payload": {
                        "message": "Target reached"
                    }
                }
        self.topic = 'explorer/037'
        self.client.subscribe(self.topic)
        self.send_message(self.topic, message)
    
    """VOR DER PRÜFUNG RAUSNEHMEN SONST KOMMT ES ZU FEHLERN!!!!!"""
    # def testplanetMessage(self):
    #     message = {
    #                 "from": "client",
    #                 "type": "testplanet",
    #                 "payload": {
    #                     "planetName":"Fassaden-M4" #hier einfach string einf.
    #                 }
    #             }
    #     self.topic = 'explorer/037'
    #     self.client.subscribe(self.topic)
    #     self.send_message(self.topic, message)
        

        
    

    # DO NOT EDIT THE METHOD SIGNATURE OR BODY
    #
    # This helper method encapsulated the original "on_message" method and handles
    # exceptions thrown by threads spawned by "paho-mqtt"
    def safe_on_message_handler(self, client, data, message):
        """
        Handle exceptions thrown by the paho library
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        try:
            self.on_message(client, data, message)
        except:
            import traceback
            traceback.print_exc()
            raise

