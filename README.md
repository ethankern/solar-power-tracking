# solar-power-tracking: Tracking the Maximum Power Generation of a Solar Cell's Orientation
Continuously adjusts a solar cell to generate maximum power via stepper motors.

This project uses two stepper motors interfaced by the PiMotor library and the SB Motor Shield for a Raspberry Pi to pitch and rotate a solar cell so that it can be aimed autonomously from power-on in the direction that generates the highest power possible. Then, after some time it automatically readjusts in case its environment has changed, and re-finds the orientation of maximum power. The voltage drop generated across the solar panel is directly used as feedback to determine where to point.
