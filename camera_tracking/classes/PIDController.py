class PIDController:
    def __init__(self,kp,ki,kd):
        self.kp = kp # proportional Gain (push)
        self.ki = ki # integral gain (windup)
        self.kd = kd # derivative gain (brake)

        self.previous_error = 0
        self.integral = 0
    def compute(self,current_error): #PID
        # proprotionslity
        P = self.kp * current_error

        # integral (accumulates all the past errors)
        self.integral += current_error
        I = self.ki * self.integral 

        # derivative (calculates velocity to apply brakes)
        self.derivative = current_error - self.previous_error
        D = self.kd * self.derivative

        # save the error state so it could be used for the next frame
        self.previous_error = current_error

        # output the required physical force
        return P + I + D