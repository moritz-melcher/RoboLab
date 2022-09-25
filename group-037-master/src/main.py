#!/usr/bin/env python3

import ev3dev.ev3           as ev3
import logging
import os
import paho.mqtt.client     as mqtt
import uuid
import signal
import time
from typing         import List, Tuple, Dict, Union
from communication  import Communication
from planet         import Direction, Planet
from odometry       import Odometry

client = None  # DO NOT EDIT
#global planet, com, odo, curr_point
    
#function to get a little buffer while waiting for a server response    
def radio_silence(): 
    if com.pathSelectFinished == True: 
        #print("A new direction has been provided by mothership" + str(com.pathSelect["payload"]["startDirection"]))
        com.pathSelectFinished = False


#checks if there are any targets that needs to be reached and returns the direction in which the robot needs to go or None if there is no target
def check_for_targets(): 
    dir = None
    print("Checking for target...")
    if com.target["payload"]["targetX"] != None and com.target["payload"]["targetX"] != None: 
       dir = reach_target((com.target["payload"]["targetX"], com.target["payload"]["targetY"]))
    return dir
    
#adds the last traversed path in planet.paths with the add_path method from planet.py
def add_current_path(): 
    startX = com.path["payload"]["startX"]
    startY = com.path["payload"]["startY"]
    startDirection = com.path["payload"]["startDirection"]
    endX = com.path["payload"]["endX"]
    endY = com.path["payload"]["endY"]
    endDirection = com.path["payload"]["endDirection"]
    weight = com.path["payload"]["pathWeight"]
    start = ((startX, startY), startDirection)
    end = ((endX, endY), endDirection)
    planet.add_path(start, end, weight)

#adds an unexplored path to the given point in the given direction, if there isn't already a path in which case it does nothing
def add_unexplored_path(point: Tuple[int,int], dir: Direction): 
    paths = planet.paths.get(point)
    print("trying to add unexplored paths to " + str(point) + " in dir: " + str(dir))
    if paths is not None and paths.get(dir) is None:
        planet.add_path((point, dir),((None, None), None), None)
        print("Adding unexplored path to " + str(point) + " in " + str(dir) + " Direction")
    else: print("Already have a path in that direction")

#calculates the direction the robots needs to go to get to the target, returns a direction or None if the target isn't reachable
def reach_target(target: Tuple[int, int]): 
    if target not in planet.points: return
    path = planet.shortest_path(current_point[0], target)
    if path is None: return
    dir = path[0][1]
    return dir

#returns a list of directions, which are the currently unexplored paths of the given point
def unexplored_paths(point: Tuple[int, int]): 
    paths = planet.paths[point]
    dirs = []
    for x in paths:
        if paths[x][2] is None: dirs.append(x)
    return dirs

#returns the point next to the given point that has shortest distance
def neighbor_with_shortest_dis(start: Tuple[int,int], nodes):
    if not nodes: nodes = planet.get_neighbors(start)
    if not nodes: return
    min_node = nodes[0]
    min_node_dis = {min_node: planet.get_distance(start,nodes[0])}
    for node in nodes:
        dis = planet.get_distance(start,node)
        if dis < min_node_dis[min_node]:
            min_node = node
            min_node_dis = {min_node: dis}
    return min_node

#returns neighbor of the given point with the highest amount of unexplored paths
def neighbor_with_max_unexplored_paths(start: Tuple[int,int]): 
    neighbors = planet.get_neighbors(start)
    if not neighbors: return
    nodes = {}
    i = 0
    for neighbor in neighbors:
        paths = planet.paths[neighbor]
        for path in paths:
            if paths[path][2] is None:
                i+=1
        nodes.update({neighbor: i})
    max_node = [nodes[0]]
    for node in nodes:
        if nodes[node] > nodes[max_node[0]]:
            max_node = [node]
        elif nodes[node] == nodes[max_node[0]]:
            max_node.append(node)
    if nodes[max_node[0]] != 0: return max_node
    else: return

#calculates the sum of number of unexplored paths, of points that we scanned
def number_unexplored_paths(): 
    i = 0
    for node in planet.points:
        num_paths = len(unexplored_paths(node))
        i = i + num_paths
    return i

#our method of exploring
def explore(): 
    print("Now exploring")
    unex_paths = unexplored_paths(current_point[0])
    #if the current point has no unexplored paths, it calculates the direction of the nearest point with unexplored paths
    if unex_paths == []:
        near = nearest_node_with_unexplored_paths(current_point[0])
        if near is None: return
        dir = near[0][1]
    #if the current point has unexplored paths it picks the first one in the array
    else:
        dir = unex_paths[0]
    return dir

#returns path from given point to nearest point with unexplored paths
def nearest_node_with_unexplored_paths(start: Tuple[int,int]): 
        nodes = {}
        nodes_unex = {}
        #gets all points with unexplored paths
        for node in planet.points:
            i = 0
            paths = planet.paths[node]
            for path in paths:
                if paths[path][2] is None:
                    i+=1
            nodes.update({node: i})
        #gets dijkstra table for given point
        dijk = planet.dijkstra(start)
        #makes a dijkstra table just for points with unexplored paths
        for node in dijk:
            if nodes[node] != 0:
                nodes_unex.update({node: dijk[node][0]})
        #gets any node as starting node
        for node in nodes_unex: 
            node_min = node
            break
        #compares all nodes in the "second" dijkstra table to get the one with min. distance
        for node in nodes_unex:
            if dijk[node] < dijk[node_min]:
                node_min = node
        #gets the way to that node with the shortest_path method
        return planet.shortest_path(start, node_min)

#scans all paths on the point and adds an unexplored path depending on found routes
def scan_add_paths(point: Tuple[int,int]): 
    odo.scanRoutes()
    print("Scanned Routes for: " + str(point))
    if odo.routeFront == True:
        print("Adding front path")
        add_unexplored_path(point, current_point[1])
    if odo.routeLeft == True:
        print("Adding left path")
        add_unexplored_path(point, (current_point[1] - 90) % 360) 
    if odo.routeRight == True:
        print("Adding right path")
        add_unexplored_path(point, (current_point[1] + 90) % 360) 

#returns the direction which to go to next and checks if we are done
def where_to_go():
    #if the current point hasn't been scanned, it gets scanned
    if current_point[0] not in planet.checked_points:
        scan_add_paths(current_point[0])
        planet.checked_points.append(current_point[0])
    else:
        global forward 
        forward = True
    
    #if all paths from the current point are blocked, the exploration is done
    current_weights = []
    for path in planet.paths[current_point[0]]: 
        if planet.paths[current_point[0]][path][2] is not None: current_weights.append(planet.paths[current_point[0]][path][2])
    if max(current_weights) == -1 and unexplored_paths(current_point[0]) == []:
        com.explorationCompletedMessage()
        time.sleep(3)
        return

    #creates a list of unexplored points, which is the difference between all points that we know of and points that we checked
    unexplored_points = [node for node in planet.points if node not in planet.checked_points]

    #if we are on the target we send a targetReached message
    if current_point[0] == (com.target["payload"]["targetX"], com.target["payload"]["targetY"]):
        com.targetReachedMessage()
        time.sleep(3)
        return

    #checks for a target and if a direction gets back it gets returned
    dir = check_for_targets()
    if dir is not None: return dir

    #checks if have no more unexplored paths, that we know of
    if number_unexplored_paths() == 0:
        #if we have no unexplored points we have completed the exploration and send an according message
        if not unexplored_points:
            com.explorationCompletedMessage()
            time.sleep(3)
            return
        #if we have unexplored points, we find the nearest and set the direction on the way, the shortest path returns
        else:
            dijk = planet.dijkstra(current_point[0])
            dijk2 = {}
            for x in dijk:
                if x in unexplored_points:
                    dijk2.update({x: dijk[x][0]})
            next_node = unexplored_points[0]
            for x in dijk2:
                if dijk2[x] < dijk2[next_node]:
                    next_node = x
            path = planet.shortest_path(current_point[0], next_node)
            dir = path[0][1]
            return dir
        
    #if we have no target, are not done and still have unexplored paths, we explored    
    dir = explore()
    if dir is None:
        dijk = planet.dijkstra(current_point[0])
        dijk2 = {}
        for x in dijk:
            if x in unexplored_points:
                dijk2.update({x: dijk[x][0]})
        next_node = unexplored_points[0]
        for x in dijk2:
            if dijk2[x] < dijk2[next_node]:
                next_node = x
        path = planet.shortest_path(current_point[0], next_node)
        dir = path[0][1]
        return dir
    return dir





def run():
    # DO NOT CHANGE THESE VARIABLES
    #
    # The deploy-script uses the variable "client" to stop the mqtt-client after your program stops or crashes.
    # Your script isn't able to close the client after crashing.
    global client

    #very important print statements
    print('Connecting to SKYNET...')
    time.sleep(0.3)
    print('Connection to SKYNET established...')
    time.sleep(0.3)
    print('Loading T-800 module...')
    time.sleep(0.3)
    print('Initializing order: ...')
    time.sleep(0.3)
    print('Eliminate all humans!')

    client_id = 'YOURGROUPID-' + str(uuid.uuid4())  # Replace YOURGROUPID with your group ID
    client = mqtt.Client(client_id=client_id,  # Unique Client-ID to recognize our program
                         clean_session=True,  # We want a clean session after disconnect or abort/crash
                         protocol=mqtt.MQTTv311  # Define MQTT protocol version
                         )
    log_file = os.path.realpath(__file__) + '/../../logs/project.log'
    logging.basicConfig(filename=log_file,  # Define log file
                        level=logging.DEBUG,  # Define default mode
                        format='%(asctime)s: %(message)s'  # Define default logging format
                        )
    logger = logging.getLogger('RoboLab')

    # THE EXECUTION OF ALL CODE SHALL BE STARTED FROM WITHIN THIS FUNCTION.
    # ADD YOUR OWN IMPLEMENTATION HEREAFTER.
    
    #importing color information
    with open('colorValues.txt', 'r') as f: 
    
        values = f.readlines()

        r1 = int(values[0])
        r2 = int(values[1])
        r3 = int(values[2])

        b1 = int(values[3])
        b2 = int(values[4])
        b3 = int(values[5])

        w1 = int(values[6])
        w2 = int(values[7])
        w3 = int(values[8])

        s1 = int(values[9])
        s2 = int(values[10])
        s3 = int(values[11])

    #Declarations
    global planet, com, odo, current_point, forward
    forward = False
    odo = Odometry(r1, r2, r3, b1, b2, b3, w1, w2, w3, s1, s2, s3) #odometry object
    planet = Planet() #planet object
    com = Communication(client, logger, planet) #communication object
    current_point =((int, int), Direction) #current position
    radioSilence = False

    #com.testplanetMessage()

    #drive to first node
    odo.drive() 
    com.readyMessage()
    time.sleep(3)
    x = com.path["payload"]["startX"]
    y= com.path["payload"]["startY"]
    print("Start X: " + str(x) + " Y: " + str(y))

    #set current_point to first node
    current_point = ((x, y), com.path["payload"]["startDirection"])

    #configure the odometry variables
    odo.deltaX = x
    odo.deltaY = y
    odo.gammaOut = current_point[1] #current direction

    #add the first path as blocked, so we don't want to drive on it later
    planet.add_path(((None , None), None),((com.path["payload"]["startX"], com.path["payload"]["startY"]), (com.path["payload"]["endDirection"] - 180) % 360), -1)
    time.sleep(2)  
    
    #loop for every node till we are done
    while not com.explorationDone:
        #print("----------------------------")
        #print("Odo X: " + str(odo.deltaX) + " Odo Y: " + str(odo.deltaY))
        print("Now selecting path from: " + str(current_point[0]))

        #get the direction where to drive to
        dir = where_to_go() 
        if dir is None: break

        #sends selected path to mothership
        com.pathSelectMessage(dir) 
        time.sleep(3)

        #signals the end of our communication phase
        ev3.Sound.beep() 
        time.sleep(2)

        #sets the driving direction from the pathSelect, our direction if no response from mothership, motherships direction if we got response
        dir_abs = com.pathSelect["payload"]["startDirection"] 
        #dir_abs = current_point[1]
        print("Current paths are:")
        for i in planet.paths:
            print(str(i) + ": " + str(planet.paths[i]))
        print("Absolute Direction" + str(dir_abs))
        #print("Facing at the end of last path: " + str(current_point[1]))

        #calculates a relative direction from the direction we are facing and the direction we want to drive to
        dir_rel = (current_point[1] - dir_abs) % 360
       
        #converts the result to number, 1 for left, 2 for forward, 3 for right and 4 for back
        if dir_rel == 90: dir_rel = 1
        elif dir_rel == 0: dir_rel = 2
        elif dir_rel == 270: dir_rel = 3
        else: dir_rel = 4  
        #print("Relative direction: " + str(dir_rel))

        #if we didn't scan we have to drive of the point we're on
        if forward == True: 
            print("Going forward")
            forward = False
            odo.forward()
        
        #we start driving in the previous selected direction
        odo.backOnTrack(dir_rel)
        #print("OUT OF BACKONTRACK")
        time.sleep(1)

        #when we get on a field we send a path message, we differentiate between blocked and free paths
        if odo.redField or odo.blueField: 
            print("Got on Field")
            if odo.blocked:
                com.pathMessage(com.path["payload"]["endX"], com.path["payload"]["endY"], (com.path["payload"]["startDirection"] - 180) % 360,"blocked")
            else:
                com.pathMessage(odo.deltaX, odo.deltaY, (odo.gammaOut - 180) % 360,"free")
            time.sleep(3)

        #adds the current path, which was likely changed by the mothership    
        add_current_path()
        
        #resetting the path status
        com.path["payload"]["pathStatus"] = "free" 
        time.sleep(2)

        #setting the currentpoint to the values of the pathMessage from the mothership
        current_point = ((com.path["payload"]["endX"], com.path["payload"]["endY"]), (com.path["payload"]["endDirection"] - 180) % 360) #updates our current point to new coordinates
        print("\n")
        print("CURRENT POINT: " + str(current_point))

        #setting the odometry values to the values provided by the mothership
        odo.deltaX = current_point[0][0]
        odo.deltaY = current_point[0][1]
        odo.gammaOut = current_point[1]
        
    print("We're done. Yayy")
    ev3.Sound.speak('Mom pick me up, I am scared') #signal tone to know that we finished our exploration or the target was reached
    time.sleep(2)
               
# DO NOT EDIT
def signal_handler(sig=None, frame=None, raise_interrupt=True):
    if client and client.is_connected():
        client.disconnect()
    if raise_interrupt:
        raise KeyboardInterrupt()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    try:
        run()
        signal_handler(raise_interrupt=False)
    except Exception as e:
        signal_handler(raise_interrupt=False)
        raise e
