# Autonomous 2-Axis Target Tracking System (USNA WRC)

This repository contains the foundational software architecture for an autonomous, 2-axis targeting and tracking turret. Due to the high computational cost of Machine Vision and the strict physical timing constraints of hardware PWM actuation, this system utilizes a **Split-Brain Architecture** bridging a Python-based PC node and a MicroPython-based Raspberry Pi Pico 2W node.

## System Architecture

### 1. The High-Level Perception Node (OpenCV)
**File:** `vision_test.py`
The PC handles heavy matrix processing. It executes a live real-time analysis of a 640x480 webcam matrix. 
- Transposes BGR color space to HSV space to isolate targets regardless of ambient brightness.
- Implements `cv2.findContours` and Image Moments (`M['m10']/M['m00']`) to dynamically calculate the physical center-of-mass (`cx`, `cy`) of the target.
- Automatically computes the true 2D Error Vector relative to the dead-center crosshairs of the optical sensor.

### 2. The Feedback Control Strategy (PID)
**File:** `classes/PIDController.py`
Raw pixel error vectors cannot be fed directly to mechanical servos. Doing so triggers catastrophic overshoot and oscillation due to unmodeled physical inertia.
- The error vectors are piped through a software-based Proportional-Integral-Derivative (PID) controller. 
- Generating `pan_force` and `tilt_force` vectors to provide mathematically dampened mechanical pushes.

### 3. The Hardware Serial Bridge
The PC Node owns the `pyserial` serial connection to the Pi Pico 2W over USB UART. 
- The data is wrapped in rigid embedded packet strings (e.g., `<PAN_FORCE,TILT_FORCE>\n`).
- The `\n` line feed is enforced as an absolute termination character to prevent buffer overflow and desynchronization in the Pico's RAM.
- Operates in full duplex; the master vision script reads and prints telemetry returned by the embedded microcontroller.

### 4. The Low-Level Actuation Node (MicroPython)
**File:** `main.py` (Resides internally on the Pico 2W)
The Pico operates as a blind execution slave. 
- Utilizes `uselect.poll()` to ingest the serial stream asynchronously without hanging the processor. 
- Validates the packet syntax using a strict state machine. Corrupted packets (e.g., missing `<`) are aggressively rejected and discarded to prevent execution faults.
- Converts the floating-point force vectors into 50Hz Pulse Width Modulation (PWM) `duty_u16` duty cycles.
- Features a hard Mathematical Safety Clamp (limiting output between `3000` and `7000`) to guarantee the generated signal never over-ranges the physical plastic limits of the servo gears.

## Hardware Integration Constraints (WRC Tech Services)
If deploying this code to standard hobby servos or a Caddx GM3 FPV Gimbal, the following physical constraints must be audited prior to wiring:
1. **Voltage Regulation:** Do NOT power the servos utilizing the Pico's internal `VBUS` or `3V3` headers. The actuator current draw will burn the logic board. Utilize a dedicated external high-amperage 5V step-down or LiPo battery. 
2. **Logic Ground Reference:** The external power supply Ground **must** be physically tied to the Pico's `GND` pins. Failure to share electrical reference grounds negates the PWM signal topology.
3. **Signal Protocol:** Ensure the mechanical receiver is explicitly rated for 50Hz Analog PWM on its input pins. 
