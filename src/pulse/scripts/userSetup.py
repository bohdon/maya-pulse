from maya import cmds

if not cmds.about(batch=True):
    from pymel import mayautils
    import pulse.ui.menu

    mayautils.executeDeferred(pulse.ui.menu.install_main_menu)
