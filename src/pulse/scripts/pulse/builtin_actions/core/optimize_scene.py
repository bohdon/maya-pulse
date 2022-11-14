import pymel.core as pm

from pulse.core import BuildAction

from . import COLOR, CATEGORY


class OptimizeSceneAction(BuildAction):
    """
    Run scene optimization, deleting unused nodes.

    There is currently no way to control which optimizations are run.
    """

    id = "Pulse.OptimizeScene"
    display_name = "Optimize Scene"
    color = COLOR
    category = CATEGORY

    def run(self):
        pm.mel.source("cleanUpScene")
        pm.mel.cleanUp_EnableProgressReporting(True)
        pm.mel.deleteInvalidNurbs(0)
        pm.mel.deleteUnusedCommon_Multi(
            (
                "stitchSrf",
                "rebuildSurface",
                "insertKnotSurface",
                "avgNurbsSurfacePoints",
            ),
            0,
            "",
        )
        # pm.mel.deleteUnusedInUnusedHierarchy("nurbsCurve", 0, "")
        pm.mel.deleteUnusedLocators()
        pm.mel.deleteUnusedConstraints()
        pm.mel.deleteUnusedPairBlends()
        # pm.mel.deleteUnusedDeformers()
        pm.mel.removeAllUnusedSkinInfs()
        pm.mel.deleteUnusedExpressions()
        # pm.mel.deleteUnusedCommon("groupId", 0, "")
        pm.mel.deleteUnusedCommon("animCurve", 0, "")
        pm.mel.deleteUnusedCommon("snapshot", 1, "")
        pm.mel.deleteUnusedCommon_Multi(
            (
                "unitConversion",
                "timeToUnitConversion",
                "unitToTimeConversion",
            ),
            1,
            "",
        )
        pm.mel.MLdeleteUnused()
        pm.clearCache(allNodes=True)
        # pm.mel.deleteEmptyGroups()
        pm.mel.deleteEmptyLayers("Display")
        pm.mel.deleteEmptyLayers("Render")
        # pm.mel.deleteUnusedSets()
        pm.mel.deleteUnusedCommon("partition", 0, "")
        pm.mel.RNdeleteUnused()
        pm.mel.deleteUnusedBrushes()
        pm.mel.deleteUnknownNodes()
        pm.mel.removeDuplicateShadingNetworks(0)
        pm.mel.userCleanUp_PerformCleanUpScene()
