import os
from typing import Optional

import pymel.core as pm
from maya import cmds

from pulse import skins
from pulse.core import BuildAction, BuildActionError
from pulse.core import BuildActionAttributeType as AttrType


class BindSkinAction(BuildAction):
    """
    Binds a mesh to a joint hierarchy
    """

    id = "Pulse.BindSkin"
    display_name = "Bind Skin"
    color = (1.0, 0.85, 0.5)
    category = "Deformers"

    attr_definitions = [
        dict(
            name="meshes",
            type=AttrType.NODE_LIST,
            description="Meshes to bind",
        ),
        dict(
            name="jointHierarchies",
            type=AttrType.NODE_LIST,
            optional=True,
            description="List of joint hierarchies to bind",
        ),
        dict(
            name="excludeJoints",
            type=AttrType.NODE_LIST,
            optional=True,
            description="List of joints to exclude from Joint Hierarchies",
        ),
        dict(
            name="explicitJoints",
            type=AttrType.NODE_LIST,
            optional=True,
            description="List of explicit joints to bind. If Joint Hierarchies is also used, both sets of "
            "joints will be combined.",
        ),
        dict(
            name="isRenderGeo",
            type=AttrType.BOOL,
            value=True,
            description="Whether the bound meshes represent rendered geometry, will affect how joints are "
            "stored in the rigs meta data.",
        ),
        dict(
            name="bindMethod",
            type=AttrType.OPTION,
            value=1,
            options=["Closest Distance", "Closest in Hierarchy", "Heat Map", "Geodesic Voxel"],
            description="Binding algorithm to use.",
        ),
        dict(
            name="skinMethod",
            type=AttrType.OPTION,
            value=0,
            options=["Classic Linear", "Dual Quaternion", "Weighted Blend"],
            description="List of joints to exclude from Joint Hierarchies",
        ),
        dict(
            name="normalizeWeights",
            type=AttrType.OPTION,
            value=1,
            options=["None", "Interactive", "Post"],
            description="The weight normalization mode to apply.",
        ),
        dict(
            name="weightDistribution",
            type=AttrType.OPTION,
            value=1,
            options=["Distance", "Neighbors"],
            description="How to redistribute weights when normalizing, such as when painting subtractive values.",
        ),
        dict(
            name="maxInfluences",
            type=AttrType.INT,
            value=4,
            min=1,
            max=30,
            description="How to redistribute weights when normalizing, such as when painting subtractive values.",
        ),
        dict(
            name="maintainMaxInfuence",
            type=AttrType.BOOL,
            value=True,
        ),
        dict(
            name="dropoffRate",
            type=AttrType.FLOAT,
            value=4.0,
            min=0.1,
            max=10.0,
        ),
        dict(
            name="heatmapFalloff",
            type=AttrType.FLOAT,
            value=0.68,
            min=0.0,
            max=1.0,
        ),
        dict(
            name="removeUnusedInfluences",
            type=AttrType.BOOL,
            value=False,
        ),
        dict(
            name="weightsFile",
            type=AttrType.FILE,
            fileFilter="Weights (*.weights)",
            optional=True,
            description="A file containing skin weights to apply when available. "
            "If no weights file exists, the skin method will be used.",
        ),
    ]

    def validate(self):
        bind_jnts = self._get_bind_joints()
        if not len(bind_jnts):
            self.logger.error("No bind joints were set.")
        # if weights file is set, ensure it exists
        if self.weightsFile:
            weights_file_path = self._resolve_file_path(self.weightsFile)
            if not os.path.isfile(weights_file_path):
                self.logger.error(f"Weights file not found: {weights_file_path}")

    def run(self):
        bind_jnts = self._get_bind_joints()
        weights_file_path = self._resolve_file_path(self.weightsFile)

        bind_kwargs = dict(
            maximumInfluences=self.maxInfluences,
            normalizeWeights=self.normalizeWeights,
            obeyMaxInfluences=self.maintainMaxInfuence,
            removeUnusedInfluence=self.removeUnusedInfluences,
            skinMethod=self.skinMethod,
            toSelectedBones=True,
            toSkeletonAndTransforms=False,
            weightDistribution=self.weightDistribution,
        )

        # if weights will be applied afterwards, don't use a bind method
        if not weights_file_path:
            bind_kwargs.update(
                dict(
                    bindMethod=self.bindMethod,
                    dropoffRate=self.dropoffRate,
                    heatmapFalloff=self.heatmapFalloff,
                )
            )

        # create skin clusters
        all_skin_names = []
        for mesh in self.meshes:
            pm.select(bind_jnts + [mesh])
            results = cmds.skinCluster(name=f"{mesh}_skcl", **bind_kwargs)
            all_skin_names.append(results[0])

        # TODO: support geomBind when using geodesic voxel binding

        # mark render and bake geo
        if self.isRenderGeo:
            self.extend_rig_metadata_list("renderGeo", self.meshes)
            self.extend_rig_metadata_list("bakeNodes", bind_jnts)

        # apply skin weights
        if weights_file_path and all_skin_names:
            all_skins = [pm.PyNode(name) for name in all_skin_names]
            skins.apply_skin_weights_from_file(weights_file_path, *all_skins)

    def _get_bind_joints(self):
        """
        Return the array of joints that should be bound.
        """
        result = set()

        # add hierarchies
        roots = self.jointHierarchies
        for jnt in roots:
            result.add(jnt)
            result.update(jnt.listRelatives(allDescendents=True, typ="joint"))

        # remove excluded joints
        exclude = self.excludeJoints
        for jnt in exclude:
            if jnt in result:
                result.remove(jnt)

        # add explicit joints
        explicit = self.explicitJoints
        for jnt in explicit:
            result.add(jnt)

        return list(result)

    def _resolve_file_path(self, file_path) -> Optional[str]:
        """
        Return the full path to the weights file, or None if the file could not be found.
        """
        # TODO: make a util that resolves a relative or absolute path for this common behavior
        if not file_path:
            return file_path
        if os.path.isfile(file_path):
            # path is already absolute
            return file_path
        else:
            # get path relative to the current scene
            scene_path = str(pm.sceneName())
            if scene_path:
                rel_file_path = os.path.join(os.path.dirname(scene_path), file_path).replace("\\", "/")
                if os.path.isfile(rel_file_path):
                    return rel_file_path
        # couldn't find the file
        return file_path
