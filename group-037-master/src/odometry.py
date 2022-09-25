# !/usr/bin/env python3

#this script contains movement and odometry functions

import ev3dev.ev3 as ev3
import time
import math

class Odometry:
    def __init__(self, r1, r2, r3, b1, b2, b3, w1, w2, w3, s1, s2, s3):

        self.motorL = ev3.LargeMotor('outD')                        #initializing left motor
        self.motorR = ev3.LargeMotor('outA')                        #initializing right motor
        self.cs     = ev3.ColorSensor()                             #initializing color sensor
        self.us     = ev3.UltrasonicSensor()                        #initializing ultrasonic sensor
        self.gs     = ev3.GyroSensor()                              #initializing gyroscope

        self.r1     = r1                                            #initializing color information
        self.r2     = r2
        self.r3     = r3
        self.b1     = b1
        self.b2     = b2
        self.b3     = b3
        self.w1     = w1
        self.w2     = w2
        self.w3     = w3
        self.s1     = s1
        self.s2     = s2
        self.s3     = s3

        self.v      = 100                                           #initializing PID controll variables
        self.kp     = 0.45
        self.ki     = 0
        self.kd     = 0.5

        #blue field boundries
        self.bb11 = int(self.b1*0.7)
        self.bb12 = int(self.b1*1.3)

        self.bb21 = int(self.b2*0.7)
        self.bb22 = int(self.b2*1.3)

        self.bb31 = int(self.b3*0.7)
        self.bb32 = int(self.b3*1.3)

        #red field boundries
        self.rb11 = int(self.r1*0.7)
        self.rb12 = int(self.r1*1.3)

        self.rb21 = int(self.r2*0.7)
        self.rb22 = int(self.r2*1.3)

        self.rb31 = int(self.r3*0.7)
        self.rb32 = int(self.r3*1.3)

        self.blueField = False                                      #field booleans
        self.redField  = False

        self.routeLeft  = False                                     #outgoing paths
        self.routeFront = False
        self.routeRight = False
        self.deadEnd    = False

        self.blocked    = False                                     #indicator for blocked path

        self.leftDirect = 0                                         #absolute orientation of left and right paths
        self.rightDirect= 0                                         #front path has same absolute orientation as robot

        #initializing color sensor mode
        self.cs.mode = 'RGB-RAW'

        #initializing ultrasonic sensor mode
        self.us.mode = 'US-DIST-CM'

        self.motorRevList = []                                      #list that contains motor revolution data for position determination

        self.deltaX         = 0                                     #current coordinates
        self.deltaY         = 0
        self.gammaCalc      = 0                                     #current angle in rad
        self.gammaOut       = 0                                     #current orientation in degrees


    #following the line (final)
    def drive(self):

        #print('Now driving...')                                    #[4debugging]

        integral    =   0                                           #variables for motor controll
        lastError   =   0
        derivative  =   0

        self.blocked    = False                                     #reseting booleans
        self.deadEnd    = False
        self.blueField  = False
        self.redField   = False

        self.motorRevList = []                                      #reseting list of motor revolutions

        l = 0                                                       #variables for left-/ right turn power
        r = 0

        cycles = 0                                                  #counter for saving motor revolutions

        offset = (self.w1 + self.w2 + self.w3 + self.s1 + self.s2 + self.s3)/6 #offset = average of b & w

        self.motorL.reset()
        self.motorR.reset()

        #pid-controller
        while True:

            self.redField  = False                                  #reseting field booleans
            self.blueField = False
        
            rgb = self.cs.bin_data('hhh')                           #getting color sensor data
            lv = sum(rgb)/3                                         #averageing color sensor data
            collision = self.us.value()                             #getting proximity data

            #pid-controller
            error = lv - offset
            integral = integral + error
            derivative = error - lastError
            turn = self.kp*error + self.ki*integral + self.kd*derivative
            l = int(self.v+turn)
            r = int(self.v-turn)
            if (l > 500) and not (l < 0):
                l = 500
            if (l < -500) and not (l > 0):
                l = -500
            if (r > 500) and not (l < 0):
                r = 500
            if (r < -500) and not (r >0):
                r = -500
            #print(l,' ',r)                                         #[4debugging]
            self.motorL.run_forever(speed_sp=l)
            self.motorR.run_forever(speed_sp=r)
            lastError = error

            cycles += 1                                             #loop cycle count increment

            #saving motor revolution data every 100 controll cycles
            if cycles == 100:
                self.motorRevList.append((self.motorL.position, self.motorR.position))
                self.motorL.reset()
                self.motorR.reset()
                cycles = 0

            #check for red field
            if (self.rb11 < rgb[0] < self.rb12) and (self.rb21 < rgb[1] < self.rb22) and (self.rb31 < rgb[2] < self.rb32):
                self.motorL.stop()
                self.motorR.stop()
                self.redField = True
                self.motorRevList.append((self.motorL.position, self.motorR.position))
                self.position()
                #print('red field detected')                        #[4debugging]
                break

            #check for blue field
            if (self.bb11 < rgb[0] < self.bb12) and (self.bb21 < rgb[1] < self.bb22) and (self.bb31 < rgb[2] < self.bb32):
                self.motorL.stop()
                self.motorR.stop()
                self.blueField = True
                self.motorRevList.append((self.motorL.position, self.motorR.position))
                self.position()
                #print('blue field detected')
                #time.sleep(5)                                      #[4debugging]
                break

            #check for collision detection
            if collision < 150:
                self.motorL.stop()
                self.motorR.stop()
                self.blocked = True
                self.motorRevList.append((self.motorL.position, self.motorR.position))
                time.sleep(0.1)
                time.sleep(1)
                ev3.Sound.speak('collision ahead')
                time.sleep(1)
                self.position()
                self.turnAround()
                break

    #turns around if way is blocked (final)
    def turnAround(self):

        #print('Turning around...')                                 #[4debugging]

        self.motorL.reset()
        self.motorR.reset()

        #backing off a little from object ahead
        self.motorL.run_timed(time_sp=1000, speed_sp=-20)
        self.motorR.run_timed(time_sp=1000, speed_sp=-50)
        time.sleep(1.1)
        self.motorL.run_timed(time_sp=1000, speed_sp=50)
        self.motorR.run_timed(time_sp=1000, speed_sp=-50)
        time.sleep(1.1)
        self.motorL.stop()
        self.motorR.stop()

        #turning as long as we are on the line again
        while True:

            rgb = self.cs.bin_data('hhh')
            self.motorL.run_forever(speed_sp=100)
            self.motorR.run_forever(speed_sp=-100)

            if rgb[0] < 45 and rgb[1] < 75 and rgb[2] < 30:
                self.motorL.stop()
                self.motorR.stop()
                break

        time.sleep(0.1)
        self.motorR.stop()
        self.motorL.stop()
        self.motorR.reset()
        self.motorL.reset()

        #continue driving
        self.drive()

    #scans routes (version for new robot configuration) (final)
    def scanRoutes(self):
        self.routeFront = False
        self.routeRight = False
        self.routeLeft = False

        print('Scanning routes...')                                #[4debugging]

        ev3.Sound.beep()

        self.gs.mode = 'GYRO-CAL'                                   #calibrating gyro
        time.sleep(0.1)
        self.gs.mode = 'GYRO-CAL'
        time.sleep(0.1)
        self.gs.mode = 'GYRO-ANG'

        time.sleep(0.1)
        
        if self.blueField:
            #print('Getting off of blue field...')                  #[4debugging]
            while True:
                rgb = self.cs.bin_data('hhh')
                self.motorL.run_forever(speed_sp=50)
                self.motorR.run_forever(speed_sp=60)

                if rgb[0] > self.bb12 and rgb[1] > self.bb22 and rgb[2] > self.bb32:
                    self.motorL.stop()
                    self.motorR.stop()
                    time.sleep(0.1)
                    break   

        if self.redField:
            #print('Getting off of red field...')                   #[4debugging]
            while True:
                rgb = self.cs.bin_data('hhh')
                self.motorL.run_forever(speed_sp=50)
                self.motorR.run_forever(speed_sp=60)

                if rgb[0] > self.rb11 and rgb[1] > self.rb21 and rgb[2] > self.rb31:
                    self.motorL.stop()
                    self.motorR.stop()
                    self.motorL.run_timed(time_sp=1500, speed_sp=60)
                    self.motorR.run_timed(time_sp=1500, speed_sp=70)
                    time.sleep(2)
                    break   

        #print('Down from field, now moving forward...')            #[4debugging]
        time.sleep(0.1)

        self.motorL.run_timed(time_sp=1000, speed_sp=60)
        self.motorR.run_timed(time_sp=1000, speed_sp=70)

        time.sleep(1.1)
        
        self.motorL.reset()
        self.motorR.reset()
        time.sleep(0.1)
        self.motorL.reset()
        self.motorR.reset()
        time.sleep(0.1)
        self.cs.mode='COL-REFLECT'
        time.sleep(0.1)
        self.cs.mode='RGB-RAW'
        #print('vor der schleife=', self.motorL.position)       [4debugging]
        
        #scanning with gyro
        while True:

            rgb = self.cs.bin_data('hhh')
            rotation = self.gs.value()

            #print('rotation =', rotation)                      [4debugging]
            #print('ticks left =', ticksL)
            #check for front route
            if (rgb[0] < 55 and rgb[1] < 85 and rgb[2] < 40) and (rotation < 45):
                self.routeFront = True
                #print('route front found!')                    #[4debugging]

            #check for right route
            if (rgb[0] < 55 and rgb[1] < 85 and rgb[2] < 40) and (45 < rotation < 135):
                self.routeRight = True
                #print('route right found!')                    #[4debugging]

            #check for left route
            if (rgb[0] < 55 and rgb[1] < 85 and rgb[2] < 40) and (225 < rotation < 315):
                self.routeLeft = True
                #print('route left found!')                     #[4debugging]

            if (350 < rotation < 370):
                break

            #print('in der schleife=', ticksL)                  [4debugging]
            #if (rgb[0] < 55 and rgb[1] < 85 and rgb[2] < 40):
            #    print("black")

            self.motorL.run_forever(speed_sp=120)
            self.motorR.run_forever(speed_sp=-120)


        if self.routeLeft == False and self.routeFront == False and self.routeRight == False:
            self.deadEnd = True

        if self.routeLeft:
            self.leftDirect = (self.gammaOut - 90) % 360

        if self.routeRight:
            self.rightDirect = (self.gammaOut + 90) % 360

        self.motorL.stop()
        self.motorR.stop()

        #print('routeLeft=', self.routeLeft, 'routeFront=', self.routeFront, 'routeRight=', self.routeRight, 'deadEnd=', self.deadEnd)  #[4debugging]


    #calculates current X and Y position and orientation according to motor position (final)
    def position(self):

        #print('Calculating position...')                           #[4debugging]

        a = 12.25                                                   #wheelbase
        dX = 0
        dY = 0
        self.gammaCalc = math.radians(self.gammaOut)

        for index, tuple in enumerate(self.motorRevList):           #iterating trough motor data

            ticksMotorL = tuple[0]
            ticksMotorR = tuple[1]

            distMotorL = (ticksMotorL/360)*17.3                     #distance motors traveled in cm
            distMotorR = (ticksMotorR/360)*17.3
            alpha =     (distMotorR - distMotorL) / a
        
            beta  =     alpha * 0.5

            if distMotorL != distMotorR:                            #avoiding 0 division
                s = ((distMotorR + distMotorL) / alpha) * math.sin(beta)

            else:
                s = distMotorL

            dX = int(round(dX + ((- math.sin(self.gammaCalc + beta)) * s))) 
            dY = int(round(dY + ((math.cos(self.gammaCalc + beta)) * s)))

            self.gammaCalc = self.gammaCalc + alpha

            self.gammaOut += (self.gammaCalc * 180 / math.pi) % 360
            self.gammaOut = self.gammaOut % 360

        if (315 < self.gammaOut < 361) or (-1 < self.gammaOut < 46):
            self.gammaOut = 0
            #print("\n \n Current Dir NORTH: " + str(self.gammaOut))    #[4debugging]

        elif 45 < self.gammaOut < 136:
            self.gammaOut = 90
            #print("\n \n Current Dir EAST: " + str(self.gammaOut))     #[4debugging]

        elif 135 < self.gammaOut < 226:
            self.gammaOut = 180
            #print("\n \n Current Dir SOUTH: " + str(self.gammaOut))    #[4debugging]

        elif 225 < self.gammaOut < 316:
            self.gammaOut = 270
            #print("\n \n Current Dir WEST: " + str(self.gammaOut))     #[4debugging]

        #Ergebnis durch 50 und dann runden
        self.deltaX += int(round((dX/50)))
        self.deltaY += int(round((dY/50)))

        #print('Calculation done')
        #print('current position: x = ', self.deltaX, 'y = ', self.deltaY, 'orientation =', self.gammaOut)        #[4debugging]


    #choses a path to continue driving (final)
    def backOnTrack(self, way):

        #print('Getting back on track...')                          #[4debugging]
    
        #resetting motor values
        self.motorL.reset()
        time.sleep(0.1)
        self.motorL.reset()

        self.gs.mode = 'GYRO-CAL'                                   #calculating gyro
        time.sleep(0.1)
        self.gs.mode = 'GYRO-CAL'
        time.sleep(0.1)
        self.gs.mode = 'GYRO-ANG'

        time.sleep(0.1)

        if self.deadEnd == True:
            way = 4

        #selecting left route
        if way == 1:

            #print('Route chosen: left')                            #[4debugging]

            while True:

                rgb = self.cs.bin_data('hhh')
                rotation = self.gs.value()

                self.motorL.run_forever(speed_sp=-100)
                self.motorR.run_forever(speed_sp=100)

                if (rgb[0] < 55 and rgb[1] < 85 and rgb[2] < 40) and (-135 < rotation < -45):
                    self.motorL.stop()
                    self.motorR.stop()
                    break

            self.motorR.run_timed(time_sp=1000, speed_sp=100)
            time.sleep(1.1)
            self.motorR.stop()
            self.gammaOut = (self.gammaOut - 90) % 360
            self.drive()
                

        #selecting front route
        if way == 2:

            #print('Route chosen: front')                           #[4debugging]
            self.drive()


        #selecting right route
        if way == 3:

            #print('Route chosen: right')                           #[4debugging]
            
            while True:

                rgb = self.cs.bin_data('hhh')
                #ticksL = self.motorL.position
                rotation = self.gs.value()

                self.motorL.run_forever(speed_sp=100)
                self.motorR.run_forever(speed_sp=-100)

                if (rgb[0] < 55 and rgb[1] < 85 and rgb[2] < 40) and (45 < rotation < 135):
                    self.motorL.stop()
                    self.motorR.stop()
                    break

            self.gammaOut = (self.gammaOut + 90) % 360
            self.motorR.run_timed(time_sp=1000, speed_sp=100)
            time.sleep(1.1)
            self.motorR.stop()
            self.drive()


        #selecting back route
        if way == 4:

            #print('Route chosen: back')                            #[4debugging]
            
            while True:

                rgb = self.cs.bin_data('hhh')
                rotation = self.gs.value()
                self.motorL.run_forever(speed_sp=100)
                self.motorR.run_forever(speed_sp=-100)

                if (rgb[0] < 55 and rgb[1] < 85 and rgb[2] < 40) and (135 < rotation < 225):
                    self.motorL.stop()
                    self.motorR.stop()
                    break

            self.gammaOut = (self.gammaOut + 180) % 360
            self.motorR.run_timed(time_sp=1000, speed_sp=100)
            time.sleep(1.1)
            self.motorR.stop()
            self.drive()

    #forward lol
    def forward(self):

        if self.blueField:
           #print('Getting off of blue field...')                  #[4debugging]
           while True:
               rgb = self.cs.bin_data('hhh')
               self.motorL.run_forever(speed_sp=50)
               self.motorR.run_forever(speed_sp=60)  
               if rgb[0] > self.bb12 and rgb[1] > self.bb22 and rgb[2] > self.bb32:
                   self.motorL.stop()
                   self.motorR.stop()
                   time.sleep(0.1)
                   break   

        if self.redField:
            #print('Getting off of red field...')                   #[4debugging]
            while True:
                rgb = self.cs.bin_data('hhh')
                self.motorL.run_forever(speed_sp=50)
                self.motorR.run_forever(speed_sp=60)

                if rgb[0] > self.rb11 and rgb[1] > self.rb21 and rgb[2] > self.rb31:
                    self.motorL.stop()
                    self.motorR.stop()
                    self.motorL.run_timed(time_sp=1500, speed_sp=60)
                    self.motorR.run_timed(time_sp=1500, speed_sp=70)
                    time.sleep(2)
                    break   
        self.blueField = False
        self.redField = False
        #print('Down from field, now moving forward...')            #[4debugging]
        time.sleep(0.5)

        self.motorL.run_timed(time_sp=1000, speed_sp=60)
        self.motorR.run_timed(time_sp=1000, speed_sp=70)

        time.sleep(1.1)