import random

import meshcat
import numpy as np
import pinocchio as pin
from pinocchio.visualize import MeshcatVisualizer as PMV

from . import colors


def materialFromColor(color):
    if isinstance(color, meshcat.geometry.MeshPhongMaterial):
        return color
    elif isinstance(color, str):
        material = colors.colormap[color]
    elif isinstance(color, list):
        material = meshcat.geometry.MeshPhongMaterial()
        material.color = colors.rgb2int(*[int(c * 255) for c in color[:3]])
        if len(color) == 3:
            material.transparent = False
        else:
            material.transparent = color[3] < 1
            material.opacity = float(color[3])
    elif color is None:
        material = random.sample(list(colors.colormap), 1)[0]
    else:
        material = colors.black
    return material


class MeshcatVisualizer(PMV):
    def __init__(
    self, robot=None, model=None, collision_model=None, visual_model=None, url="classical"#None
    ):
        if robot is not None:
            super().__init__(robot.model, robot.collision_model, robot.visual_model)
        elif model is not None:
            super().__init__(model, collision_model, visual_model)

        if url is not None:
            if url == "classical":
                url = "tcp://127.0.0.1:6000"
                print(f'*** You asked to start meshcat "classically" in {url}')
                print('*** Did you start meshcat manually (meshcat-server)')
            print("Wrapper tries to connect to server <%s>" % url)
            server = meshcat.Visualizer(zmq_url=url)
        else:
            server = None

        if robot is not None or model is not None:
            self.initViewer(loadModel=True, viewer=server)
        else:
            self.viewer = server if server is not None else meshcat.Visualizer()

    def addSphere(self, name, radius, color):
        material = materialFromColor(color)
        self.viewer[name].set_object(meshcat.geometry.Sphere(radius), material)

    def addLine(self, name, point1, point2, color, linewidth=None):
        material = materialFromColor(color)
        if linewidth is not None:
            # 1 by default set in the constructor of material
            # TODO: this does not seem to have any effect
            material.linewidth=linewidth
        points = np.block([[point1],[point2]]).T.astype(np.float32)
        line = meshcat.geometry.Line(meshcat.geometry.PointsGeometry(points),material)
        self.viewer[name].set_object(line)

    def addCylinder(self, name, length, radius, color=None):
        material = materialFromColor(color)
        self.viewer[name].set_object(
            meshcat.geometry.Cylinder(length, radius), material
        )

    def addBox(self, name, dims, color):
        material = materialFromColor(color)
        self.viewer[name].set_object(meshcat.geometry.Box(dims), material)

    def applyConfiguration(self, name, placement):
        if isinstance(placement, list) or isinstance(placement, tuple):
            placement = np.array(placement)
        if isinstance(placement, pin.SE3):
            R, p = placement.rotation, placement.translation
            T = np.r_[np.c_[R, p], [[0, 0, 0, 1]]]
        elif isinstance(placement, np.ndarray):
            if placement.shape == (7,):  # XYZ-quat
                R = pin.Quaternion(np.reshape(placement[3:], [4, 1])).matrix()
                p = placement[:3]
                T = np.r_[np.c_[R, p], [[0, 0, 0, 1]]]
            elif placement.shape == (4,4):
                T = placement
            else:
                print("Error, np.shape of placement is not accepted")
                return False
        else:
            print("Error format of placement is not accepted")
            return False
        self.viewer[name].set_transform(T)

    def delete(self, name):
        self.viewer[name].delete()

    def __getitem__(self, name):
        return self.viewer[name]


# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# The next part of code is to reproduce the behavior of meshcat in pinocchio
# 3 (version 2.99) inside pinocchio 2 (version 2.7).

def _loadPrimitive(geometry_object):
    '''
    Update the pin loadPrimitive function of Pinocchio2 by a code from 
    pinocchio 2.99.
    '''
    import meshcat.geometry
    import hppfcl

    # Cylinders need to be rotated
    R = np.array([[1.,  0.,  0.,  0.],
                  [0.,  0., -1.,  0.],
                  [0.,  1.,  0.,  0.],
                  [0.,  0.,  0.,  1.]])
    RotatedCylinder = type("RotatedCylinder", (meshcat.geometry.Cylinder,), {"intrinsic_transform": lambda self: R })

    geom = geometry_object.geometry
    if isinstance(geom, hppfcl.Capsule):
        if hasattr(meshcat.geometry, 'TriangularMeshGeometry'):
            obj = pin.visualize.meshcat_visualizer.createCapsule(2. * geom.halfLength, geom.radius)
        else:
            obj = pin.visualize.meshcat_visualizer.RotatedCylinder(2. * geom.halfLength, geom.radius)
    elif isinstance(geom, hppfcl.Cylinder):
        obj = RotatedCylinder(2. * geom.halfLength, geom.radius)
    elif isinstance(geom, hppfcl.Box):
        obj = meshcat.geometry.Box(npToTuple(2. * geom.halfSide))
    elif isinstance(geom, hppfcl.Sphere):
        obj = meshcat.geometry.Sphere(geom.radius)
    elif isinstance(geom, hppfcl.Ellipsoid):
        obj = meshcat.geometry.Ellipsoid(geom.radii)
    elif isinstance(geom, hppfcl.ConvexBase):
        obj = pin.visualize.meshcat_visualizer.loadMesh(geom)
    else:
        msg = "Unsupported geometry type for %s (%s)" % (geometry_object.name, type(geom) )
        warnings.warn(msg, category=UserWarning, stacklevel=2)
        obj = None

    return obj

# Update the pin2 version of loadPrimitive by the pin3 version
pin.visualize.meshcat_visualizer.loadPrimitive = _loadPrimitive

# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
