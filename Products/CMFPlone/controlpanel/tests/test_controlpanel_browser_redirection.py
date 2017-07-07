# -*- coding: utf-8 -*-
from Products.CMFPlone.PloneBatch import Batch
from Products.CMFPlone.controlpanel.browser.redirects import RedirectionSet
from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
from plone.app.redirector.interfaces import IRedirectionStorage
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

    def test_redirection_controlpanel_add_redirect(self):

        redirection_path = '/Member1'
        target_path = '/Member'
        storage_path = '/plone/Member1'

        self.browser.open(
            "%s/@@redirection-controlpanel" % self.portal_url)
        self.browser.getControl(
            name='redirection').value = redirection_path
        self.browser.getControl(
            name='target_path').value = target_path
        self.browser.getControl(name='form.button.Add').click()

        storage = getUtility(IRedirectionStorage)
        self.assertTrue(
            storage.has_path(storage_path),
            u'Redirection storage should have path "{0}"'.format(storage_path)
        )

    def test_redirection_controlpanel_set(self):
        storage = getUtility(IRedirectionStorage)
        portal_path = self.layer['portal'].absolute_url_path()
        for i in range(1000):
            storage.add('{0:s}/foo/{1:s}'.format(portal_path, str(i)),
                        '{0:s}/bar/{1:s}'.format(portal_path, str(i)))
        redirects = RedirectionSet()
        self.assertEqual(len(redirects), 1000)
        self.assertDictEqual(redirects[0], {
            'redirect': '{0:s}/foo/0'.format(portal_path),
            'path': '/foo/0', 'redirect-to': '/bar/0'
        })
        self.assertDictEqual(redirects[999], {
            'redirect': '{0:s}/foo/999'.format(portal_path),
            'path': '/foo/999', 'redirect-to': '/bar/999'
        })
        self.assertEqual(len(list(iter(redirects))), 1000)
        self.assertDictEqual(list(iter(redirects))[0], {
            'redirect': '{0:s}/foo/0'.format(portal_path),
            'path': '/foo/0', 'redirect-to': '/bar/0'
        })

    def test_redirection_controlpanel_batching(self):
        storage = getUtility(IRedirectionStorage)
        portal_path = self.layer['portal'].absolute_url_path()
        for i in range(1000):
            storage.add('{0:s}/foo/{1:s}'.format(portal_path, str(i)),
                        '{0:s}/bar/{1:s}'.format(portal_path, str(i)))
        view = getMultiAdapter((self.layer['portal'], self.layer['request']),
                               name='redirection-controlpanel')
        # Test that view/redirects returns batch
        self.assertIsInstance(view.redirects(), Batch)

        # Test that view/batching returns batching with anchor in urls
        batching = view.batching()
        self.assertIn('?b_start:int=990#manage-existing-aliases', batching)