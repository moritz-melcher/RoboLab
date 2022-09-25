# !/usr/bin/env python3

#this script sets the rgb color values according to the current brightness levels

import ev3dev.ev3 as ev3
import time

cs = ev3.ColorSensor()  #initializing color sensor and setting it to rgb mode
cs.mode = 'RGB-RAW'

#red evaluation
ev3.Sound.speak('red')
time.sleep(3)

i = 0

a = 0
b = 0
c = 0

while i < 3:
    a += cs.bin_data('hhh')[0]
    b += cs.bin_data('hhh')[1]
    c += cs.bin_data('hhh')[2]
    i += 1
    time.sleep(2)
    ev3.Sound.beep()

col_val = str(int(a/3)) + '\n' + str(int(b/3)) + '\n' + str(int(c/3)) + '\n'

# with open('colorValues.txt', 'w') as f:
#    f.write(col_val)

#blue evaluation
ev3.Sound.speak('blue')
time.sleep(3)

i = 0

a = 0
b = 0
c = 0

while i < 3:
    a += cs.bin_data('hhh')[0]
    b += cs.bin_data('hhh')[1]
    c += cs.bin_data('hhh')[2]
    i += 1
    time.sleep(2)
    ev3.Sound.beep()

col_val = col_val + str(int(a/3)) + '\n' + str(int(b/3)) + '\n' + str(int(c/3)) + '\n'

#with open('colorValues.txt', 'a') as f:
#   f.write(col_val)

#white evaluation
ev3.Sound.speak('white')
time.sleep(3)

i = 0

a = 0
b = 0
c = 0

while i < 3:
    a += cs.bin_data('hhh')[0]
    b += cs.bin_data('hhh')[1]
    c += cs.bin_data('hhh')[2]
    i += 1
    time.sleep(2)
    ev3.Sound.beep()

col_val = col_val + str(int(a/3)) + '\n' + str(int(b/3)) + '\n' + str(int(c/3)) + '\n'

#with open('colorValues.txt', 'a') as f:
#    f.write(col_val)

#black evaluation
ev3.Sound.speak('black')
time.sleep(3)

i = 0

a = 0
b = 0
c = 0

while i < 3:
    a += cs.bin_data('hhh')[0]
    b += cs.bin_data('hhh')[1]
    c += cs.bin_data('hhh')[2]
    i += 1
    time.sleep(2)
    ev3.Sound.beep()

col_val = col_val + str(int(a/3)) + '\n' + str(int(b/3)) + '\n' + str(int(c/3))

with open('colorValues.txt', 'w') as f:
    f.write(col_val)
