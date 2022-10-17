import os

import pymel.core as pm
from maya import cmds

import pulse.joints
import pulse.skins
from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType


class BindSkinAction(BuildAction):
    id = 'Pulse.BindSkin'
    display_name = 'Bind Skin'
    description = 'Binds a mesh to a joint hierarchy'
    color = (1.0, .85, 0.5)
    category = 'Deformers'

    attr_definitions = [
        dict(name='meshes', type=AttrType.NODE_LIST,
             description="Meshes to bind"),
        dict(name='jointHierarchies', type=AttrType.NODE_LIST, optional=True,
             description="List of joint hierarchies to bind"),
        dict(name='excludeJoints', type=AttrType.NODE_LIST, optional=True,
             description="List of joints to exclude from Joint Hierarchies"),
        dict(name='explicitJoints', type=AttrType.NODE_LIST, optional=True,
             description="List of explicit joints to bind. If Joint Hierarchies is also used, both sets of "
                         "joints will be combined."),
        dict(name='isRenderGeo', type=AttrType.BOOL, value=True,
             description="Whether the bound meshes represent rendered geometry, will affect how joints are "
                         "stored in the rigs meta data."),
        dict(name='bindMethod', type=AttrType.OPTION, value=1,
             options=['Closest Distance', 'Closest in Hierarchy', 'Heat Map', 'Geodesic Voxel'],
             description="Binding algorithm to use."),
        dict(name='skinMethod', type=AttrType.OPTION, value=0,
             options=['Classic Linear', 'Dual Quaternion', 'Weighted Blend'],
             description="List of joints to exclude from Joint Hierarchies"),
        dict(name='normalizeWeights', type=AttrType.OPTION, value=1, options=['None', 'Interactive', 'Post'],
             description="The weight normalization mode to apply."),
        dict(name='weightDistribution', type=AttrType.OPTION, value=1, options=['Distance', 'Neighbors'],
             description="How to redistribute weights when normalizing, such as when painting subtractive values."),
        dict(name='maxInfluences', type=AttrType.INT, value=4, min=1, max=30,
             description="How to redistribute weights when normalizing, such as when painting subtractive values."),
        dict(name='maintainMaxInfuence', type=AttrType.BOOL, value=True),
        dict(name='dropoffRate', type=AttrType.FLOAT, value=4.0, min=0.1, max=10.0),
        dict(name='heatmapFalloff', type=AttrType.FLOAT, value=0.68, min=0.0, max=1.0),
        dict(name='removeUnusedInfluences', type=AttrType.BOOL, value=False),

    ]

    @classmethod
    def util_fromSelection(cls):
        sel = pm.selected()
        meshes = []
        joints = []
        for s in sel:
            sh = s.getShape()
            if sh and sh.nodeType() == 'mesh':
                meshes.append(s)
            elif s.nodeType() == 'joint':
                joints.append(s)
        return BindSkinAction(meshes=meshes, joints=joints)

    def validate(self):
        if not len(self.meshes):
            raise BuildActionError('meshes must have at least one value')
        bind_jnts = self.getBindJoints()
        if not len(bind_jnts):
            raise BuildActionError('no bind joints were set')

    def run(self):
        bind_jnts = self.getBindJoints()

        bindkwargs = dict(
            toSelectedBones=True,
            toSkeletonAndTransforms=False,
            bindMethod=self.bindMethod,
            dropoffRate=self.dropoffRate,
            heatmapFalloff=self.heatmapFalloff,
            maximumInfluences=self.maxInfluences,
            normalizeWeights=self.normalizeWeights,
            obeyMaxInfluences=self.maintainMaxInfuence,
            removeUnusedInfluence=self.removeUnusedInfluences,
            skinMethod=self.skinMethod,
            weightDistribution=self.weightDistribution,
        )

        for mesh in self.meshes:
            pm.select(bind_jnts + [mesh])
            skin = cmds.skinCluster(**bindkwargs)
            pm.rename(skin, '{0}_skcl'.format(mesh))

        # TODO: support geomBind when using geodesic voxel binding

        if self.isRenderGeo:
            self.extend_rig_metadata_list('renderGeo', self.meshes)
            self.extend_rig_metadata_list('bakeNodes', bind_jnts)

    def getBindJoints(self):
        """
        Return the array of joints that should be bound.
        """
        result = set()

        # add hierarchies
        roots = self.jointHierarchies
        for jnt in roots:
            result.add(jnt)
            result.update(jnt.listRelatives(ad=True, typ='joint'))

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


class ApplySkinWeightsAction(BuildAction):
    id = 'Pulse.ApplySkinWeights'
    display_name = 'Apply Skin Weights'
    description = 'Applies data from a .weights file to a skinned mesh'
    color = (1.0, .85, 0.5)
    category = 'Deformers'

    attr_definitions = [
        dict(name='meshes', type=AttrType.NODE_LIST,
             description="The meshes to apply weights to."),
        dict(name='fileName', type=AttrType.STRING,
             description="The name of the .weights file, relative to the blueprint."),
    ]

    def validate(self):
        if not len(self.meshes):
            raise BuildActionError('meshes must have at least one value')
        filePath = self.getWeightsFilePath()
        if not os.path.isfile(filePath):
            raise BuildActionError('file not found: %s' % filePath)

    def run(self):
        filePath = self.getWeightsFilePath()
        skins = self.getSkinClusters()
        pulse.skins.applySkinWeightsFromFile(filePath, *skins)

    def getSkinClusters(self):
        result = []
        for mesh in self.meshes:
            skin = pulse.skins.getSkinFromMesh(mesh)
            if not skin:
                raise BuildActionError(f"No skin cluster found for mesh: {mesh}")
            result.append(skin)
        return result

    def getWeightsFilePath(self):
        blueprintPath = str(pm.sceneName())
        if self.fileName:
            return os.path.join(
                os.path.dirname(blueprintPath), self.fileName).replace('\\', '/')
        else:
            # default to blueprint file name
            return os.path.splitext(blueprintPath)[0] + '.weights'
