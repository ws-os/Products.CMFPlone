# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import ISearchSchema
from Products.CMFPlone.controlpanel import tests

from plone.registry.interfaces import IRegistry

from zope.component import getUtility
from zope.component import getMultiAdapter


class SearchControlPanelFunctionalTest(tests.ControlPanelFunctionalTest):
    """Test that changes in the search control panel are actually
    stored in the registry.
    """

    def test_search_control_panel_link(self):
        self.browser.open(
            "%s/plone_control_panel" % self.portal_url)
        self.browser.getLink('Search').click()

    def test_search_control_panel_backlink(self):
        self.browser.open(
            "%s/@@search-controlpanel" % self.portal_url)
        self.assertTrue("Plone Configuration" in self.browser.contents)

    def test_search_control_panel_sidebar(self):
        self.browser.open(
            "%s/@@search-controlpanel" % self.portal_url)
        self.browser.getLink('Site Setup').click()
        self.assertEqual(
            self.browser.url,
            'http://nohost/plone/@@overview-controlpanel')

    def test_search_controlpanel_view(self):
        view = getMultiAdapter((self.portal, self.portal.REQUEST),
                               name="search-controlpanel")
        view = view.__of__(self.portal)
        self.assertTrue(view())

    def test_enable_livesearch(self):
        self.browser.open(
            "%s/@@search-controlpanel" % self.portal_url)
        self.browser.getControl('Enable LiveSearch').selected = True
        self.browser.getControl('Save').click()

        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISearchSchema, prefix="plone")
        self.assertEqual(settings.enable_livesearch, True)

    def test_types_not_searched(self):
        self.browser.open(
            "%s/@@search-controlpanel" % self.portal_url)
        self.browser.getControl(
            name='form.widgets.types_not_searched:list'
        ).value = ['Discussion Item', 'News Item']
        self.browser.getControl('Save').click()

        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISearchSchema, prefix="plone")
        self.assertFalse('Discussion Item' in settings.types_not_searched)
        self.assertFalse('News Item Item' in settings.types_not_searched)
