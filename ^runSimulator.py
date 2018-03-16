"""
TODO: 
    0) Fix the polygons for loop in init(). It's messy. Maybe, try defining
        all the pieces grouped per face instead of all at once, then "flatten"
        the entire thing later. Don't actually use flatten though. Bad effects.
    1) Remove the need to input indivFactor into the puzzle file.
        Instead, I want the program to infer it from the data.
    2) Somehow incorporate mouse interaction. idk
    3) Write a solved-state checker. I think this will somehow incorporate
        rotIns, and check the ideal rotIns against the current one.
        This might cause problems for puzzles with duplicate pieces though...
    4) Macros. Algorithms. Anything like that. Recording, playing back, etc.
"""

import pygame
from numpy import (array, dot, arctan, copy, linspace, 
                    eye, cos, pi, logical_or as lor)
from random import randint
from os import getcwd
from mathFuncs import arbiRot, transform as tr, centroid, offset
from ast import literal_eval as ev

#.........................................................Screen Initialization

pygame.init()

x,y = 1024,720
screen = pygame.display.set_mode((x,y), pygame.RESIZABLE)
pygame.display.set_caption("Braden's Puzzle Simulator")
clock = pygame.time.Clock()

names = ["cube333", "cube222", "pentaMixup", "pentaPrism", "skewb"]

fileName = getcwd() + "/{}.txt".format(names[4])

#..........................................................Constants Definition

off = 0.035 #offset
D2R = 3.14159265358979/180 #Degrees to radians factor of conversion
frameRate = 60 #Frames per second
rotLength = 1/4 #How long the rotation takes, in seconds
factorCoef = 1.2 #The factor by which to scale the factor lol
speedCoef = 1.2 #The factor by which to scale the speed

#..........................................................Variables Definition

factor = y/4*(y<=x) + x/4*(x<y) #The factor by which to scale the figure
indivFactor = 1
speed = 120/frameRate #How fast the figure spins (no unit)
background = False #Should the stickers behind be rendered?
backColour = (175,175,175) #The background colour
done = False #Is the program done
rotMode = True #True will be free, False will be fixed about the y axis
moves = [] #The memory of every move done
undo = 0 #how many levels of undo

#.......................................................Data Generation Section

rotX = arbiRot([1,0,0])
rotY = arbiRot([0,1,0])
rotZ = arbiRot([0,0,1])

polygons, colours, direcs, midpoints, rotIns = [], [], [], [], []
moveKeys, permu = {}, []

axes = eye(3)
axesFixed = eye(3)

file = open(fileName, "r")
fullFile = file.read()
file.close()

def init():
    global factor, polygons, colours, direcs, midpoints, rotIns, permu,moveKeys
    polygons, colours, direcs, midpoints, rotIns = [], [], [], [], []
    moveKeys, permu = {}, []

    lines = fullFile.split("\n\n\n")

    for i in range(len(lines)):
        lines[i] = ev("".join(lines[i].split()))
    
    indivFactor = lines[0]
    factor = (y/4*(y<=x) + x/4*(x<y)) / indivFactor
    
    faceLengths = []
    
    for face in lines[1]:
        if type(face) == list:
            faceDefn = len(polygons)
            
            for piece in face:
                if type(piece) == list:
                    pieceDefn = len(polygons)
                    
                    points = []
                    
                    for point in piece:
                        if type(point) == list:
                            pointDefn = len(points)
                            points += [point]
                        elif type(point) == tuple:
                            points += [tr(points[pointDefn], point)]

                    polygons += [offset(array(points), off*indivFactor)]
                    
                elif type(piece) == tuple:
                    polygons += [tr( copy(polygons[pieceDefn]), piece )]
            piecesPerFace = len(polygons) - faceDefn

        elif type(face) == tuple:
            for i in range(piecesPerFace):
                polygons += [tr( copy(polygons[faceDefn + i]) , face )]
        faceLengths += [int(len(polygons) - sum(faceLengths))]
    
    fls = faceLengths
    for face in lines[2]:
        if type(face) == tuple:
            colours += [face] * fls[0]
        elif type(face) == list:
            colours += face
        fls = fls[1:]
    
    for face in lines[3]:
        direcs += [face] * faceLengths[0]
        faceLengths = faceLengths[1:]

    for polygon in polygons:
        midpoints += [centroid(polygon)]
    
    for face in lines[4]:
        rotIns += [array(piece) for piece in face]

    for i in range(len(lines[5])):
        moveKeys[ord(lines[5][i])] = (i+1, arbiRot(lines[6][i]), lines[7][i])
    
    for i in range(len(lines[8])):
        permu += [[lines[8][i], list(array(order(lines[8][i]))+1)]]
    
    mostPoints = max(map(len,polygons))
    for i in range(len(polygons)):
        diff = mostPoints - len(polygons[i])
        polygons[i] = array(list(polygons[i]) + ([polygons[i][-1]] * diff))
    
    polygons, colours, direcs = array(polygons), array(colours), array(direcs)
    midpoints, rotIns, permu = array(midpoints), array(rotIns), array(permu)
    direcs = direcs.astype('float64')

#...............................................................Drawing Section

lz = lambda x: list(zip(*x))
order = lambda x: lz(sorted(lz(lz(enumerate(x))[::-1])))[1]
prepare = lambda data: lz(( data[:,:,0]*factor+x/2, -data[:,:,1]*factor+y/2 ))

def render(axes):
    dirs = lor(dot(copy(direcs),axes)[:,2]>=0 , background)
    mps = array(order(dot(copy(midpoints),axes)[:,2]))
    toRender = mps[dirs[mps]] #the render indices to use
    
    polys = prepare(dot(copy(polygons[toRender]),axes))
    cols = colours[toRender]
    for poly,col in zip(polys,cols):
        pygame.draw.polygon(screen, col, lz(poly))

#.................................................................Moves Section

p = lambda s: print(s, end="\n\n")

def turn(move, sense): #Sense is clockwise vs counter clockwise
    ID, rot, degrees = move
    
    smooth = lambda ps, angle: (1-cos(2*pi*linspace(0,1,ps+1))) * angle/ps
    points = int(frameRate*rotLength) #How many frames per rotation
    ts = smooth(points, degrees) #The t values of the smoothstep function

    toRot = [i for i in range(len(rotIns)) if ID in rotIns[i]] #"to rotate"
    
    polyTemp = dot(copy(polygons[toRot]), rot(degrees*sense))
    dirTemp = dot(copy(direcs[toRot]), rot(degrees*sense))
    midTemp = dot(copy(midpoints[toRot]), rot(degrees*sense))
    
    per = permu[ID-1, (sense+1)//2]
    for i in toRot:
        rotIns[i] = per[rotIns[i]-1]
    
    for t in ts:
        polygons[toRot] = dot(polygons[toRot], rot(t*sense))
        direcs[toRot] = dot(direcs[toRot], rot(t*sense))
        midpoints[toRot] = dot(midpoints[toRot], rot(t*sense))
        
        keyPresses()
        eventHandling(moving = True)
        refresh()
        if done:
            return
    
    polygons[toRot] = polyTemp
    direcs[toRot] = dirTemp
    midpoints[toRot] = midTemp

def scramble(times = 50, record = False):
    global moves, undo    
    moves *= record
    undo *= record
    
    turns = list(moveKeys.values())
    senses = [-1, 1]
    turnOld, turnNew, senseOld, senseNew = -1, -1, -1, 0
    
    for i in range(times):
        while True:
            turnNew = randint(0, len(turns)-1)
            senseNew = randint(0,1)
            if turnOld != turnNew or senseOld == senseNew: break
        turnOld, senseOld = turnNew, senseNew
        
        turn(turns[turnNew], senses[senseNew])
        moves += [(turns[turnNew], senses[senseNew])]*record
        if done: return

#...............................................................Looping Section
    
def keyPresses():
    global axes, axesFixed
    keys = pygame.key.get_pressed()
    
    if rotMode: #Checks if it's free rotations
        if keys[pygame.K_KP4] and not keys[pygame.K_KP6]:
            axes = dot(axes, rotY(speed))
        elif keys[pygame.K_KP6] and not keys[pygame.K_KP4]:
            axes = dot(axes, rotY(-speed))
        if keys[pygame.K_KP8] and not keys[pygame.K_KP5]:
            axes = dot(axes, rotX(speed))
        elif keys[pygame.K_KP5] and not keys[pygame.K_KP8]:
            axes = dot(axes, rotX(-speed))
        if keys[pygame.K_KP7] and not keys[pygame.K_KP9]:
            axes = dot(axes, rotZ(-speed))
        elif keys[pygame.K_KP9] and not keys[pygame.K_KP7]:
            axes = dot(axes, rotZ(speed))
        
    else: #If it's a fixed rotation
        if keys[pygame.K_KP4] and not keys[pygame.K_KP6]:
            axesFixed = dot(axesFixed, rotY(speed))
        elif keys[pygame.K_KP6] and not keys[pygame.K_KP4]:
            axesFixed = dot(axesFixed, rotY(-speed))
        if keys[pygame.K_KP8] and not keys[pygame.K_KP5]:
            axes = dot(axes, rotX(speed))
            if axes[1,1] < 0:
                axes = rotX(90)
        elif keys[pygame.K_KP5] and not keys[pygame.K_KP8]:
            axes = dot(axes, rotX(-speed))
            if axes[1,1] < 0:
                axes = rotX(-90)

def eventHandling(moving = False):
    global moves, undo, background, axes, axesFixed, rotMode, done
    global factor, speed, screen, x,y
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            
            if not moving:
                eventMove(event)
            
            if event.key == pygame.K_c:
                background = not background
                
            if event.key == pygame.K_DOWN:
                factor /= factorCoef
            if event.key == pygame.K_UP:
                factor *= factorCoef
            
            if event.key == pygame.K_RIGHT:
                speed *= speedCoef
            if event.key == pygame.K_LEFT:
                speed /= speedCoef
                
            if event.key == pygame.K_m and rotMode: #If it's free
                axes = dot(axes, rotZ( -arctan(axes[1,0]/axes[1,1])/D2R ))
                axes = dot(axes, rotZ( -180 * (axes[1,1] < 0) ))
                cos1, sin1 = axes[1,1], -axes[1,2]
                cos2, sin2 = axes[0,0], -axes[2,0]
                axes = array([[1,0,0],[0,cos1,-sin1],[0,sin1,cos1]])
                axesFixed = array([[cos2,0,sin2],[0,1,0],[-sin2,0,cos2]])
                rotMode = not rotMode

            elif event.key == pygame.K_m and not rotMode: #If it's fixed
                axes = dot(axesFixed, axes)
                axesFixed = eye(3)
                rotMode = not rotMode
                
            if event.key == pygame.K_KP0:
                axes = eye(3)
                axesFixed = eye(3)
            if event.key == pygame.K_ESCAPE:
                done = True
            
        if event.type == pygame.VIDEORESIZE:
            tempFactor = (y/4*(y<=x) + x/4*(x<y))
            x,y = event.size
            screen = pygame.display.set_mode((x,y), pygame.RESIZABLE)
            factor *= (y/4*(y<=x) + x/4*(x<y)) / tempFactor

def eventMove(event):
    global moves, undo
    
    if event.key == pygame.K_s:
        scramble()

    if event.key in moveKeys.keys():
        shift = 2*bool(pygame.key.get_mods() & pygame.KMOD_SHIFT) - 1
        if undo > 0:
            moves = moves[:-undo]
            undo = 0
        moves += [(moveKeys[event.key],-shift)]
        turn(moves[-1][0], moves[-1][1])

    elif event.key == pygame.K_z and undo < len(moves):
        undo += 1
        turn(moves[-undo][0], -moves[-undo][1])
    elif event.key == pygame.K_x and undo > 0:
        turn(moves[-undo][0], moves[-undo][1])
        undo -= 1
    
    if event.key == pygame.K_KP_PERIOD:
        init()
        moves = []
        undo = 0
        
def refresh():
    screen.fill(backColour)
    render(dot(axesFixed, axes))
    pygame.display.flip()
    clock.tick(frameRate)

#..................................................................Main Section

init()
#solvedState = copy(rotIns)

while not done:    
    keyPresses() 
    eventHandling()
    refresh()
    
pygame.quit()
