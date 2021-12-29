import cv2 as cv
import numpy as np
import random as rand
import imutils

dummy = cv.imread('dummy.jpg')
dummy = cv.resize(dummy, (600, 470))

car = cv.imread('raceCar.png')
car = imutils.resize(car, width=80)
car = cv.rotate(car, cv.ROTATE_90_CLOCKWISE)

original = np.zeros_like(dummy)
original = imutils.resize(original, width=720)

winName = "Obstacle Detection"
y, h, dx, dy = (0, 10, 4, 4)
x = rand.randint(11, dummy.shape[1]-6)
hitDelayCounter = 0
hit, miss = 0, 0

hi, he = (original.shape[0]-20) - car.shape[0], original.shape[0]-20
wi, we = 150, 150 + car.shape[1]
laneHeight, length, carLen = int(original.shape[0]//6)-4, 50, 30
ballSize = 10
carDirection = "Left"

# LANE SEPARATOR
jump, jmpTime, step = 1, 30, 5

laneSeparators = [{
    "startHeight": 0,
    "endHeight": 0,
    "step": step,
    "currHeight": 0
}]

def moveLeft(img, startMargin, endMargin, deltaX, cLen, points):
    midRoad = int((endMargin - startMargin)//2)

    wi, we = points

    if not (midRoad-cLen < wi < we < midRoad+cLen):
        wi, we = wi-deltaX, we-deltaX

        if wi < startMargin:
            wi, we = startMargin, startMargin + img.shape[1]
    
    return wi, we

def moveRight(img, startMargin, endMargin, deltaX, cLen, points):
    midRoad = int((endMargin - startMargin)//2) + startMargin

    wi, we = points

    if not (midRoad-cLen < wi < we < midRoad+cLen):
        wi, we = wi+deltaX, we+deltaX

        if we > endMargin:
            wi, we = endMargin - img.shape[1], endMargin
    
    return wi, we

def updateHitDelay(delay):
    if delay >= 1:
        delay += 1
        if delay > 10:
            delay = 0
    return delay

def updateJump(jump):
    if jump >= 1:
        jump += 1
        if jump > jmpTime:
            jump = 0
    return jump

def getCarDirection(points):
    wi, we = points

    if we < leftEnd:
        return "Left"

    if wi > rightStart:
        return "Right"
    
    return "Middle"



while True:
    img = original.copy()
    cv.rectangle(img, (5, 5), (10, img.shape[0]-10), (123, 23, 232), cv.FILLED)
    cv.rectangle(img, (img.shape[1]-10, 5), (img.shape[1]-5, img.shape[0]-10), (123, 23, 232), cv.FILLED)

    leftStart, leftEnd = 12, int(img.shape[1]//2)-2
    rightStart, rightEnd = int(img.shape[1]//2)+12, img.shape[1]-15

    # Ball
    cv.circle(img, (x, y), ballSize, (223, 43, 22), cv.FILLED)
    cv.circle(img, (x, y), ballSize, (123, 43, 252), 2)
    y, h = y+dy, h+dy

    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    canny = cv.Canny(gray, 75, 125)

    contours, _ = cv.findContours(canny, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    for cont in contours:
        area = cv.contourArea(cont)

        if area < 2000:
            al = cv.arcLength(cont, True)
            approx = cv.approxPolyDP(cont, .02*al, True)

            if len(approx) > 4:
                _x, _y, _w, _h = cv.boundingRect(approx)
                # cv.rectangle(img, (_x, _y), (_x+_w, _y+_h), (213, 23, 122), 2)

                if leftStart <= _x <= leftEnd and leftStart <= (_x+_w) <= leftEnd:
                    wi, we = moveRight(car, rightStart, rightEnd, dx, carLen, (wi, we))                    
                elif rightStart <= _x <= rightEnd and rightStart <= (_x+_w) <= rightEnd:
                    wi, we = moveLeft(car, leftStart, leftEnd, dx, carLen, (wi, we))
                else:
                    if not ((leftStart <= wi and we <= leftEnd) or (rightStart <= wi and we <= rightEnd)):
                        if carDirection == "Left":
                            wi, we = moveLeft(car, leftStart, leftEnd, dx, carLen, (wi, we))
                        elif carDirection == "Right":   
                            wi, we = moveRight(car, rightStart, rightEnd, dx, carLen, (wi, we))                           

                carDirection = getCarDirection((wi, we))
                img[hi:he, wi:we] = car

                if wi <= _x < (_x+_w) <= we and (_y+_h) >= hi and hitDelayCounter == 0:
                    hitDelayCounter = 1
                    hit += 1

    hitDelayCounter = updateHitDelay(hitDelayCounter)
    
    if h >= img.shape[0]:
        x = rand.randint(25, img.shape[1]-125)
        length = rand.randint(10, 100)
        ballSize = rand.randint(14, 23)
        y, h = (0, 10)
        miss += 1

    ################ ROAD MARKINGS ########################

    # Left Side
    if carDirection == "Left":
        cv.putText(img, carDirection.upper(), (int(leftEnd//3), int(img.shape[0]//2)), cv.FONT_HERSHEY_COMPLEX, 1.5, (255, 255, 255), 1)

    # Right Side
    if carDirection == "Right":
        cv.putText(img, carDirection.upper(), (rightStart + int((rightEnd - rightStart)//3), int(img.shape[0]//2)), cv.FONT_HERSHEY_COMPLEX, 1.5, (255, 255, 255), 1)
    
    cv.putText(img, f"Hit: {hit}", (50, 30), cv.FONT_HERSHEY_PLAIN, 1.2, (25, 55, 255), 1)
    cv.putText(img, f"Miss: {miss}", (200, 30), cv.FONT_HERSHEY_PLAIN, 1.2, (25, 55, 255), 1)
    cv.putText(img, f"Car: x{dx}", (rightStart + 50, 30), cv.FONT_HERSHEY_PLAIN, 1.2, (25, 55, 255), 1)
    cv.putText(img, f"Object: x{dy}", (rightEnd - 150, 30), cv.FONT_HERSHEY_PLAIN, 1.2, (25, 55, 255), 1)
    
    # LANE SEPARATOR
    
    if laneSeparators[-1]["currHeight"] < laneHeight:
        laneSeparators[-1]["currHeight"] += laneSeparators[-1]["step"]
        laneSeparators[-1]["endHeight"] = laneSeparators[-1]["currHeight"]
    elif laneSeparators[-1]["currHeight"] == laneHeight and jump == 0:
        jump = 1
        laneSeparators[-1]["endHeight"] += laneSeparators[-1]["step"]
        laneSeparators[-1]["endHeight"] += jump
        laneSeparators[-1]["startHeight"] = laneSeparators[-1]["endHeight"] - laneSeparators[-1]["currHeight"]
        
        # Append New Lane Separator
        laneSeparators.append({
            "startHeight": 0,
            "endHeight": 0,
            "step": step,
            "currHeight": 0
        })

    # Moving the lane separators
    for lane in laneSeparators:
        if lane["currHeight"] == laneHeight:
            lane["endHeight"] += lane["step"]
            lane["startHeight"] = lane["endHeight"] - lane["currHeight"]

        cv.rectangle(img, (int(img.shape[1]//2), lane["startHeight"]), 
        (int(img.shape[1]//2) + 10, lane["endHeight"]), (255, 255, 255), cv.FILLED)

    # Remove Lane Lines that have no use
    if laneSeparators[0]["startHeight"] > img.shape[0]:
        laneSeparators = laneSeparators[1:]

    jump = updateJump(jump)

    ########################################################

    img[hi:he, wi:we] = car
    
    # cv.namedWindow(winName, cv.WINDOW_NORMAL)
    # cv.setWindowProperty(winName, cv.WINDOW_NORMAL, cv.WINDOW_FREERATIO)
    cv.imshow(winName, img)
    key = cv.waitKey(1) & 0xFF

    if key == ord('q'):
        cv.destroyAllWindows()
        break
    if key == ord('a'):
        dx += 1
    if key == ord('d'):
        dx -= 1
        if dx < 1: dx = 1
    if key == ord('h'):
        dy += 1
    if key == ord('l'):
        dy -= 1
        if dy < 1: dy = 1
