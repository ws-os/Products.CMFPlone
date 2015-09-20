from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.controlpanel.utils import migrate_to_email_login
from Products.CMFPlone.controlpanel.utils import migrate_from_email_login
from Products.CMFPlone.interfaces import ISecuritySchema
from Products.CMFPlone.interfaces.controlpanel import IExtendedSecuritySchema
from Products.Five.browser import BrowserView
from collections import defaultdict
from plone.app.registry.browser import controlpanel
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.interface import alsoProvides

import logging

logger = logging.getLogger('Products.CMFPlone')


class ContextProxy(object):
    def __init__(self, record_proxy=None, interfaces=None, form=None):
        self.__record_proxy = record_proxy
        self.__form = form
        alsoProvides(self, *interfaces)

    def __getattr__(self, name):
        if name.startswith('__') or name.startswith('_ContextProxy__'):
            return object.__getattr__(self, name)
        if name in self.__record_proxy.__schema__:
            return getattr(self.__record_proxy, name)
        else:
            return getattr(self.__form, name)

    def __setattr__(self, name, value):
        if name.startswith('__') or name.startswith('_ContextProxy__'):
            return object.__setattr__(self, name, value)
        if name in self.__record_proxy.__schema__:
            return setattr(self.__record_proxy, name, value)
        else:
            return setattr(self.__form, name, value)


class RegistryProxyEditForm(controlpanel.RegistryEditForm):
    """Registry edit form that can contain fields that are not part of
    the registry schema.

    This form base class is useful if your form needs to work with fields that
    are not part of the registry. First define a schema with fields that will
    be stored in the registry (see ``RegistryEditForm`` for more information).
    Then define a separate schema with fields which will not be part of
    the registry. This schema should extend the registry schema::

      class IExtendedSettings(IMySettings):
          # define additional non-registry fields here
          extra_field = schema.TextLine(title=u'Extra field')

    Your form class should subclass this form and define the ``schema`` and
    ``extended_schema``class attributes, pointing to the relevant interfaces::

      class MyForm(RegistryProxyEditForm):
          schema = IMySettings
          extended_schema = IExtendedSettings

    To handle the additional fields in the ``IExtendedSettings`` schema,
    you need to define a property on your form class that gets and sets the
    field value (property name has to be the same as the name of the field)::

      class MyForm(RegistryProxyEditForm):
          schema = IMySettings
          extended_schema = IExtendedSettings

          def get_extra_field(self):
              # get the field value from some location other than the registry

          def set_extra_field(self, value):
              # set the field value to some location other than the registry

          extra_field = property(get_extra_field, set_extra_field)
    """
    def getContent(self):
        record_proxy = getUtility(IRegistry).forInterface(
            self.registry_schema,
            prefix=self.schema_prefix
        )
        interfaces = [self.schema]
        return ContextProxy(record_proxy=record_proxy, interfaces=interfaces,
                            form=self)


class SecurityControlPanelForm(RegistryProxyEditForm):
    id = "SecurityControlPanel"
    label = _(u"Security Settings")
    registry_schema = ISecuritySchema
    schema = IExtendedSecuritySchema
    schema_prefix = "plone"

    def get_enable_self_reg(self):
        portal = self.context
        app_perms = portal.rolesOfPermission(
            permission='Add portal member')
        for app_perm in app_perms:
            if app_perm['name'] == 'Anonymous' \
               and app_perm['selected'] == 'SELECTED':
                return True
        return False

    def set_enable_self_reg(self, value):
        portal = self.context
        app_perms = portal.rolesOfPermission(
            permission='Add portal member')
        reg_roles = []

        for app_perm in app_perms:
            if app_perm['selected'] == 'SELECTED':
                reg_roles.append(app_perm['name'])
        if value is True and 'Anonymous' not in reg_roles:
            reg_roles.append('Anonymous')
        if value is False and 'Anonymous' in reg_roles:
            reg_roles.remove('Anonymous')

        portal.manage_permission('Add portal member', roles=reg_roles,
                                 acquire=0)

    enable_self_reg = property(get_enable_self_reg, set_enable_self_reg)


class SecurityControlPanel(controlpanel.ControlPanelFormWrapper):
    form = SecurityControlPanelForm


class EmailLogin(BrowserView):
    """View to help in migrating to or from using email as login.

    We used to change the login name of existing users here, but that
    is now done by checking or unchecking the option in the security
    control panel.  Here you can only search for duplicates.
    """

    duplicates = []

    def __call__(self):
        if self.request.form.get('check_email'):
            self.duplicates = self.check_email()
        elif self.request.form.get('check_userid'):
            self.duplicates = self.check_userid()
        return self.index()

    @property
    def _email_list(self):
        context = aq_inner(self.context)
        pas = getToolByName(context, 'acl_users')
        emails = defaultdict(list)
        orig_transform = pas.login_transform
        try:
            if not orig_transform:
                # Temporarily set this to lower, as that will happen
                # when turning emaillogin on.
                pas.login_transform = 'lower'
            for user in pas.getUsers():
                if user is None:
                    # Created in the ZMI?
                    continue
                email = user.getProperty('email', '')
                if email:
                    email = pas.applyTransform(email)
                else:
                    logger.warn("User %s has no email address.",
                                user.getUserId())
                    # Add the normal login name anyway.
                    email = pas.applyTransform(user.getUserName())
                emails[email].append(user.getUserId())
        finally:
            pas.login_transform = orig_transform
            return emails

    def check_email(self):
        duplicates = []
        for email, userids in self._email_list.items():
            if len(userids) > 1:
                logger.warn("Duplicate accounts for email address %s: %r",
                            email, userids)
                duplicates.append((email, userids))

        return duplicates

    @property
    def _userid_list(self):
        # user ids are unique, but their lowercase version might not
        # be unique.
        context = aq_inner(self.context)
        pas = getToolByName(context, 'acl_users')
        userids = defaultdict(list)
        orig_transform = pas.login_transform
        try:
            if not orig_transform:
                # Temporarily set this to lower, as that will happen
                # when turning emaillogin on.
                pas.login_transform = 'lower'
            for user in pas.getUsers():
                if user is None:
                    continue
                login_name = pas.applyTransform(user.getUserName())
                userids[login_name].append(user.getUserId())
        finally:
            pas.login_transform = orig_transform
            return userids

    def check_userid(self):
        duplicates = []
        for login_name, userids in self._userid_list.items():
            if len(userids) > 1:
                logger.warn("Duplicate accounts for lower case user id "
                            "%s: %r", login_name, userids)
                duplicates.append((login_name, userids))

        return duplicates

    def switch_to_email(self):
        # This is not used and is only here for backwards
        # compatibility.  It avoids a test failure in
        # Products.CMFPlone.
        # XXX: check if this can be removed
        migrate_to_email_login(self.context)

    def switch_to_userid(self):
        # This is not used and is only here for backwards
        # compatibility.  It avoids a test failure in
        # Products.CMFPlone.
        # XXX: check if this can be removed
        migrate_from_email_login(self.context)
