import numpy as np
import laspy
from .pblib.generate_protobuf import PBPointCloud


def loadLAS(filename, points_only = False, points_classification_only = False, compact = False):
    las = laspy.read(filename)
    pts = las.xyz
    classification = np.array([]).astype(np.uint8)
    intensity = np.array([]).astype(np.uint16)
    returnNumber = np.array([]).astype(np.uint8)
    numberOfReturns = np.array([]).astype(np.uint8)
    if not points_only:
        classification = np.array(las.classification)
    if not(points_only or points_classification_only):
        intensity = np.array(las.intensity)
        returnNumber = np.array(las.return_num)
        numberOfReturns = np.array(las.num_returns)
    print(classification.shape)
    pb = PBPointCloud(pts, classification, intensity, returnNumber, numberOfReturns)
    return pb