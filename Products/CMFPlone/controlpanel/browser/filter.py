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

    def _settransform(self, **kwargs):
        # Cannot pass a dict to set transform parameters, it has
        # to be separate keys and values
        # Also the transform requires all dictionary values to be set
        # at the same time: other values may be present but are not
        # required.
        safe_html = getattr(
            getToolByName(self.context, 'portal_transforms'),
            'safe_html',
            None)
        for k in ('valid_tags', 'nasty_tags'):
            if k not in kwargs:
                kwargs[k] = safe_html.get_parameter_value(k)

        for k in list(kwargs):
            if isinstance(kwargs[k], dict):
                v = kwargs[k]
                kwargs[k + '_key'] = v.keys()
                kwargs[k + '_value'] = [str(s) for s in v.values()]
                del kwargs[k]
        safe_html.set_parameters(**kwargs)
        safe_html._p_changed = True
        safe_html.reload()

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
        nasty_tags = data['nasty_tags']
        if sorted(nasty_tags) != \
                sorted(safe_html._config['nasty_tags'].keys()):
            values = dict.fromkeys(nasty_tags, 1)
            valid = safe_html.get_parameter_value('valid_tags')
            for value in values:
                if value in valid:
                    del valid[value]
            self._settransform(nasty_tags=values, valid_tags=valid)

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
