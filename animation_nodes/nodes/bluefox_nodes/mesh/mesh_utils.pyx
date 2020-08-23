import cython
from libc.math cimport sin, cos, M_PI
from .... data_structures cimport Vector3DList

######################################### simple deform utils #####################################
# adapted from Sverchok:https://github.com/nortikin/sverchok/blob/master/nodes/transforms/deform.py

cdef mapRange(float value, float leftMin, float leftMax, float rightMin, float rightMax):
    cdef float scale = 0
    if leftMin == leftMax:
        return (rightMin + rightMax) / 2.0
    if value <= leftMin:
        return rightMin
    if value >= leftMax:
        return rightMax
    scale = (rightMax - rightMin) / (leftMax - leftMin)
    return rightMin + scale * (value - leftMin)

cdef limit(float minValue, float maxValue, float low, float high):
    if minValue == maxValue:
        return minValue, maxValue
    cdef float delta = maxValue - minValue
    return minValue + low * delta, minValue + high * delta

def twistDeform(Vector3DList vertices, float minValue, float maxValue, float low, float high, float angle):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vertices)
    cdef float z, theta, angleValue, sTheta, cTheta
    cdef Vector3DList outVertices = Vector3DList(length = count)

    minValue, maxValue = limit(minValue, maxValue, low, high)
    angleValue = angle / 2
    for i in range(count):
        z = vertices.data[i].z
        theta = mapRange(z, minValue, maxValue, -angleValue, angleValue)
        sTheta = sin(theta)
        cTheta = cos(theta)
        outVertices.data[i].x = vertices.data[i].x * cTheta - vertices.data[i].y * sTheta
        outVertices.data[i].y = vertices.data[i].x * sTheta + vertices.data[i].y * cTheta
        outVertices.data[i].z = z
    return outVertices

def taperDeform(Vector3DList vertices, float minValue, float maxValue, float low, float high, float factor):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vertices)
    cdef float z, scale, factMin, factMax
    cdef Vector3DList outVertices = Vector3DList(length = count)

    minValue, maxValue = limit(minValue, maxValue, low, high)
    factMin = 1 - factor / 2
    factMax = 1 + factor / 2
    for i in range(count):
        z = vertices.data[i].z
        scale = mapRange(z, minValue, maxValue, factMin, factMax)
        outVertices.data[i].x = vertices.data[i].x * scale
        outVertices.data[i].y = vertices.data[i].y * scale
        outVertices.data[i].z = z
    return outVertices

def bendDeform(Vector3DList vertices, float minValue, float maxValue, float low, float high, float angle):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vertices)
    cdef Vector3DList outVertices = Vector3DList(length = count)
    cdef float x, y, z, delta, rVal, minS, maxS, dx, dy, phi, rho, hl

    if angle == 0:
        return vertices
    else:
        delta = maxValue - minValue
        if delta == 0:
            delta = 0.00001

        minS = minValue
        maxS = maxValue

        if minS != maxS:
            minS = minValue + low * delta
            maxS = minValue + high * delta

        hl = high - low
        if hl == 0:
            hl = 0.00001    

        angle /= hl
        rVal = delta / angle

        for i in range(count):
            x = vertices.data[i].x
            y = vertices.data[i].y
            z = vertices.data[i].z

            dx = 0
            dy = 0

            if x < minS:
                dx = (x - minS) * cos(minS * angle / delta)
                dy = (x - minS) * sin(minS * angle / delta)
                x = minS
            if x > maxS:
                dx = (x - maxS) * cos(maxS * angle / delta)
                dy = (x - maxS) * sin(maxS * angle / delta)
                x = maxS

            phi = (x / delta) * angle - M_PI / 2
            rho = rVal - y

            outVertices.data[i].x = rho * cos(phi) + dx
            outVertices.data[i].y = rho * sin(phi) + rVal + dy
            outVertices.data[i].z = z

    return outVertices 

##########################################################################################################       
