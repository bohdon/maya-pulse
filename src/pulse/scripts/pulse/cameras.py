
import pymel.core as pm

__all__ = [
    'saveCameras',
    'restoreCameras',
]


CAM_NAMES = [
    'perspShape',
    'topShape',
    'frontShape',
    'sideShape',
]
CAM_SETTINGS = {}


def saveCameras():
    """
    Save default camera positions in the current scene
    so that they can be maintained when travelling between
    scenes.
    """
    for camName in CAM_NAMES:
        if not pm.objExists(camName):
            continue
        cam = pm.PyNode(camName)
        CAM_SETTINGS[camName] = _getCameraSettings(cam)

def restoreCameras():
    """
    Restore the default cameras to the last saved position
    """
    for camName in CAM_NAMES:
        if not pm.objExists(camName) or not camName in CAM_SETTINGS:
            continue
        cam = pm.PyNode(camName)
        _setCameraSettings(cam, CAM_SETTINGS[camName])

def _getCameraSettings(cam):
    transform = cam.getParent()
    t = transform.t.get()
    r = transform.r.get()
    s = transform.s.get()
    focalLength = cam.focalLength.get()
    coi = cam.coi.get()
    return [t, r, s, focalLength, coi]

def _setCameraSettings(cam, settings):
    t, r, s, focalLength, coi = settings
    transform = cam.getParent()
    transform.t.set(t)
    transform.r.set(r)
    transform.s.set(s)
    cam.focalLength.set(focalLength)
    cam.coi.set(coi)
