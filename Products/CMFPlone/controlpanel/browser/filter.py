# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _  # NOQA
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
        # Save in portal tools
        safe_html = getattr(
            getToolByName(self.context, 'portal_transforms'),
            'safe_html',
            None)
        disable_filtering = int(data['disable_filtering'])
        if disable_filtering != safe_html._config['disable_transform']:
            safe_html._config['disable_transform'] = disable_filtering
            safe_html._p_changed = True
            safe_html.reload()

        # Proceed to registry storage
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
