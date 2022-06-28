import numpy as np
import laspy
from .pblib.generate_protobuf import PBPointCloud


def loadLAS(filename):
    las = laspy.read(filename)
    pts = las.xyz
    #las.close()
    #pts = np.random.randn(10,3)
    pb = PBPointCloud(pts)
    return pb 
