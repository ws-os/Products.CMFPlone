import json
import logging
import smtplib

from zope import component
from zope.component import hooks

from Acquisition import aq_inner
import zExceptions

from Products.CMFCore import interfaces as cmf_ifaces
from Products.CMFCore.utils import getToolByName

from plone import protect
from plone.app.controlpanel import usergroups
from Products.CMFPlone import PloneMessageFactory as _

logger = logging.getLogger('Products.CMFPlone.controlpanel')


class UsersControlPanelView(usergroups.UsersGroupsControlPanelView):
    """
    Render the Users Control Panel structure mockup pattern based listing.
    """

    def __call__(self):
        """
        Render the Users Control Panel structure mockup pattern based listing.
        """
        form = self.request.form
        findAll = form.get('form.button.FindAll', None) is not None
        self.searchString = not findAll and form.get('searchstring', '') or ''

        site = hooks.getSite()
        base_url = site.absolute_url()
        base_vocabulary = '%s/@@getVocabulary?name=' % base_url
        options = {
            'vocabularyUrl': '%splone.app.vocabularies.Users' % (
                base_vocabulary),
            'buttonGroups': {
                'primary': [
                    {'title': 'Delete',
                     'url': '/delete',
                     'context': 'danger',
                     'icon': 'trash'},
                    {'title': 'Deactivate',
                     'url': '/deactivate'},
                    {'title': 'Activate',
                     'context': 'default',
                     'url': '/activate',
                     'icon': ''},
                ],
                'secondary': [
                    {'title': 'Add To Group',
                     'url': '/add-to-group'},
                    {'title': 'Add Roles',
                     'url': '/add-roles'}
                ]},
            'activeColumns': [
                'fullName',
                'email',
                'dateJoined',
                'userRoles'
            ],
            'availableColumns': {
                'fullName': 'Full Name',
                'email': 'Email',
                'dateJoined': 'Date Joined',
                'dateLastActivity': 'Date of Last Activity',
                'dateLastLogin': 'Date of Last Login',
                'userRoles': 'Roles',
                'hasConfirmed': 'Confirmed',
                'loginEnabled': 'Can Log in'
            },
            'cookieSettingPrefix': '_u_'
        }
        self.options = json.dumps(options)
        return super(UsersControlPanelView, self).__call__()


class UsersControlPanel(usergroups.UsersGroupsControlPanelView):

    mailhost_tool = None

    def __call__(self):
        submitted = form.get('form.submitted', False)
        search = form.get('form.button.Search', None) is not None
        self.searchResults = []
        self.newSearch = False

        if search or findAll:
            self.newSearch = True

        if submitted:
            if form.get('form.button.Modify', None) is not None:
                self.manageUser(form.get('users', None),
                                form.get('resetpassword', []),
                                form.get('delete', []))

        # Only search for all ('') if the many_users flag is not set.
        self.searchString = searchString
        if not(self.many_users) or bool(self.searchString):
            self.searchResults = self.doSearch(self.searchString)

        return self.index()

    def get_mailhost(self):
        if self.mailhost_tool is None:
            self.mailhost_tool = getToolByName(self, 'MailHost')
        return self.mailhost_tool

    def manageUser(self, users=None, resetpassword=None, delete=None):
        if users is None:
            users = []
        if resetpassword is None:
            resetpassword = []
        if delete is None:
            delete = []

        protect.CheckAuthenticator(self.request)

        if users:
            context = aq_inner(self.context)
            acl_users = getToolByName(context, 'acl_users')
            regtool = getToolByName(context, 'portal_registration')
            groups_tool = getToolByName(self, 'portal_groups')

            utils = getToolByName(context, 'plone_utils')

            users_with_reset_passwords = []
            users_failed_reset_passwords = []

            for user in users:
                # Don't bother if the user will be deleted anyway
                if user.id in delete:
                    continue

                member = mtool.getMemberById(user.id)
                current_roles = member.getRoles()

                # TODO: is it still possible to change the e-mail address here?
                #       isn't that done on @@user-information now?
                # If email address was changed, set the new one
                if hasattr(user, 'email'):
                    # If the email field was disabled (ie: non-writeable), the
                    # property might not exist.
                    if user.email != member.getProperty('email'):
                        utils.setMemberProperties(
                            member, REQUEST=context.REQUEST, email=user.email)
                        utils.addPortalMessage(_(u'Changes applied.'))

                # If reset password has been checked email user a new password
                pw = None
                if hasattr(user, 'resetpassword'):
                    if 'Manager' in current_roles and not self.is_zope_manager:
                        raise zExceptions.Forbidden
                    if not context.unrestrictedTraverse(
                            '@@overview-controlpanel').mailhost_warning():
                        pw = regtool.generatePassword()
                    else:
                        utils.addPortalMessage(
                            _(u'No mailhost defined. '
                              'Unable to reset passwords.'),
                            type='error')

                roles = user.get('roles', [])
                if not self.is_zope_manager:
                    # don't allow adding or removing the Manager role
                    # add check if user is in Administrators group
                    grouproles = []
                    for group in groups_tool.getGroupsByUserId(member.id):
                        grouproles.extend(group.getRoles())
                    if ('Manager' in roles or 'Manager' in grouproles) != (
                            'Manager' in current_roles):
                        raise zExceptions.Forbidden

                # Ideally, we would like to detect if any role assignment has
                # actually changed, and only then issue "Changes applied".
                acl_users.userFolderEditUser(
                    user.id, pw, roles, member.getDomains(),
                    REQUEST=context.REQUEST)

                if pw:
                    context.REQUEST.form['new_password'] = pw
                    # [Comment copied from
                    # plone.app.contentrules.actions.mail.MailActionExecutor.__call__()]
                    # XXX: We're using "immediate=True" because otherwise we
                    # won't be able to catch SMTPException as the smtp
                    # connection is made as part of the transaction apparatus.
                    # AlecM thinks this wouldn't be a problem if mail queuing
                    # was always on -- but it isn't. (stevem)
                    # so we test if queue is not on to set immediate
                    immediate = not self.get_mailhost().smtp_queue
                    try:
                        regtool.mailPassword(
                            user.id, context.REQUEST, immediate=immediate)
                    except smtplib.SMTPException as e:
                        logger.exception(e)
                        users_failed_reset_passwords.append(user.id)
                    else:
                        users_with_reset_passwords.append(user.id)

            if delete:
                self.deleteMembers(delete)

            if users_with_reset_passwords:
                reset_passwords_message = _(
                    u"reset_passwords_msg",
                    default=
                    u"The following users have been sent an e-mail with link "
                    u"to reset their password: ${user_ids}",
                    mapping={
                        u"user_ids": ', '.join(users_with_reset_passwords),
                        },
                    )
                utils.addPortalMessage(reset_passwords_message)
            if users_failed_reset_passwords:
                failed_passwords_message = _(
                    u'failed_passwords_msg',
                    default=
                    u'A password reset e-mail could not be sent to the '
                    u'following users: ${user_ids}',
                    mapping={
                        u'user_ids': ', '.join(users_failed_reset_passwords),
                        },
                    )
                utils.addPortalMessage(failed_passwords_message, type='error')

            # TODO: issue message only if something actually has changed
            utils.addPortalMessage(_(u'Changes applied.'))

    def deleteMembers(self, member_ids):
        # this method exists to bypass the 'Manage Users' permission check
        # in the CMF member tool's version
        context = aq_inner(self.context)
        mtool = getToolByName(self.context, 'portal_membership')

        # Delete members in acl_users.
        acl_users = context.acl_users
        if isinstance(member_ids, basestring):
            member_ids = (member_ids,)
        member_ids = list(member_ids)
        for member_id in member_ids[:]:
            member = mtool.getMemberById(member_id)
            if member is None:
                member_ids.remove(member_id)
            else:
                if not member.canDelete():
                    raise zExceptions.Forbidden
                if 'Manager' in member.getRoles() and not self.is_zope_manager:
                    raise zExceptions.Forbidden
        try:
            acl_users.userFolderDelUsers(member_ids)
        except (AttributeError, NotImplementedError):
            raise NotImplementedError(
                'The underlying User Folder '
                'doesn\'t support deleting members.')

        # Delete member data in portal_memberdata.
        mdtool = getToolByName(context, 'portal_memberdata', None)
        if mdtool is not None:
            for member_id in member_ids:
                mdtool.deleteMemberData(member_id)

        # Delete members' local roles.
        mtool.deleteLocalRoles(
            component.getUtility(cmf_ifaces.ISiteRoot),
            member_ids, reindex=1, recursive=1)
