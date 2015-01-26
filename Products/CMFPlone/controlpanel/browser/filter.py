# -*- coding: utf-8 -*-
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IFilterSchema
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from z3c.form import button


class FilterControlPanelForm(RegistryEditForm):
    id = "FilterControlPanel"
    label = _(u"Filter settings")
    schema = IFilterSchema
    schema_prefix = "plone"

    def updateActions(self):  # NOQA
        """Have to override this because we only have Save, not Cancel
        """
        super(RegistryEditForm, self).updateActions()
        self.actions['save'].addClass("context")

    @button.buttonAndHandler(_(u"Save"), name='save')
    def handleSave(self, action):  # NOQA
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(
            _(u"Changes saved."),
            "info")
        self.request.response.redirect(self.request.getURL())


class FilterControlPanel(ControlPanelFormWrapper):
    form = FilterControlPanelForm
