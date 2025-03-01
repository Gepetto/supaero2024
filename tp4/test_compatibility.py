from compatibility import P3X
import unittest
import pinocchio as pin
import hppfcl
import numpy as np
from numpy.linalg import norm



### TEST ZONE ############################################################
### This last part is to automatically validate the versions of this example.

from compatibility import _getConstraintJacobian6d,_getConstraintJacobian3d,_getConstraintsJacobian

class TestJconstraint(unittest.TestCase):
    def test_j6d(self):
        pass

from tp4.scenes import buildSceneThreeBodies
model,gmodel = buildSceneThreeBodies()
data = model.createData()
cmodel6 = pin.RigidConstraintModel(pin.ContactType.CONTACT_6D,model,
                                  1,pin.SE3.Random(),
                                  2,pin.SE3.Random(),pin.LOCAL)
cdata6 = cmodel6.createData()
q = pin.randomConfiguration(model)
pin.computeJointJacobians(model,data,q)
Ji = _getConstraintJacobian6d(model,data,cmodel6,cdata6)
if P3X:
    Je = pin.getConstraintJacobian(model,data,cmodel6,cdata6)
    assert( np.allclose(Je,Ji) )

cmodel3 = pin.RigidConstraintModel(pin.ContactType.CONTACT_3D,model,
                                  1,pin.SE3.Random(),
                                  2,pin.SE3.Random(),pin.LOCAL)
cdata3 = cmodel3.createData()
Ji = _getConstraintJacobian3d(model,data,cmodel3,cdata3)
if P3X:
    Je = pin.getConstraintJacobian(model,data,cmodel3,cdata3)
    assert( np.allclose(Je,Ji) )

Ji = _getConstraintsJacobian(model,data,[cmodel3,cmodel6],[cdata3,cdata6])
if P3X:
    Je = pin.getConstraintsJacobian(model,data,[cmodel3,cmodel6],[cdata3,cdata6])
    assert( np.allclose(Je,Ji) )

### TEST ZONE ############################################################
