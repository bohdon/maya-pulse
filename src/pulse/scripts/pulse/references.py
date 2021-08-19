import logging

import pymel.core as pm

LOG = logging.getLogger(__name__)


def importAllReferences(loadUnloaded=True, depthLimit=10, removeNamespace=False, prompt=False):
    """
    Recursively import all references in the scene

    Args:
        loadUnloaded: A bool, whether to load currently unloaded references before importing
        depthLimit: An int, recursion depth limit when handling recursive references
        removeNamespace: A bool, whether to remove reference namespaces when importing
        prompt: A bool, whether to prompt the user to confirm the operation before running
    """
    if prompt and not importAllReferencesConfirm():
        return False


    def importReferences(refs, depth):
        if depth > depthLimit:
            return
        
        for ref in refs:

            if not ref.isLoaded():
                if loadUnloaded:
                    LOG.debug("Loading {0}".format(ref))
                    ref.load(loadReferenceDepth='all')
                else:
                    continue

            # Store the list of sub-references
            subRefs = ref.subReferences()

            path = ref.path
            try:
                LOG.debug("Importing {0}".format(ref))
                ref.importContents(removeNamespace=removeNamespace)
            except RuntimeError as e:
                LOG.warning('Could not import reference: {0}\n{1}'.format(path, e))

            # Import any subrefs
            if len(subRefs):
                LOG.debug("Loading {0} Sub-Reference(s)".format(len(subRefs)))
                importReferences(subRefs.values(), depth+1)

    i = 0
    refs = getTopLevelReferences()
    if not refs:
        LOG.debug("No References to import")
        return True

    LOG.debug("Importing {0} Top-Level Reference(s)".format(len(refs)))
    importReferences(refs, 1)

    # cleanup
    bad = getBadReferences()
    if len(bad):
        try:
            badlist = [str(b) for b in bad]
            pm.delete(bad)
            LOG.debug('Deleted bad references: {0}'.format(badlist))
        except Exception as e:
            LOG.error('Could not delete bad references: {0}'.format(bad))
    
    return True

def importAllReferencesConfirm():
    confirmKw = {
        't':'Import All References',
        'm':'This action is not undoable.\nContinue?',
        'b':['OK', 'Cancel'],
        'cb':'Cancel',
        'ds':'dismiss',
        'icn':'warning',
    }
    result = pm.confirmDialog(**confirmKw)
    if result != 'OK':
        return False
    return True

def getBadReferences():
    refs = pm.ls(rf=True)
    return [r for r in refs if r.referenceFile() is None]

def getFileReferences():
    """
    Return a list of the referenced files in the current scene
    """
    refNodes = pm.ls(rf=True)
    fileRefs = [r.referenceFile() for r in refNodes]
    return fileRefs

def getTopLevelReferences():
    refs = getFileReferences()
    return [r for r in refs if isTopLevelReference(r)]

def isTopLevelReference(ref):
    """
    Return True if the given file reference's parent is the scene

    Args:
        ref: A reference node
    """
    if ref is None:
        return False
    return pm.referenceQuery(ref, rfn=True, tr=True) == ref.refNode

