#!/usr/bin/env python3

#
# Runs initial sky scans and automatically adjusts solar cell to find and
# orient itself in the position of maximum power. This can be left running
# and the cell will rescan its immediate neighborhood and re-adjust over time.
#
# Ethan Kern
# 31May2018

import numpy as np
import time
import PiMotor
from Adafruit import ADS1x15

mrot = PiMotor.Stepper("STEPPER1") # Motor that controls rotation angle.
mpit = PiMotor.Stepper("STEPPER2") # Motor that controls pitch angle.

delay = 0.04  # Delay time to be used between the motors' fine stepping in
              # every movement in this script.

pitcount = 0  # These counting variables are used as "global" positions to
rotcount = 0  # keep track of the motors over numerous scans.

                              # Function doubles the amount of steps available
                              # by default in the stepper motors. We call this
                              # function whenever we want to scan.
def split_steps(total, motor, delay):  # Args:
                                       # total num of steps to scan over,
                                       # which motor to run, delay time

	voltages = np.empty((0, 100))  # Array of voltage measurements to be
	                               # populated.


	for i in range(1, total+1):  # for loop performs a scan forward over
	                             # the desired number of steps, 1 at a time.
	                             # The odd/even checks will alternate
	                             # whether forward1 or forward2 is called.

		if i % 2 != 0: # If step index is odd.

			motor.forward1(delay)    # Rotate motor forward 1 step.

			readVolts = ADS1x15().readADCDifferential23(4096, 128)\
		                         *0.005 # Reads voltage of solar cell
		                                # and accounts for the
		                                # measurement being reduced by
		                                # a factor of 5 due to the
                                        # voltage divider.

			voltages = np.append(voltages, readVolts)
		                             # Store voltage measurement.


		else:     # If step index is even.

			motor.forward2(delay)

			readVolts = ADS1x15().readADCDifferential23(4096, 128)\
			                                                 *0.005

			voltages = np.append(voltages, readVolts)

		print('Current Voltage: ', voltages[i-1]) # Prints current
		                                          # reading.
		time.sleep(0.1)

	return voltages    # Function returns an array of voltages.

                        # Function performs a rotation scan and tracks rotation
                        # motor's position.
def rot_scan(steps, rotcount): # Args:
                               # number of steps forward to scan over, a number
                               # containing the rotation motor's current
                               # position from zero.
	delay = 0.04

	time.sleep(2)

	voltages = split_steps(steps, mrot, delay) # Call function to perform
	                                           # the scan over these steps
	                                           # 1-by-1, stores voltage
	                                           # readings in an array.
	rotcount += steps    # Increases current rotation position by the
	                     # number of steps it just moved through.
	time.sleep(2)

	maxvoltpos = np.argmax(voltages) # Finds the index of the highest
	                                 # voltage reading.

	print('Rotating back %3.2f degrees' %(3.6*(steps-maxvoltpos)))

	for backstep in range(1, steps-maxvoltpos): # The index is used to
	                                             # find how many steps to
	                                             # move back and reach the
	                                             # desired position.

		if backstep % 2 != 0:     # Same odd/even alternation method
		                          # as in split_steps().
			mrot.backward1(delay)

		else:
			mrot.backward2(delay)

		rotcount -= 1 # The rotation position is decreased by 1 for
		              # every step backward it rotates.

	return rotcount    # Function returns the updated rotation position.

            # Function performs a pitch scan and tracks pitch motor's position.
def pit_scan(steps, pitcount): # Args:
                               # number of steps forward to scan over, a number
                               # containing the pitch motor's current
                               # position from zero.
	delay = 0.04

	time.sleep(2)

	voltages = split_steps(steps, mpit, delay) # Calls function similarly
	                                           # to obtain voltage
	                                           # measurements, this time
	                                           # through different pitches.
	pitcount += steps  # Increases current pitch position by number of
	                   # steps it just moved forward through.
	time.sleep(2)

	maxvoltpos = np.argmax(voltages) # Find index where highest voltage is.

	print('Pitching back %3.2f degrees' %(3.6*(steps-maxvoltpos)))

	for backstep in range(1, steps-maxvoltpos+1): # Steps back through
	                                               # pitch similarly until
	                                               # it reaches the best
	                                               # position.
		if backstep % 2 != 0:
			mpit.backward1(delay)

		else:
			mpit.backward2(delay)

		pitcount -= 1     # Decrease pitch position by the number of
		                  # steps it just moved backward through.

	return pitcount  # Function returns the updated position of the
	                  # pitch motor.




print('\nStarting rotation scan...\n')

mpit.backward(delay,2) # Initially bring the pitch down from zenith and account
pitcount = -4          # for this pitch position change.

rotcount = rot_scan(100, rotcount) # Initial rotation scan over 3.6 degree
		                 # steps, moves to best rot angle and stores
		                 # position.
                                 # NOTE: 100 steps = 360 degrees

print('\nStarting pitch scan...\n')

mpit.backward(delay,3)  # Initially bring pitch down until it's 45 degrees.
pitcount -= 6           # Account for this negative pitch change.

pitcount = pit_scan(10, pitcount) # Initial pitch scan. Stores position at end.
                                  # NOTE: 10 steps = 36 degrees

print('\nBest orientation found.\n')
print('Current position: %3.2f degrees, pitch %3.2f degrees' \
                                            %(3.6*rotcount, 3.6*pitcount))

while True: # Now that it's at the best position, we will keep it reading
             # the voltage in an infinite loop, and enter another loop when
             # we want it to adjust itself periodically.

	t = 0  # Reset time whenever we re-adjust.
	t0 = time.perf_counter()

	while t < 1800:          # After 30 minutes at the same position, it
	                          # will exit this loop to adjust itself.

		print('Current Voltage: ', \
		              ADS1x15().readADCDifferential23(4096, 128)*0.005)
		time.sleep(5)

		t = time.perf_counter() - t0

		print('Seconds elapsed: ', int(t))

	print('\nUpdating scan...\n')

	mrot.backward(delay, 4) # Rotate backward a bit to begin a small
	rotcount -= 8          # rotation scan forward, accounting for change.

	rotcount = rot_scan(16, rotcount)  # Scans forward through twice the
	                                   # distance it moved backward, and
	                                   # stores the updated position.

	                   # These statements check how far down in either
	                   # direction the solar cell is pitched, and stops it
	                   # from pitching into the ground when it lowers.
	if np.abs(pitcount) <= 8 and np.abs(pitcount) > 6:
		mpit.backward(delay, 1)
		pitcount -= 2

	elif np.abs(pitcount) <= 6:
		mpit.backward(delay, 2)
		pitcount -= 4

	pitcount = pit_scan(5, pitcount)  # Run forward pitch scan and store
	                                  # updated pitch position.
	print('Current position: %3.2f degrees, pitch %3.2f degrees' \
                                           	%(3.6*rotcount, 3.6*pitcount))
