## Script (Python) "link_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=remote_url, id='', title=None, description=None, subject=None
##title=Edit a link
##

new_context = context.portal_factory.doCreate(context, id)
new_context.edit(remote_url=remote_url)
new_context.plone_utils.contentEdit(new_context
                               , id=id
                               , description=description)
return ('success', new_context)