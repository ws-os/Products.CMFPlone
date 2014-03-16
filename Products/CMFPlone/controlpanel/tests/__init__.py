# -*- coding: utf-8 -*-
import unittest

from plone.testing import z2
from plone.app import testing

from Products.CMFPlone import testing as cmfplone_testing


class ControlPanelFunctionalTest(unittest.TestCase):

    layer = cmfplone_testing.PRODUCTS_CMFPLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.portal_url = self.portal.absolute_url()
        self.browser = z2.Browser(self.app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization', 'Basic %s:%s' % (
                testing.SITE_OWNER_NAME, testing.SITE_OWNER_PASSWORD))
