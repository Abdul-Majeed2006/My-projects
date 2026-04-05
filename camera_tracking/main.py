import sys, time
import uselect
from machine import PWM, Pin
# listen for message from computer, and also prevent pico from freezing while waiting for data
poller = uselect.poll()
poller.register(sys.stdin,uselect.POLLIN)

print('system ready and listening')

# initialize pins
pan_servo = PWM(Pin(15))
pan_servo.freq(50)

tilt_servo = PWM(Pin(14))
tilt_servo.freq(50)

# declare tracking varibles to center
current_pan_pwm = 5000
current_tilt_pwm = 5000

# lock servos to middle
pan_servo.duty_u16(current_pan_pwm)
tilt_servo.duty_u16(current_tilt_pwm)

# intialize hert beat
last_heartbeat = time.ticks_ms()
while True:
    # is there any data waiting in the usb
    if poller.poll(0):
        try:
            # extract all data until \n i.e goes to next line
            raw_data = sys.stdin.readline()
            
            # check if data matches our data format to avoid reading corrupted data
            if raw_data.startswith('<') and raw_data.endswith('>\n'):
                # if yes strip the data of < and >
                clean_data = raw_data[1:-2]
                
                # split it by ','
                parts = clean_data.split(',')
                
                # check if two datas were sent
                if len(parts) == 2:
                    # convert to floats
                    pan_force, tilt_force = [float(_) for _ in parts]
                    
                    # inject error force into the physical position
                    current_pan_pwm -= int(pan_force)
                    current_tilt_pwm += int(tilt_force)
                    
                    # safety clamps
                    if current_pan_pwm > 7000:
                        current_pan_pwm = 7000
                    elif current_pan_pwm <3000:
                        current_pan_pwm = 3000
                        
                    if current_tilt_pwm > 7000:
                        current_tilt_pwm = 7000
                    elif current_tilt_pwm <3000:
                        current_tilt_pwm = 3000
                        
                    # send new calculated electrical pulse to pico
                    pan_servo.duty_u16(current_pan_pwm)
                    tilt_servo.duty_u16(current_tilt_pwm)
                    
                    print(f'pic0, pan pwm {current_pan_pwm}, tilt pwm {current_tilt_pwm}')
        except Exception as e:
            # if we didnt receive the right data or we recieved corrrupt data pass and run loop again
            print(f'i didnt work {e}')
            pass
    # heart beat logic
    if time.ticks_diff(time.ticks_ms(), last_heartbeat) > 1000:
        print('pico is alive and reading')
        last_heartbeat = time.ticks_ms()