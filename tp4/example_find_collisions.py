import hppfcl
import pinocchio as pin
import numpy as np
import time
from supaero2024.meshcat_viewer_wrapper import MeshcatVisualizer
from tp4 import compatibility
from tp4.scenes import buildSceneThreeBodies, buildScenePillsBox, buildSceneCubes

# Build a scene
model,geom_model = buildSceneThreeBodies()
data = model.createData()
geom_data = geom_model.createData()

# Start meshcat
viz = MeshcatVisualizer(model=model, collision_model=geom_model,
                        visual_model=geom_model)

# %jupyter_snippet find
for trial in range(1000):
    q = pin.randomConfiguration(model)
    col = pin.computeCollisions(model,data,geom_model,geom_data,q)
    if col: break
assert(col)
viz.display(q)
# %end_jupyter_snippet

# %jupyter_snippet print
for pairId,c in enumerate(geom_data.collisionResults):
    if len(c.getContacts())>0:
        contact = c.getContact(0)
        print([ n for n in dir(contact) if '__' not in n])
        break
# %end_jupyter_snippet
