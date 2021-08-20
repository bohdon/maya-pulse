import os

import pymel.core as pm
from maya import cmds

import pulse.joints
import pulse.skins
from pulse.buildItems import BuildAction, BuildActionError


class BindSkinAction(BuildAction):

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
            self.extendRigMetaDataList('renderGeo', self.meshes)
            self.extendRigMetaDataList('bakeNodes', bind_jnts)

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
