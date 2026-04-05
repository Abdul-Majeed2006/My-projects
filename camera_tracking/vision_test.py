import cv2
import numpy as np

# to intialize camera
cap = cv2.VideoCapture(0)
print("Camera intialized")

if not cap.isOpened():
    print('camera failed to open')
    exit()

print('commencing video loop, press q to stop')

while True:
    #trying data acquisition
    # cap.rad() returns ret and frame, ret tells us if the camera is reading values an dreturns true or false
    # frame returns out a matrix of pixel coordinates and rgb colors
    ret, frame = cap.read()
    
    # if ret =  false break
    if not ret:
        print('camera not reading')
        break

    # we need to convert our BGR to hue and saturation and value
    # to be able to cancel out noises
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # we need to be able to define the colors we want it to see
    # define an upper end of the color and a lower end of the color
    # that is to be passed into the system
    lower = np.array([100,100,100])
    upper = np.array([140,255,255])

    # using this threshold to get a new binary matrix to identify 
    # anything in between
    mask = cv2.inRange(hsv_frame, lower, upper)
    
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

                # now draw a red circle on our target
                cv2.circle(frame,(cx,cy),2,(0,0,255), -1)

                print(f'{cx},{cy}')


    # now render the new mask to a new window to observe th logic
    cv2.imshow('Binary Mask -view',mask)

    # it works now we run the target extraction logic, 
    # now lets render the matrix from frame to a window 
    cv2.imshow('Targeting Feed - BGR', frame)

    # create a break key to interupt and a limit to how many times it reads per second
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print('breaking workflow')
        break

cap.release()
cv2.destroyAllWindows()