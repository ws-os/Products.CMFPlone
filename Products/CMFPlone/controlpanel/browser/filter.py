# -*- coding: utf-8 -*-
from Products.CMFPlone import PloneMessageFactory as _  # NOQA
from Products.CMFPlone.interfaces import IFilterSchema
# from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
# from plone.z3cform import layout


class FilterControlPanelForm(RegistryEditForm):
    id = "FilterControlPanel"
    label = _(u"Filter settings")
    schema = IFilterSchema
    schema_prefix = "plone"


class FilterControlPanel(ControlPanelFormWrapper):
    form = FilterControlPanelForm
