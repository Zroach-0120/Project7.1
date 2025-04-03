from direct.showbase.ShowBase import ShowBase
import math, sys, random
import DefensePaths as defensePaths
import SpaceJamClasses as SpaceJamClasses
from panda3d.core import Vec3, CollisionTraverser, CollisionHandlerPusher
from Player import Spaceship
from SpaceJamClasses import Missile, Alien, Orbiter
from direct.task import Task

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.rootAssetFolder = "Assets"
        
        self.SetupScene()
        self.taskMgr.add(self.SpawnDronesTask, "SpawnDronesTask")
        
        self.Hero = Spaceship(self.loader, self.accept, "Assets/Spaceships/spacejet.3ds", self.render, 'Hero', 
                             "Assets/Spaceships/spacejet_C.png", Vec3(900, 200, -58), Vec3(58, 58, 58), self.taskMgr, self.camera)
        
        self.Hero.SetKeyBindings()
        
        
        
        self.taskMgr.add(self.UpdateCamera, "update-camera")
        
        # Collision setup
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        self.pusher.addCollider(self.Hero.collisionNode, self.Hero.modelNode)
        self.cTrav.addCollider(self.Hero.collisionNode, self.pusher)
        self.cTrav.showCollisions(self.render)

        # Camera settings
        #self.freeCamera = False
        #self.cameraMode = "third_person"
    
        self.planet3 = self.render.find("**/planet3")  

        if not self.planet3.isEmpty():
            print("Planet3 found, spawning alien.")
            self.alien = Alien(self.loader, "Assets/Spaceships/spacejet.3ds", self.render, "Alien",
                               "./Assets/Spaceships/redufo.png", 2, self.planet3, self.cTrav, self.pusher)
            self.taskMgr.add(self.alien.Update, "UpdateAlien")
        else:
            print("Planet3 not found! Alien cannot orbit.")

        self.accept("missile_collider-into-alien_collider", self.OnMissileHitAlien)

        self.orbiters = []
        # ORBITERS In Progress
        # Cloud Orbiters
        for i in range(2):  
            orbiter = Orbiter(self.loader, self.taskMgr, "./Assets/DroneDefender/DroneDefender.obj",
                              self.render, f"CloudOrbiter{i}", Vec3(2, 2, 2), "./Assets/DroneDefender/Drones.jpg",
                              self.Hero.modelNode, orbitRadius=300, orbitType="Cloud", staringAt=None)
            self.orbiters.append(orbiter)

        # MLB Orbiters
        for i in range(2):
            orbiter = Orbiter(self.loader, self.taskMgr, "./Assets/DroneDefender/DroneDefender.obj",
                              self.render, f"MLBOrbiter{i}", Vec3(3, 3, 3), "./Assets/DroneDefender/Drones.jpg",
                              self.Hero.modelNode, orbitRadius=500, orbitType="MLB", staringAt=None)
            self.orbiters.append(orbiter)

        print(f"Initialized {len(self.orbiters)} orbiters!")




    def UpdateCamera(self, Hero):
        self.camera.reparentTo(self.Hero.modelNode)
        self.camera.setFluidPos(0, -20, 10)  
          
   
    def OnMissileHitAlien(self, collisionEntry):
        print("Missile hit the alien!")
        self.alien.Destroy()

    def SetupScene(self):
        self.Universe = SpaceJamClasses.Universe(self.loader, "./Assets/Universe/Universe.obj", self.render, 'Universe', "Assets/Universe/Universe2.jpg", (0, 0, 0), 18008)
        self.Planet1 = SpaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Planet1', "./Assets/Planets/WaterPlanet2.png", (-6000, -3000, -800), 250, self.taskMgr)
        self.Planet2 = SpaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Planet2', "./Assets/Planets/planet1.png", (0, 6000, 0), 300, self.taskMgr)
        self.Planet3 = SpaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Planet3', "./Assets/Planets/cheeseplanet.png", (500, -5000, 200), 500, self.taskMgr)
        self.Planet4 = SpaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Planet4', "./Assets/Planets/grplanet.png", (300, 6000, 500), 150, self.taskMgr)
        self.Planet5 = SpaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Planet5', "./Assets/Planets/redplanet.png", (700, -2000, 100), 500, self.taskMgr)
        self.Planet6 = SpaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Planet6', "./Assets/Planets/planet3.jpg", (0, -980, -1480), 780, self.taskMgr)
        self.SpaceStation1 = SpaceJamClasses.SpaceStation(
            self.loader, 
            "./Assets/SpaceStation/spaceStation.x", 
            self.render, 
            'SpaceStation1', 
            (1500, 1800, -100),
            40,
            "./Assets/SpaceStation/SpaceStation1_Dif2.png"
        )

    

    def DrawBaseballSeams(self, centralObject, droneName, step, numSeams, radius=1):
        unitVec = defensePaths.BaseballSeams(step, numSeams, B=0.4)
        unitVec.normalize()
        position = unitVec * radius * 250 + centralObject.modelNode.getPos()
        drone = SpaceJamClasses.Drone(self.loader, "./Assets/DroneDefender/DroneDefender.obj", self.render, droneName, 
                                      "./Assets/DroneDefender/octotoad1_auv.png", position, 5)
        drone.modelNode.reparentTo(self.render)

    def DrawCloudDefense(self, centralObject, droneName):
        unitVec = defensePaths.Cloud()
        unitVec.normalize()
        position = unitVec * 500 + centralObject.modelNode.getPos()
        drone = SpaceJamClasses.Drone(self.loader, "./Assets/DroneDefender/DroneDefender.obj", self.render, droneName, 
                                      "./Assets/DroneDefender/octotoad1_auv.png", position, 10)
        drone.modelNode.reparentTo(self.render)
        
    def SpawnDronesTask(self, task):
        if SpaceJamClasses.Drone.droneCount >= 60:
            return task.done
        
        SpaceJamClasses.Drone.droneCount += 1
        nickName = f"Drone{SpaceJamClasses.Drone.droneCount}"
        
        if SpaceJamClasses.Drone.droneCount % 2 == 0:
            self.DrawCloudDefense(self.Planet1, nickName)
        else:
            self.DrawBaseballSeams(self.SpaceStation1, nickName, SpaceJamClasses.Drone.droneCount, 60, 2)
        
        return task.cont

app = MyApp()
app.run()