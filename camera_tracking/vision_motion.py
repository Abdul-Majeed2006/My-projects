import cv2
import numpy as np
from classes.PIDController  import PIDController
import serial, time

# to intialize camera
cap = cv2.VideoCapture(0)
print("Camera intialized")

if not cap.isOpened():
    print('camera failed to open')
    exit()

print('commencing video loop, press q to stop')


# intialize PID controllers for the pan and tilt motors, they have to be 
# separate because different forces act on them, gravity acts on our upward and downward tilt but is negligible on our pan 
# since it only rotates about the earth splane
# kp = 0.1. ki = 0 kd = 0.05
pan_pid = PIDController(0.1, 0.0, 0.05)
tilt_pid = PIDController(0.1, 0.0, 0.05)

# initialize serial port
try:
    pico_serial = serial.Serial('COM4', 115200, timeout = 0.1)
    print('COM link established with pico')
except Exception as e:
    print('serial port failed')
    pico_serial = None

# intialize the calculus engine that, checks the frame matrix fro moving pixels on the video
back_sub = cv2.createBackgroundSubtractorMOG2(history = 3000,varThreshold = 40, detectShadows = False)

# extract the camearas physical resolution limits
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# get center of the width and height use// to remain int and strip of remainders in the division
center_x = W//2
center_y = H//2


while True:
    #trying data acquisition
    # cap.rad() returns ret and frame, ret tells us if the camera is reading values an dreturns true or false
    # frame returns out a matrix of pixel coordinates and rgb colors
    ret, frame = cap.read()
    
    # if ret =  false break
    if not ret:
        print('camera not reading')
        break

    # using MOG2 to get a new binary matrix to identify 
    # any frame that moves
    mask = back_sub.apply(frame)

    # create an array of ones which is our brush to clea noice
    kernel = np.ones((5,5), np.uint8)

    # sweep our brush though the mask to clean all the tiny noice
    # cleans all tiny white noice to black
    mask = cv2.erode(mask, kernel, iterations = 1)
    # cleans any place we see a lot of white and amplify it
    mask = cv2.dilate(mask, kernel, iterations = 3)
    
    # lets trace all the white bobs in our image
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # now we confirm if there are actually any blue objects in the screen
    if len(contours) > 0:
        # sort and isolate the largest white(blue) object
        largest_contour = max(contours, key= cv2.contourArea)

        # noise rejection i.e reject tiny objects and its area is more that 500 pixels
        if cv2.contourArea(largest_contour) > 500:
            # calculate the middle of the object
            M = cv2.moments(largest_contour)
            if M['m00'] != 0:
                # x coordinate
                cx = int(M['m10']/M['m00'])
                # y coordinate
                cy = int(M['m01']/M['m00'])

                # print coordinate of target
                #print(f'x{cx},y{cy}')

                # now draw a red circle on our target
                cv2.circle(frame,(cx,cy),2,(0,0,255), -1)

                # claculate the offset in you servos aim and your drwn circle aim
                error_x = cx - center_x
                error_y = cy - center_y

                # draw the crosshairs to visualize the dead zone
                cv2.line(frame,(center_x,0),(center_x,H),(0,255,0),1)
                cv2.line(frame,(0,center_y),(W,center_y),(0,255,0),1)

                # Draw line to represent the error
                cv2.line(frame,(center_x,center_y),(cx,cy),(255,0,0),2)

                # read error
                #print(f'x error{error_x}, y error{error_y}')

                # conpute our dynamic PID control for pan and tilt
                pan_force = pan_pid.compute(error_x)
                tilt_force = tilt_pid.compute(error_y)

                # print x error and force required for pid control
                #print(f'Raw x error{error_x} pan force{pan_force:.2f}') 

                # send data to pico send data in 2 sig figs 
                payload = f'<{pan_force:.2f},{tilt_force:.2f}>\n'

                # if the pico_serial exists
                if pico_serial is not None:
                    pico_serial.write(payload.encode('utf-8'))

                    # check if pico reads anything  and send it back
                    if pico_serial.in_waiting > 0 :
                        # READ THE RECEIVED DATA
                        pico_response = pico_serial.readline().decode('utf-8').strip()
                        print(f'pico replies {pico_response}')




    # now render the new mask to a new window to observe th logic
    cv2.imshow('Binary Mask -view',mask)

    # it works now we run the target extraction logic, 
    # now lets render the matrix from frame to a window 
    cv2.imshow('Targeting Feed - BGR', frame)

    # create a break key to interupt and a limit to how many times it reads per second
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print('breaking workflow')
        pico_serial = None
        break

cap.release()
cv2.destroyAllWindows()