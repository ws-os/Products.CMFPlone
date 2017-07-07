# -*- coding: utf-8 -*-
from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
from plone.registry.interfaces import IRegistry
from plone.testing.z2 import Browser

from zope.component import getMultiAdapter
from zope.component import getUtility

from Products.CMFPlone.testing import \
    PRODUCTS_CMFPLONE_FUNCTIONAL_TESTING

import unittest


class RedirectionControlPanelFunctionalTest(unittest.TestCase):
    """Test that changes in the mail control panel are actually
    stored in the registry.
    """

    layer = PRODUCTS_CMFPLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(self.app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )

    """
    def test_mail_controlpanel_link(self):
        self.browser.open(
            "%s/@@overview-controlpanel" % self.portal_url)
        self.browser.getLink('Mail').click()

    def test_mail_controlpanel_backlink(self):
        self.browser.open(
            "%s/@@mail-controlpanel" % self.portal_url)
        self.assertTrue("General" in self.browser.contents)

    def test_mail_controlpanel_sidebar(self):
        self.browser.open(
            "%s/@@mail-controlpanel" % self.portal_url)
        self.browser.getLink('Site Setup').click()
        self.assertTrue(
            self.browser.url.endswith('/plone/@@overview-controlpanel')
        )
    """

    def test_redirection_controlpanel_view(self):
        view = getMultiAdapter((self.portal, self.portal.REQUEST),
                               name="redirection-controlpanel")
        self.assertTrue(view())
