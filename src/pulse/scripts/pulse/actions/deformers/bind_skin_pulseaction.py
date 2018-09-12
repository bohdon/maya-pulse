
import os
from maya import cmds
import pymel.core as pm

import pulse
import pulse.skins


class BindSkinAction(pulse.BuildAction):

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
            raise pulse.BuildActionError('No meshes found to bind')
        if not len(self.joints):
            raise pulse.BuildActionError('No joints found to bind')

    def run(self):
        bindkwargs = dict(
            toSelectedBones=(self.bindTo == 2),
            toSkeletonAndTransforms=(self.bindTo == 1),
            bindMethod=self.bindMethod,
            dropoffRate=self.dropoffRate,
            maximumInfluences=self.maxInfluences,
            normalizeWeights=self.normalizeWeights,
            obeyMaxInfluences=self.maintainMaxInfuence,
            removeUnusedInfluence=self.removeUnusedInfluences,
            skinMethod=self.skinMethod,
            weightDistribution=self.weightDistribution,
        )
        # TODO: work around bad binding when using toSelectedBones
        jntNames = [j.longName() for j in self.joints]
        for m in self.meshes:
            pm.select(cl=True)
            skin = cmds.skinCluster(m.longName(), jntNames, **bindkwargs)
            pm.rename(skin, '{0}_skcl'.format(m))

        # TODO: support geomBind when using geodesic voxel binding

        if self.isRenderGeo:
            rigData = self.getRigMetaData()
            # add meshes to renderGeo list
            renderGeo = rigData.get('renderGeo', [])
            renderGeo = list(set(renderGeo + self.meshes))
            # add joints to bakedJoints list
            bakeNodes = rigData.get('bakeNodes', [])
            bakeNodes = list(set(bakeNodes + self.joints))

            self.updateRigMetaData({
                'renderGeo': renderGeo,
                'bakeNodes': bakeNodes,
            })


class ApplySkinWeightsAction(pulse.BuildAction):

    def validate(self):
        if not len(self.meshes):
            raise pulse.BuildActionError('No meshes were set')
        if not self.fileName:
            raise pulse.BuildActionError('No filename was set')

    def run(self):
        # get full path
        blueprintPath = str(pm.sceneName())
        if not self.fileName:
            # default to blueprint file name
            filePath = os.path.splitext(blueprintPath)[0] + '.weights'
        else:
            filePath = os.path.join(
                os.path.dirname(blueprintPath), self.fileName)

        skins = [pulse.skins.getSkinFromMesh(m) for m in self.meshes]
        pulse.skins.applySkinWeightsFromFile(filePath, *skins)
