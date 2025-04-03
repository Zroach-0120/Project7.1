from panda3d.core import NodePath, Vec3, CollisionNode, CollisionSphere, Filename
import random, math
from direct.task import Task
from direct.task.Task import TaskManager
from CollideObjectBase import SphereCollideObject, InverseSphereCollideObject, CollideableObject, CapsuleCollideableObject
import DefensePaths as defensePaths
from CollideObjectBase import PlacedObject
from panda3d.core import CollisionTraverser, CollisionHandlerEvent


class Universe(InverseSphereCollideObject):
    def __init__(self, loader, modelPath, parentNode, nodeName, texPath, posVec, scaleVec):
        super().__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 0.9)
        self.modelNode = loader.loadModel(modelPath)
        self.modelNode.reparentTo(parentNode)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)



class Planet(CollideableObject):
    def __init__(self, loader, modelPath, parentNode, nodeName, texPath, posVec, scaleVec, taskMgr):
        super().__init__(loader, modelPath, parentNode, nodeName)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.collisionNode.node().addSolid(CollisionSphere(0, 0, 0, 1.0 * scaleVec))

        self.taskMgr = taskMgr
        self.rotationSpeed = 1.0  # Initial rotation speed
        self.taskMgr.add(self.Rotate, "planet_rotation")

    def Rotate(self, task):
        self.modelNode.setH(self.modelNode.getH() + self.rotationSpeed)
        return Task.cont

    def ReverseRotation(self):
        self.rotationSpeed *= -1  # Reverse direction

class Drone(CollideableObject):
    droneCount = 0
    dronePool = []

    def __init__(self, loader, modelPath, parentNode, nodeName, texPath, posVec, scaleVec):
        super().__init__(loader, modelPath, parentNode, nodeName)
        
        if Drone.dronePool:
            self.modelNode = Drone.dronePool.pop()
            self.modelNode.reparentTo(parentNode)
            self.collisionNode = self.modelNode.attachNewNode(CollisionNode(nodeName + '_cNode'))
        else:
            self.modelNode = loader.loadModel(modelPath)
            self.modelNode.reparentTo(parentNode)
            self.collisionNode = self.modelNode.attachNewNode(CollisionNode(nodeName + '_cNode'))
        
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        
        Drone.droneCount += 1
        
        # Access the underlying CollisionNode directly
        collision_node = self.collisionNode.node()  # This gets the actual CollisionNode
        
        # Add a collision shape (e.g., a CollisionSphere)
        collision_node.addSolid(CollisionSphere(0, 0, 0, 5))  # Adding collision shape
        
        # Now apply the collision masks directly to the CollisionNode
        collision_node.setFromCollideMask(1)  # Set the collide mask for the node
        collision_node.setIntoCollideMask(1)  # Optionally, set the into collide mask

    @staticmethod
    def return_to_pool(drone):
        if hasattr(drone, 'collisionNode') and drone.collisionNode is not None:
            drone.collisionNode.removeNode()
        Drone.dronePool.append(drone.modelNode)
        drone.modelNode.detachNode()





class SpaceStation(CapsuleCollideableObject):
    def __init__(self, loader, modelPath, parentNode, nodeName, posVec, scaleVec, texPath):
        super().__init__(loader, modelPath, parentNode, nodeName, 1, -1, 5, 1, -1, -5, 10)
        self.modelNode = loader.loadModel(modelPath)
        self.modelNode.reparentTo(parentNode)
        self.modelNode.setPos(Vec3(100, 200, 300))  # Fixed position override issue
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

class Missile(SphereCollideObject):
    fireModels = {}
    cNodes = {}
    collisionSolids = {}
    Intervals = {}
    missileCount = 0

    def __init__(self, loader, modelPath: str, parentNode: NodePath, nodeName: str, posVec: Vec3, scaleVec: float = 1.0):
        super(Missile, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3.0)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setPos(posVec)
        self.reloadTime = .25
        self.missileDistance = 4000
        self.missileBay = 1
        
        Missile.missileCount += 1
        Missile.fireModels[nodeName] =self.modelNode
        Missile.cNodes[nodeName] = self.collisionNode
        Missile.collisionSolids[nodeName] = self.collisionNode.node().getSolid(0)
        Missile.cNodes[nodeName].show()
        print("Fire torpedo #" + str(Missile.missileCount))

    
class Orbiter(SphereCollideObject):
    # Class variables must be declared before they're used.
    numOrbits = 0
    velocity = 0.005
    cloudTimer = 240

    def __init__(self, loader, taskMgr, modelPath: str, parentNode: NodePath, nodeName: str, 
                 scaleVec: Vec3, texPath: str, centralObject, orbitRadius: float, 
                 orbitType: str, staringAt):
        # Initialize the base class with a default collision center and radius.
        super(Orbiter, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3.2)
        
        self.taskMgr = taskMgr
        self.orbitType = orbitType

        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        
        self.orbitObject = centralObject
        self.orbitRadius = orbitRadius
        self.staringAt = staringAt

        # Increment the class variable and store it in the instance (if needed).
        Orbiter.numOrbits += 1
        self.numOrbits = Orbiter.numOrbits

        self.cloudClock = 0
        self.taskFlag = "Traveler-" + str(self.numOrbits)
        
        # Add the orbit task.
        self.taskMgr.add(self.Orbit, self.taskFlag)

    def Orbit(self, task):
        if self.orbitType == "MLB":
            # Calculate the new position using the MLB orbit function.
            positionVec = defensePaths.BaseballSeams(task.time * Orbiter.velocity, self.numOrbits, 2.0)
            newPos = positionVec * self.orbitRadius + self.orbitObject.modelNode.getPos()
            self.modelNode.setPos(newPos)
        elif self.orbitType == "Cloud":
            if self.cloudClock < Orbiter.cloudTimer:
                self.cloudClock += 1
            else:
                self.cloudClock = 0
                positionVec = defensePaths.Cloud()
                newPos = positionVec * self.orbitRadius + self.orbitObject.modelNode.getPos()
                self.modelNode.setPos(newPos)
        
        self.modelNode.lookAt(self.staringAt.modelNode)
        return task.cont

                 
                 
       

class Alien:
    def __init__(self, loader, modelPath, parentNode, nodeName, texPath, scale, planetNode, traverser, handler):
        # Create the alien model
        self.modelNode = loader.loadModel(modelPath)
        self.modelNode.reparentTo(parentNode)
        self.modelNode.setScale(scale)
        self.modelNode.setName(nodeName)

        # Set up the texture
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex)

        # Reference to the planet node
        self.planetNode = planetNode

        # Rotation parameters
        self.orbitRadius = 200  # Distance from planet
        self.orbitSpeed = 0.5  # Speed of rotation (adjust as needed)
        self.angle = 0  # Start angle

        # Collision Setup
        self.traverser = traverser
        self.handler = handler

        self.collisionNode = CollisionNode(nodeName + "_collider")
        self.collisionNode.addSolid(CollisionSphere(0, 0, 0, scale * 1.5))  # Adjust size
        self.collisionNode.setTag("type", "alien")

        self.collisionNodePath = self.modelNode.attachNewNode(self.collisionNode)
        traverser.addCollider(self.collisionNodePath, handler)

        handler.addInPattern("%fn-into")  # Setup collision event pattern

    def Update(self, task):
        # Calculate new position based on circular motion
        self.angle += self.orbitSpeed * task.dt  # Increase angle over time
        x = self.planetNode.getX() + self.orbitRadius * math.cos(self.angle)
        y = self.planetNode.getY() + self.orbitRadius * math.sin(self.angle)
        z = self.planetNode.getZ()  # Keep the alien at the same height

        self.modelNode.setPos(Vec3(x, y, z))

        return task.cont

    def Destroy(self):
        print("Alien destroyed!")
        self.modelNode.removeNode()  # Remove the alien from the scene




def create_drone_circle(centralObject, numDrones, axis='x', radius=1):
    """Creates a formation of drones in a circle around an object."""
    angleStep = 2 * math.pi / numDrones
    
    for i in range(numDrones):
        angle = i * angleStep
        position = Vec3()

        if axis == 'x':
            position.setX(math.cos(angle) * radius)
            position.setY(random.uniform(-0.5, 0.5))
            position.setZ(random.uniform(-0.5, 0.5))
        elif axis == 'y':
            position.setX(random.uniform(-0.5, 0.5))
            position.setY(math.cos(angle) * radius)
            position.setZ(random.uniform(-0.5, 0.5))
        else:
            position.setX(random.uniform(-0.5, 0.5))
            position.setY(random.uniform(-0.5, 0.5))
            position.setZ(math.cos(angle) * radius)
        
        position += centralObject.modelNode.getPos()

        Drone(
            centralObject.loader,
            "./Assets/DroneDefender/DroneDefender.obj",
            centralObject.render,
            f"Drone-{i}",
            "./Assets/DroneDefender/octotoad1_auv.png",
            position,
            5
        )
