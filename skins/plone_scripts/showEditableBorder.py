##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=template_id=None
##title=returns whether or not current template displays *editable* border
##
""" assumes the object has a edit property """

REQUEST=context.REQUEST
actions=REQUEST.get('filtered_actions', container.portal_actions.listFilteredActionsFor(context))

if template_id is None:
    template_id=REQUEST['PUBLISHED'].getId()

if ( getattr(context, 'isPortalContent', 0) and \
     'edit' in [ o.get('id', '') for o in actions.get('object', ()) ] ) or \
     'edit' in [ f.get('id', '') for f in actions.get('folder', ()) ] :
   
    if ( getattr(context, 'isPortalContent', 0) and \
         template_id in [ o.get('action', '') for o in actions.get('object', ()) ] ) or \
         template_id in [ f.get('action', '') for f in actions.get('folder', ()) ] or \
         template_id in ['folder_contents', 'folder_listing'] :
        return 1

return 0
