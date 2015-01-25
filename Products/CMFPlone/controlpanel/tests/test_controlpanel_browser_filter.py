# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IFilterSchema
from Products.CMFPlone.testing import PRODUCTS_CMFPLONE_FUNCTIONAL_TESTING
from Products.PortalTransforms.data import datastream
from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
from plone.registry.interfaces import IRegistry
from plone.testing.z2 import Browser
from zope.component import getMultiAdapter
from zope.component import getUtility
import unittest2 as unittest


class FilterControlPanelFunctionalTest(unittest.TestCase):
    """Test that changes in the site control panel are actually
    stored in the registry.
    """

    layer = PRODUCTS_CMFPLONE_FUNCTIONAL_TESTING

    def setUp(self):  # NOQA
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(self.app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )
        self.safe_html = getattr(
            getToolByName(self.portal, 'portal_transforms'),
            'safe_html',
            None)

    def test_filter_control_panel_link(self):
        self.browser.open(
            "%s/plone_control_panel" % self.portal_url)
        self.browser.getLink('Site').click()

    def test_filter_control_panel_backlink(self):
        self.browser.open(
            "%s/@@filter-controlpanel" % self.portal_url)
        self.assertTrue("Plone Configuration" in self.browser.contents)

    def test_filter_control_panel_sidebar(self):
        self.browser.open(
            "%s/@@filter-controlpanel" % self.portal_url)
        self.browser.getLink('Site Setup').click()
        self.assertEqual(
            self.browser.url,
            'http://nohost/plone/@@overview-controlpanel')

    def test_filter_controlpanel_view(self):
        view = getMultiAdapter((self.portal, self.portal.REQUEST),
                               name="filter-controlpanel")
        view = view.__of__(self.portal)
        self.assertTrue(view())

    def test_disable_filtering(self):
        self.browser.open(
            "%s/@@filter-controlpanel" % self.portal_url)
        self.browser.getControl(
            name='form.widgets.disable_filtering:list').value = "selected"
        self.browser.getControl('Save').click()

        # test registry storage
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IFilterSchema, prefix="plone")
        self.assertEqual(settings.disable_filtering, True)

        # test that the transform is disabled, making anything pass
        nasty_html = '<script></script>'
        ds = datastream('dummy_name')
        self.assertEqual(
            nasty_html,
            str(self.safe_html.convert(nasty_html, ds))
        )

    def test_nasty_tags(self):
        self.browser.open(
            "%s/@@filter-controlpanel" % self.portal_url)
        self.browser.getControl(
            name='form.widgets.nasty_tags'
        ).value = 'div\r\na'
        self.browser.getControl('Save').click()

        # test registry storage
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IFilterSchema, prefix="plone")
        self.assertEqual(sorted(settings.nasty_tags), ['a', 'div'])

        # test that <a> is filtered
        self.assertFalse(settings.disable_filtering)
        good_html = '<a href="http://example.com">harmless link</a>'
        ds = datastream('dummy_name')
        self.assertEqual(
            str(self.safe_html.convert(good_html, ds)),
            ''
        )

    def test_stripped_tags_is_stored_in_registry(self):
        self.browser.open(
            "%s/@@filter-controlpanel" % self.portal_url)
        self.browser.getControl(
            name='form.widgets.stripped_tags'
        ).value = 'foo\r\nbar'
        self.browser.getControl('Save').click()

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IFilterSchema, prefix="plone")
        self.assertEqual(settings.stripped_tags, ['foo', 'bar'])

    def test_custom_tags_is_stored_in_registry(self):
        self.browser.open(
            "%s/@@filter-controlpanel" % self.portal_url)
        self.browser.getControl(
            name='form.widgets.custom_tags'
        ).value = 'foo\r\nbar'
        self.browser.getControl('Save').click()

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IFilterSchema, prefix="plone")
        self.assertEqual(settings.custom_tags, ['foo', 'bar'])

    def test_stripped_attributes_is_stored_in_registry(self):
        self.browser.open(
            "%s/@@filter-controlpanel" % self.portal_url)
        self.browser.getControl(
            name='form.widgets.stripped_attributes'
        ).value = 'foo\r\nbar'
        self.browser.getControl('Save').click()

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IFilterSchema, prefix="plone")
        self.assertEqual(settings.stripped_attributes, ['foo', 'bar'])

    def test_style_whitelist_is_stored_in_registry(self):
        self.browser.open(
            "%s/@@filter-controlpanel" % self.portal_url)
        self.browser.getControl(
            name='form.widgets.style_whitelist'
        ).value = 'foo\r\nbar'
        self.browser.getControl('Save').click()

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IFilterSchema, prefix="plone")
        self.assertEqual(settings.style_whitelist, ['foo', 'bar'])

    def test_class_blacklist_is_stored_in_registry(self):
        self.browser.open(
            "%s/@@filter-controlpanel" % self.portal_url)
        self.browser.getControl(
            name='form.widgets.class_blacklist'
        ).value = 'foo\r\nbar'
        self.browser.getControl('Save').click()

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IFilterSchema, prefix="plone")
        self.assertEqual(settings.class_blacklist, ['foo', 'bar'])
