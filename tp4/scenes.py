import pinocchio as pin
import hppfcl
import numpy as np
import random
from supaero2024.hppfcl_utils import load_hppfcl_convex_from_stl_file
from tp4.compatibility import HPPFCL3X
import unittest

def buildScenePillsBox(nobj=30,wall_size=4.0,seed=0,no_walls=False,one_of_each=False):
    '''
    Create pinocchio models (pin.Model and pin.GeometryModel) for a scene
    composed of a box (6 walls partly transparent) and <nobj> objects of small
    size (capsules, ellipsoid, convex patatoid from STL).
    The scene can be varied by changing the number of objects <nobj>, the size of the
    box <wall_size> and the random seed <seed>.
    If no_walls is True, then don't build the walls.
    If one_of_each is True, then don't randomize the type of the objects.
    '''
    SEED = seed
    NOBJ = nobj
    WORLD_SIZE = 0.45*wall_size

    # Initialize the random generators
    pin.seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)

    model = pin.Model()
    geom_model = pin.GeometryModel()

    # ###
    # ### OBJECT SAMPLING
    # ###
    # Sample objects with the following classes.
    shapes = [
        load_hppfcl_convex_from_stl_file("supaero2024/share/mesh.stl"),
        hppfcl.Ellipsoid(0.05, 0.15, 0.2),
        hppfcl.Capsule(0.1, 0.2)
    ]

    for s in shapes: s.computeLocalAABB()

    # Joint limits
    world_bounds = np.array([ WORLD_SIZE ] * 3 + [ np.inf ] * 4)
        
    if one_of_each:
        shapeSamples = []
        for _ in range((nobj+1)//len(shapes)):
            shapeSamples.extend(shapes)
        shapeSamples = shapeSamples[:nobj]
    else:
        shapeSamples = random.sample(shapes*NOBJ,k=NOBJ)

    for shape in shapeSamples:
        jid = model.addJoint(0,pin.JointModelFreeFlyer(),pin.SE3.Identity(),'obj1',
                             min_config=-world_bounds,max_config=world_bounds,
                             max_velocity=np.ones(6),max_effort=np.ones(6))
        color = np.random.rand(4)
        color[-1] = 1
        # Place the object so that it is centered
        Mcenter = pin.SE3(np.eye(3),-shape.computeCOM())
        geom = pin.GeometryObject( f"{str(type(shape))[22:-2]}_{jid}", jid,
                                   placement=Mcenter,collision_geometry=shape)
            
        geom.meshColor = np.array(color)
        geom_model.addGeometryObject(geom)
        # Add inertia
        volum = shape.computeVolume()
        I = shape.computeMomentofInertia()
        density = 700 # kg/m3 = wood
        model.appendBodyToJoint(jid,
                                pin.Inertia(volum*density, np.zeros(3), I*density),
                                pin.SE3.Identity())

    # Add all pairs
    geom_model.addAllCollisionPairs()

    if not no_walls:
        addBox(geom_model,wall_size)
    
    return model,geom_model

def buildSceneThreeBodies(seed=0,size=1.0):
    '''
    Build a new scenes composed of 3 floating objects.
    This function is a proxy over the more general buildScenePillsBox.
    '''
    return buildScenePillsBox(nobj=3,no_walls=True,seed=seed,
                              one_of_each=True,wall_size=size)


def addFloor(geom_model,altitude=0,addCollisionPairs=True,color=np.array([0.9, 0.6, 0., .20])):
    '''
    Add an infinite horizontal plan to an existing scene.
    '''
    shape = hppfcl.Halfspace( np.array([0,0,1.]),0)
    M = pin.SE3.Identity()
    M.translation[2] = altitude
    floor = pin.GeometryObject("floor", 0, 0, placement=M, collision_geometry=shape)
    floor.meshColor = color
    ifloor = geom_model.addGeometryObject(floor)

    # Collision pairs between all objects and the floor.
    for ig,g in enumerate(geom_model.geometryObjects):
        if g.name != 'floor':
            geom_model.addCollisionPair(pin.CollisionPair(ig,ifloor))
            # geom_model.addCollisionPair(pin.CollisionPair(ifloor,ig))


def addBox(geom_model,wall_size=4.0,color=np.array([1,1,1,0.2]),transparency=None):
    '''
    Add a box composed of 6 transparent walls forming a cube.
    This box is typically though to come outside of a previously defined object set.
    '''
    WALL_SIZE = wall_size
    WALL_THICKNESS = WALL_SIZE*.05
   
    wall_color = color.copy()
    assert(len(wall_color)==4)
    if transparency is not None:
        wall_color[3] = transparency
    
    # X-axis
    M = pin.SE3.Identity()
    M.translation = np.array([-WALL_SIZE-WALL_THICKNESS, 0., 0.])/2
    shape = hppfcl.Box(WALL_THICKNESS, WALL_SIZE, WALL_SIZE)
    geom = pin.GeometryObject( f"wall_X-", 0,0, placement=M, collision_geometry=shape)
    geom.meshColor = np.array(wall_color)
    geom_model.addGeometryObject(geom)


    M = pin.SE3.Identity()
    M.translation = np.array([WALL_SIZE, 0., 0.])/2
    shape = hppfcl.Box(WALL_THICKNESS, WALL_SIZE, WALL_SIZE)
    geom = pin.GeometryObject( f"wall_X+", 0,0, placement=M, collision_geometry=shape)
    geom.meshColor = np.array(wall_color)
    geom_model.addGeometryObject(geom)

    # Y-axis
    M = pin.SE3.Identity()
    M.translation = np.array([0., -WALL_SIZE, 0.])/2
    shape = hppfcl.Box(WALL_SIZE, WALL_THICKNESS, WALL_SIZE)
    geom = pin.GeometryObject( f"wall_Y-", 0,0, placement=M, collision_geometry=shape)
    geom.meshColor = np.array(wall_color)
    geom_model.addGeometryObject(geom)

    M = pin.SE3.Identity()
    M.translation = np.array([0., WALL_SIZE, 0.])/2
    shape = hppfcl.Box(WALL_SIZE, WALL_THICKNESS, WALL_SIZE)
    geom = pin.GeometryObject( f"wall_Y+", 0,0, placement=M, collision_geometry=shape)
    geom.meshColor = np.array(wall_color)
    geom_model.addGeometryObject(geom)

    # Z-axis
    M = pin.SE3.Identity()
    M.translation = np.array([0., 0., -WALL_SIZE])/2
    shape = hppfcl.Box(WALL_SIZE, WALL_SIZE, WALL_THICKNESS)
    geom = pin.GeometryObject( f"wall_Z-", 0,0, placement=M, collision_geometry=shape)
    geom.meshColor = np.array(wall_color)
    geom_model.addGeometryObject(geom)

    M = pin.SE3.Identity()
    M.translation = np.array([0., 0., WALL_SIZE])/2
    shape = hppfcl.Box(WALL_SIZE, WALL_SIZE, WALL_THICKNESS)
    geom = pin.GeometryObject( f"wall_Z+", 0,0, placement=M, collision_geometry=shape)
    geom.meshColor = np.array(wall_color)
    geom_model.addGeometryObject(geom)

    # Remove pairs between walls
    for ig1,g1 in enumerate(geom_model.geometryObjects):
        for ig2,g2 in enumerate(geom_model.geometryObjects):
            # a^b is XOR ( (a and not b) or (b and not a) )
            if ig1 < ig2 and ( ('wall' in g1.name) ^ ('wall' in g2.name) ):
                geom_model.addCollisionPair(pin.CollisionPair(ig1,ig2))


def buildSceneCubes(number_of_cubes,sizes=0.2, masses=1.0,
                    with_corner_collisions = True, with_cube_collisions = False,
                    with_floor=False,
                    corner_insider_the_cube = True):
    """Creates the pinocchio pin.Model and pin.GeometryModel
    of a scene containing cubes. The number of cubes is defines by the length of
    the two lists in argument.
    The cubes can be augmented with 8 small spheres corresponding to the corners.
    In that case, the collisions with the cube geometries are disable, and only the collisions
    between sphere is active.

    Args:

        number_of_cubes: number of cubes (then expect lists of proper sizes)

        sizes: a list containing the lengthes of the cubes. If a single scalar
        is given, then extrapolate it to a list of proper size. Defaults to .2

        masses: a list containing the masses of the cubes. If a single scalar
        is given, then extrapolate it to a list of proper size. Defaults to 1

    option args:

        with_corner_collisions: add balls to the corner of the cube and only enable collision
        checks between these additional balls. True by default.

        with_cube_collisions: add collision pairs between cubes. False by defaults (why?).

        corner_insider_the_cube: added for compatibility with previous code. True by default.

    Returns:
        model, geom_model

    """
    N = number_of_cubes
    if np.isscalar(sizes):  sizes = [ sizes ]*N
    if np.isscalar(masses):  masses = [ masses ]*N
    assert(len(sizes) == len(masses) == N)

    BALL_FACTOR_SIZE = 1/50
    SPHERE_TEMPLATE_NAME = "cube_corner:{n_cube}:{n_sphere}"
    CUBE_TEMPLATE_NAME = "cube:{n_cube}"
    CUBE_COLOR = np.array([0.0, 0.0, 1.0, 0.6])
    SPHERE_COLOR = np.array([1.0, 0.2, 0.2, 1.0])
    WORLD_BOUNDS = np.array([ max(sizes)*5 ] * 3 + [ np.inf ] * 4)

    model = pin.Model()
    geom_model = pin.GeometryModel()

    ball_ids = []
    cube_joints = []
    for n_cube,(size,mass) in enumerate(zip(sizes,masses)):
        # to get random init above the floor
        low = -WORLD_BOUNDS
        low[2] = size*np.sqrt(3)/2
        jointCube = model.addJoint(
            0, pin.JointModelFreeFlyer(), pin.SE3.Identity(), "joint1_" + str(n_cube),
            min_config=low,max_config=WORLD_BOUNDS,
            max_velocity=np.ones(6),max_effort=np.ones(6)
        )
        model.appendBodyToJoint(jointCube,
                                pin.Inertia.FromBox(mass, size,size,size),
                                pin.SE3.Identity())

        # Add cube visual
        shape = hppfcl.Box(size,size,size)
        geom_box = pin.GeometryObject(
            CUBE_TEMPLATE_NAME.format(n_cube=n_cube), jointCube, jointCube,
            placement=pin.SE3.Identity(), collision_geometry=shape
            )

        geom_box.meshColor = CUBE_COLOR
        box_id = geom_model.addGeometryObject(geom_box)  # only for visualisation

        # Add corner collisions
        # For each corner at +size/2 or -size/2 for x y and z, add a small sphere.
        ballSize = size*BALL_FACTOR_SIZE
        shape = hppfcl.Sphere(ballSize)
        M = pin.SE3.Identity()
        # TODO: Order x,y,z temporarily chosen to mimic the initial code.
        # Could be reset to a more classical order to avoid confusion later.
        corners = [ np.array([x,y,z])*(size/2 - (ballSize if corner_insider_the_cube else 0))
                    for x in [1,-1] for z in [-1,1] for y in [-1,1] ]
        for n_sphere,trans in enumerate(corners):
            M.translation = trans
            name = SPHERE_TEMPLATE_NAME.format(n_cube=n_cube,n_sphere=n_sphere)
            geom_ball1 = pin.GeometryObject(name, jointCube, jointCube, placement=M,
                                            collision_geometry=shape)
            geom_ball1.meshColor = SPHERE_COLOR
            ball1_id = geom_model.addGeometryObject(geom_ball1)


    # Collision pairs
    if with_corner_collisions:
        # Add collisions between corners of different cubes
        assert('cube_corner:' in SPHERE_TEMPLATE_NAME)
        for ig1,g1 in enumerate(geom_model.geometryObjects):
            for ig2,g2 in enumerate(geom_model.geometryObjects):
                if not ig1<ig2: continue
                n1 = g1.name.split(':')
                n2 = g2.name.split(':')
                if n1[0] == 'cube_corner' and n2[0] == 'cube_corner':
                    assert(len(n1)==3)
                    assert(len(n2)==3)
                    if n1[1]!=n2[1]:
                        geom_model.addCollisionPair(pin.CollisionPair(ig1,ig2))

    if with_cube_collisions:
        # Add collisions between each cube
        assert('cube:' in CUBE_TEMPLATE_NAME)
        for ig1,g1 in enumerate(geom_model.geometryObjects):
            for ig2,g2 in enumerate(geom_model.geometryObjects):
                if not ig1<ig2: continue
                n1 = g1.name.split(':')
                n2 = g2.name.split(':')
                if n1[0] == 'cube' and n2[0] == 'cube':
                    assert(len(n1)==2)
                    assert(len(n2)==2)
                    assert(n1[1]!=n2[1])
                    geom_model.addCollisionPair(pin.CollisionPair(ig1,ig2))

    if with_cube_collisions and with_corner_collisions:
        # Add collisions between the corners of different cubes
        assert('cube_corner:' in SPHERE_TEMPLATE_NAME)
        assert('cube:' in CUBE_TEMPLATE_NAME)
        for ig1,g1 in enumerate(geom_model.geometryObjects):
            for ig2,g2 in enumerate(geom_model.geometryObjects):
                if not ig1<ig2: continue
                n1 = g1.name.split(':')
                n2 = g2.name.split(':')
                if n1[0] == 'cube' and n2[0] == 'cube_corner':
                    assert(len(n1)==2)
                    assert(len(n2)==3)
                    if n1[1]!=n2[1]:
                        geom_model.addCollisionPair(pin.CollisionPair(ig1,ig2))

    if with_floor:
        addFloor(geom_model,altitude = 0)

        # Remove collision between floor and either cube or cube corners.
        for p in [p.copy() for p in geom_model.collisionPairs]:
            pairName = geom_model.geometryObjects[p.first].name \
                + geom_model.geometryObjects[p.second].name
            if not with_corner_collisions and 'floor' in pairName and 'cube_corner' in pairName:
                geom_model.removeCollisionPair(p)
            if not with_cube_collisions and 'floor' in pairName and 'cube:' in pairName:
                geom_model.removeCollisionPair(p)

    # Reference configuration
    xy = [ (np.random.rand(2)*2-1)*s/4 for s in sizes ]
    z = [ [sum(sizes[:i+1])*1.75] for i in range(len(sizes)) ]
    rot = [ pin.Quaternion(pin.SE3.Random().rotation).coeffs() for _ in sizes ]
    model.referenceConfigurations['default'] = np.concatenate([ np.concatenate(qi)
                                                                for qi in zip(xy,z,rot) ])

    return model, geom_model

                
### TEST ZONE ############################################################
### This last part is to automatically validate the versions of this example.
class MyTest(unittest.TestCase):
    def test_pillsbox(self):
        model,gmodel = buildScenePillsBox(nobj=10)
        assert( isinstance(model,pin.Model) )
    def test_3b(self):
        model,gmodel = buildSceneThreeBodies()
        assert( isinstance(model,pin.Model) )
    def test_cubes(self):
        model,gmodel = buildSceneCubes(3)
        assert( isinstance(model,pin.Model) )
        assert( model.nv==3*6 )
        assert( len(geom_model.geometryObjects) == 3*9 )
        assert( len(geom_model.collisionPairs) == 3*8**2 )
    def test_floor(self):
        model,gmodel = buildSceneThreeBodies()
        addFloor(gmodel,True)
        assert( isinstance(gmodel,pin.GeometryModel) )
        assert( len(gmodel.geometryObjects ) == 4 )
        assert( len(gmodel.collisionPairs ) == 6 )

if __name__ == "__main__":
    from supaero2024.meshcat_viewer_wrapper import MeshcatVisualizer
    import time
    
    model,geom_model = buildScenePillsBox(seed=2,nobj=29,no_walls=True,one_of_each=True)
    viz = MeshcatVisualizer(model=model, collision_model=geom_model,
                            visual_model=geom_model,url="classical")
    
    q = pin.randomConfiguration(model)
    viz.display(q)


    for p in geom_model.collisionPairs:
        i,j=p.first,p.second
        print(geom_model.geometryObjects[i].name,geom_model.geometryObjects[j].name)
