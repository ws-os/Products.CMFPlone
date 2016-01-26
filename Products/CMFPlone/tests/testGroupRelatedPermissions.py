import pkg_resources
from AccessControl.PermissionRole import rolesForPermissionOn
from Products.CMFPlone.permissions import AddGroups
from Products.CMFPlone.permissions import DeleteGroups
from Products.CMFPlone.permissions import ManageGroups
from Products.CMFPlone.permissions import SetGroupOwnership
from Products.CMFPlone.permissions import ViewGroups
from Products.CMFPlone.tests import PloneTestCase

class TestSiteAdministratorRole(PloneTestCase.PloneTestCase):

    def testManagerPermissions(self):
        errors = []

        for p in (AddGroups, DeleteGroups, ManageGroups, 
                        SetGroupOwnership, ViewGroups):
            if 'Manager' not in rolesForPermissionOn(p, self.portal):
                errors.append('%s: Should be enabled' % p)

        if errors:
            self.fail('Unexpected permissions for Manager role:\n' +
                      ''.join(['\t%s\n' % msg for msg in errors])
                      )

    def testOwnerPermissions(self):
        errors = []

        for p in (SetGroupOwnership, ViewGroups):
            if 'Owner' not in rolesForPermissionOn(p, self.portal):
                errors.append('%s: Should be enabled' % p)

        for p in (AddGroups, DeleteGroups, ManageGroups):
            if 'Owner' in rolesForPermissionOn(p, self.portal):
                errors.append('%s: Should be disabled' % p)

        if errors:
            self.fail('Unexpected permissions for Owner role:\n' +
                      ''.join(['\t%s\n' % msg for msg in errors])
                      )

    def testMemberPermissions(self):
        errors = []

        for p in (ViewGroups,):
            if 'Member' not in rolesForPermissionOn(p, self.portal):
                errors.append('%s: Should be enabled' % p)

        for p in (AddGroups, DeleteGroups, ManageGroups, SetGroupOwnership):
            if 'Member' in rolesForPermissionOn(p, self.portal):
                errors.append('%s: Should be disabled' % p)

        if errors:
            self.fail('Unexpected permissions for Member role:\n' +
                      ''.join(['\t%s\n' % msg for msg in errors])
                      )

