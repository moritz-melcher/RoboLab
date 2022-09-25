#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
from enum import IntEnum, unique
from typing import List, Tuple, Dict, Union


@unique
class Direction(IntEnum):
    """ Directions in shortcut """
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270


Weight = int
"""
Weight of a given path (received from the server)

Value:  -1 if blocked path
        >0 for all other paths
        never 0
"""


class Planet:
    """
    Contains the representation of the map and provides certain functions to manipulate or extend
    it according to the specifications
    """

    def __init__(self):
        """ Initializes the data structure """
        self.paths = {}
        self.points = []
        self.checked_points = []

    def add_path(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
                 weight: int):
        """
         Adds a bidirectional path defined between the start and end coordinates to the map and assigns the weight to it

        """    
        # print("------------------------")
        # print("Adding path between " + str(start) + " and "  + str(target))
        # print("The path weight is -- " + str(weight))
        # print("------------------------")
        #input gets put into variables
        startPoint = start[0]
        startDir = start[1]
        targetPoint = target[0]
        targetDir = target[1]

        #if target or start point not in points, gets added to points        
        if self.points.count(startPoint) == 0 and startPoint != (None, None):
            self.points.append(startPoint)
            self.paths.update({startPoint: {}})        
        if self.points.count(targetPoint) == 0 and targetPoint != (None, None):
            self.points.append(targetPoint)
            self.paths.update({targetPoint: {}}) 

        #New Path gets added and if a point has 4 adjacend paths it is automatically checked
        if startPoint != (None, None):
            self.paths[startPoint].update({startDir: (targetPoint, targetDir, weight)})
            if len(self.paths[startPoint]) == 4 and startPoint not in self.checked_points: self.checked_points.append(startPoint)
        if targetPoint != (None,None):
            self.paths[targetPoint].update({targetDir: (startPoint, startDir, weight)})
            if len(self.paths[targetPoint]) == 4 and targetPoint not in self.checked_points: self.checked_points.append(targetPoint)

        # print("Current Paths are now: ")
        # for x in self.paths:
        #     print(str(x) + ": " + str(self.paths[x]))
        return

    #returns the direction of the shortest path between two neighboring points
    def get_direction(self, start: Tuple[int,int], target: Tuple[int,int]):
        if start not in self.points or target not in self.points: return
        neighbors = self.get_neighbors(start)
        if target not in neighbors or start == target: return
        paths = self.paths[start]
        found_paths = []
        for path in paths:
            if paths[path][0] == target and paths[path][2] != -1:
                found_paths.append(path)
        min_path_dir = found_paths[0]
        for path_dir in found_paths:
            if paths[path_dir][2] < paths[min_path_dir][2]:
                min_path_dir = path_dir 
        return min_path_dir

    #returns the distance/path weight between two neighboring points
    def get_distance(self, start: Tuple[int,int], target: Tuple[int,int]):
        neighbors = self.get_neighbors(start)
        if target not in neighbors or start == target: return
        paths = self.paths[start]
        found_weights = []
        for path in paths:
            if paths[path][0] == target:
                found_weights.append(paths[path][2])
        return min(found_weights)

    #returns a list of neighbors of the given point
    def get_neighbors(self, node: Tuple[int,int]):
        if node not in self.points: return []
        neighbors = []
        paths = self.paths[node]
        for path in paths:
            if paths[path][2] != -1 and paths[path][2] is not None and paths[path][0] != node and paths[path][0] not in neighbors:
                neighbors.append(paths[path][0])
        return neighbors

    #returns all paths
    def get_paths(self) -> Dict[Tuple[int, int], Dict[Direction, Tuple[Tuple[int, int], Direction, Weight]]]:
       
        return self.paths

    #calculates the dijkstra table of the given point 
    def dijkstra(self, start: Tuple[int, int]) -> Dict:
        print("Starting Dijkstra")
        #new array with all points and empty dijkstra dictionary
        unchecked_points = [x for x in self.points]
        dijk = {}
        #all points exept start get infinite distance, start gets 0
        for x in self.points:
            if x == start:
                dijk.update({x: (0,)})
            else:
                dijk.update({x: (float('inf'),)})
        curr_point = start 
        stack = [start]
        #"real" dijkstra starts
        while unchecked_points != []:
            if curr_point in unchecked_points: unchecked_points.remove(curr_point)
            # print("----------------------------")  
            # print("Current Point: " + str(curr_point))
            # print("Unchecked Points: " + str(unchecked_points))
            # print("Stack: " + str(stack))

            #checks for neighbors that haven't been checked yet and aren't connected by a blocked path
            neighbors = [x for x in self.get_neighbors(curr_point) if x in unchecked_points]

            
            for x in dijk.items():
                if x[0] in neighbors:
                    for y in self.paths[curr_point]: #loop through Dictionary with paths
                        val = self.paths[curr_point][y]
                        if x[0] == val[0]: #gets path with the same key as the one in neighbors
                            sucdir = y
                            weight = val[2]
                    sucdis = dijk.get(curr_point)[0]
                    new_weight = weight + sucdis
                    if new_weight < x[1][0]: 
                        dijk[x[0]] = (new_weight, curr_point, sucdir)
                        
            if not unchecked_points: break
            curr_point = unchecked_points[0]
            dijk2 = dijk.copy()
            checked_points = [x for x in self.points if x not in unchecked_points]
            for x in checked_points:
                dijk2.pop(x)
            for x in dijk2.items():        
                if x[1][0] < dijk2.get(curr_point)[0]: curr_point = x[0]
            
        return dijk

    def shortest_path(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[None, List[Tuple[Tuple[int, int], Direction]]]:
        start_weights = []
        target_weights = []
        # print("Calculating shortest path between " + str(start) + " and " + str(target))
        #return None if:
        #one of the two points isn't discovered yet
        #one of the two points only has blocked paths attached
        #the two points are the same 
        if start not in self.points or target not in self.points or start == target : return
        else:
            for path in self.paths[start]: 
                if self.paths[start][path][2] is not None: start_weights.append(self.paths[start][path][2])
            for path in self.paths[target]: 
                if self.paths[target][path][2] is not None: target_weights.append(self.paths[target][path][2])
            if max(start_weights) == -1 or max(target_weights) == -1: return
            
        #gets the dijkstra table of the start point
        dijk = self.dijkstra(start)
        path = []
        current = target

        #if the target is not reachable, return
        if dijk.get(target) == (float('inf'),): return

        #puts together the path to the target and returns it
        while True:
            table = dijk.get(current)
            path.insert(0, (table[1], table[2]))
            if table[1] == start: 
                print("Shortest path between " + str(start) + " and " + str(target) + " is:")
                print(path)
                return path
            else: current = table[1]
            
