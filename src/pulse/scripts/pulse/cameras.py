import pymel.core as pm

CAM_NAMES = [
    "perspShape",
    "topShape",
    "frontShape",
    "sideShape",
]

CAM_SETTINGS = {}


def save_cameras():
    """
    Save default camera positions in the current scene
    so that they can be maintained when travelling between
    scenes.
    """
    for camName in CAM_NAMES:
        if not pm.objExists(camName):
            continue
        cam: pm.nt.Camera = pm.PyNode(camName)
        CAM_SETTINGS[camName] = _get_camera_settings(cam)


def restore_cameras():
    """
    Restore the default cameras to the last saved position
    """
    for camName in CAM_NAMES:
        if not pm.objExists(camName) or camName not in CAM_SETTINGS:
            continue
        cam: pm.nt.Camera = pm.PyNode(camName)
        _set_camera_settings(cam, CAM_SETTINGS[camName])


def _get_camera_settings(cam):
    transform = cam.getParent()
    t = transform.t.get()
    r = transform.r.get()
    s = transform.s.get()
    focal_length = cam.focalLength.get()
    coi = cam.coi.get()
    return [t, r, s, focal_length, coi]


def _set_camera_settings(cam, settings):
    t, r, s, focal_length, coi = settings
    transform = cam.getParent()
    transform.t.set(t)
    transform.r.set(r)
    transform.s.set(s)
    cam.focalLength.set(focal_length)
    cam.coi.set(coi)
