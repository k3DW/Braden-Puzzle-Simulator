from numpy import (sqrt, eye, array, pi, cos, sin, tan, repeat, sum,
                    vstack, dot, round_, copy, cross, arange)
from numpy.linalg import norm

def cot(x):
    return 1 / tan(x)
def csc(x):
    return 1 / sin(x)
def sec(x):
    return 1 / cos(x)

def translate(data, vec): #To facilitate translation
    data = array(data)
    for i in [0,1,2]:
        if len(data.shape)==1:
            data[i] += vec[i]
        elif len(data.shape)==2:
            data[:,i] += vec[i]
    return copy(data)
    
def arbiRot(vec):
    """This function takes in any vector 'vec' and returns a function which
    returns a matrix that rotates space about 'vec' by an arbitrary angle.
    This function assumes a right-handed coordinate system."""
    a,b,c = vec #breaking up 'vec' into its components
    d = sqrt(b**2 + c**2) #the 2D diagonal
    p = sqrt(a**2 + d**2) #the 3D diagonal
    
    rx, rx1 = eye(3), eye(3) #Initializing the x rotations
    ry = array([[d/p, 0, a/p], [0, 1, 0], [-a/p, 0, d/p]])
    ry1 = array([[d/p, 0, -a/p], [0, 1, 0], [a/p, 0, d/p]])
    
    if d != 0: #This is here because the function returns NAN for [1,0,0]
        rx = array([[1, 0, 0], [0, c/d, b/d], [0, -b/d, c/d]])
        rx1 = array([[1, 0, 0], [0, c/d, -b/d], [0, b/d, c/d]])
    
    def arbiRotMat(t):
        """This function takes in an angle 't' in radians and outputs
        a matrix that rotates space about the predetermined 'vec' by 't'."""
        t *= pi/180
        rz = array([[cos(t), -sin(t), 0], [sin(t), cos(t), 0], [0, 0, 1]])
        
        totalMat = eye(3) #Initialize as identity
        for mat in [rx,ry,rz,ry1,rx1]:      # This loops through the individual
            totalMat = dot(totalMat, mat)   # matrices and combines them.
        totalMat = round_(totalMat, 12)+0 #Removing the floating point error
    
        return totalMat
    return arbiRotMat
    
def centroid(data):
    """This function takes in a polygon, defined by its points,
    and returns the location of its centroid. It assumes that all the
    points are coplanar, and will spit out a meaningless answer if not."""
    p1, p2, p3 = array([data[0]]), data[1:-1], data[2:] #p1 is the first point
    p1 = repeat(p1, len(p2), axis=0) #p2 and p3 are the other points
    centroids = copy(p1+p2+p3)/3 #The centroids of the individual triangles
    
    a = norm(p2-p1, axis=1)
    b = norm(p3-p1, axis=1) #2nd sides
    c = norm(p3-p2, axis=1) #3rd sides
    p = copy(a+b+c)/2 #A construction in Heron's area formula
    areas = copy(sqrt(p*(p-a)*(p-b)*(p-c))) #The areas of the triangles

    v1 = copy(p2-p1) / vstack(a) #1st unit vectors (side a)
    v2 = copy(p3-p1) / vstack(b)

    crossed = cross(v1,v2) #The cross of the unit vectors, to find direction
    lookAt = 0 #0 is x, 1 is y, 2 is z
    while abs(crossed[0,lookAt]) < 1e-8: #This checks if any of the unit
        lookAt += 1                      #vectors have a component of zero
    
    signs = crossed[ : , lookAt]    #The signs (directions) of the triangles
    signs = copy(signs)/ abs(signs)
    areas *= signs #Signing the areas
    return round_(sum(centroids*vstack(areas),axis=0)/sum(areas)+0,10)
    
def offset(data, amount):
    """This function takes in a polygon, defined by its points, and
    returns a new polygon that has been offset inwards by the amount given."""
    i1 = arange(len(data))
    i2, i3 = (i1 + 1) % len(i1) , (i1 - 1) % len(i1)
    
    p1, p2, p3 = copy(data[i1]), copy(data[i2]), copy(data[i3])
    v1 = copy(p2-p1)/vstack(norm(copy(p2-p1), axis=1))
    v2 = copy(p3-p1)/vstack(norm(copy(p3-p1), axis=1))
    
    lengths = amount / sqrt( (1/2) * (1 - sum(copy(v1*v2), axis = 1)))
    directions = (v1+v2)/vstack(norm(v1+v2, axis=1))
    offsets = vstack(lengths) * directions
    return data + offsets

def transform(data, inst):
    #Takes in the data and the instructions, and executes them.
    if type(inst[0]) in [int,float]:
        return translate(data, inst)
    
    while len(inst) > 0:
        if type(inst[0]) == tuple:
            if type(inst[0][0]) in [int,float]:
                data = translate(data, inst[0])
                inst = inst[1:]
            elif type(inst[0][0]) == list:
                data = dot( data, arbiRot(inst[0][0])(-inst[0][1]))
                inst = inst[1:]
        elif type(inst[0]) == list:
            data = dot( data, arbiRot(inst[0])(-inst[1]))
            inst = inst[2:]
    return data
    
a = array([[-3,3,3],[-1,3,1],[-1,1,3]])
rotX = arbiRot([1,0,0])
rotY = arbiRot([0,1,0])
rotZ = arbiRot([0,0,1])