
import pymel.core as pm
import pymetanode as meta

import pulse

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
            omi=self.maintainMaxInfuence,
            dr=self.dropoffRate,
            mi=self.maxInfluences,
            nw=self.normalizeWeights,
            rui=self.removeUnusedInfluences,
            bm=self.bindMethod,
            sm=self.skinMethod,
            wd=self.weightDistribution,
            tsb=True,
        )
        for m in self.meshes:
            skin = pm.cmds.skinCluster(m.longName(), [j.longName() for j in self.joints], **bindkwargs)
            pm.rename(skin, '{0}_skcl'.format(m))
        
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

