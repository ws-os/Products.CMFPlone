# -*- coding: utf-8 -*-
from Products.PluggableAuthService.interfaces import plugins
from Products.PlonePAS.interfaces import group
from zope.interface import Interface


class IGroupTool(plugins.IGroupIntrospection,
                 group.IGroupManagement,
                 plugins.IGroupsPlugin):

    """
    Defines an interface for managing and introspecting and
    groups and group membership.
    """

class IGroupDataTool(Interface):

    def wrapGroup(group):
        """
        decorate a group with property management capabilities if needed
        """
