import logging

import pymel.core as pm

LOG = logging.getLogger(__name__)


def import_all_references(load_unloaded=True, depth_limit=10, remove_namespace=False, prompt=False):
    """
    Recursively import all references in the scene

    Args:
        load_unloaded: A bool, whether to load currently unloaded references before importing
        depth_limit: An int, recursion depth limit when handling recursive references
        remove_namespace: A bool, whether to remove reference namespaces when importing
        prompt: A bool, whether to prompt the user to confirm the operation before running
    """
    if prompt and not import_all_references_confirm():
        return False

    def import_references(refs, depth):
        if depth > depth_limit:
            return

        for ref in refs:

            if not ref.isLoaded():
                if load_unloaded:
                    LOG.debug("Loading %s", ref)
                    ref.load(loadReferenceDepth='all')
                else:
                    continue

            # Store the list of sub-references
            sub_refs = ref.subReferences()

            path = ref.path
            try:
                LOG.debug("Importing %s", ref)
                ref.importContents(removeNamespace=remove_namespace)
            except RuntimeError as e:
                LOG.warning('Could not import reference: %s\n%s', path, e)

            # Import any subrefs
            if len(sub_refs):
                LOG.debug("Loading %d Sub-Reference(s)", len(sub_refs))
                import_references(sub_refs.values(), depth + 1)

    refs = get_top_level_references()
    if not refs:
        LOG.debug("No References to import")
        return True

    LOG.debug("Importing %s Top-Level Reference(s)", len(refs))
    import_references(refs, 1)

    # cleanup
    bad = get_bad_references()
    if len(bad):
        try:
            bad_list = [str(b) for b in bad]
            pm.delete(bad)
            LOG.debug('Deleted bad references: %s', bad_list)
        except Exception as e:
            LOG.error('Could not delete bad references: %s', bad)

    return True


def import_all_references_confirm():
    confirm_kw = {
        't': 'Import All References',
        'm': 'This action is not undoable.\nContinue?',
        'b': ['OK', 'Cancel'],
        'cb': 'Cancel',
        'ds': 'dismiss',
        'icn': 'warning',
    }
    result = pm.confirmDialog(**confirm_kw)
    if result != 'OK':
        return False
    return True


def get_bad_references():
    refs = pm.ls(rf=True)
    return [r for r in refs if r.referenceFile() is None]


def get_file_references():
    """
    Return a list of the referenced files in the current scene
    """
    ref_nodes = pm.ls(rf=True)
    file_refs = [r.referenceFile() for r in ref_nodes]
    return file_refs


def get_top_level_references():
    refs = get_file_references()
    return [r for r in refs if is_top_level_reference(r)]


def is_top_level_reference(ref):
    """
    Return True if the given file reference's parent is the scene

    Args:
        ref: A reference node
    """
    if ref is None:
        return False
    return pm.referenceQuery(ref, rfn=True, tr=True) == ref.refNode
