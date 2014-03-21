# -*- coding: utf-8 -*-
import json
import urllib

from lxml import etree

from Products.CMFPlone.controlpanel import tests


class UsersGroupsControlPanelFunctionalTest(tests.ControlPanelFunctionalTest):
    """
    The Users and Groups control panels render to the browser.
    """

    def test_site_control_panel_link(self):
        """
        Control panel has a link to the users listing.
        """
        self.browser.open(
            "%s/plone_control_panel" % self.portal_url)
        self.browser.getLink('Users and Groups').click()
        self.assertTrue(
            self.browser.url.endswith('@@users-controlpanel'),
            'Users control panel links to wrong URL')

    def test_controlpanel_users_renders(self):
        """
        Users listing structure pattern renders.
        """
        self.browser.open(
            "%s/@@users-controlpanel" % self.portal_url)
        self.assertRegexpMatches(
            self.browser.headers['content-type'], r'^text/html',
            'Response is not HTML')
        html = etree.fromstring(self.browser.contents)
        patterns = html.xpath("//*[@class='pat-structure']")
        self.assertEqual(
            len(patterns), 1, 'Wrong number of structure mockup patterns')
        self.assertIn(
            'data-pat-structure', patterns[0].attrib,
            'Missing structure mockup pattern data attribute')
        self.assertIn(
            'vocabularyUrl', patterns[0].attrib['data-pat-structure'],
            'Missing structure mockup pattern custom users list')
        self.assertIn(
            'vocabularyUrl', patterns[0].attrib['data-pat-structure'],
            'Missing structure mockup pattern custom users list')

    def test_controlpanel_users_admin_vocabulary(self):
        """
        Users admin vocabulary returns extra data for administering users.
        """
        attributes = [
            'id', 'login', 'fullname', 'email', 'roles',
            'can_delete', 'can_set_email', 'can_set_password']
        query = dict(
            name='plone.app.vocabularies.UsersAdmin',
            query='test',
            attributes=json.dumps(attributes))
        self.browser.open("{0}/@@getVocabulary?{1}".format(
            self.portal_url, urllib.urlencode(query)))
        self.assertRegexpMatches(
            self.browser.headers['content-type'], r'^application/json',
            'Response is not JSON')
        response = json.loads(self.browser.contents)
        self.assertIn('results', response, 'Missing JSON results list')
        self.assertIsInstance(
            response['results'], list, 'Wrong JSON results list type')
        for attr in attributes:
            self.assertIn(
                attr, response['results'][0], 'Missing user info attribute')
            self.assertTrue(
                attr, response['results'][0], 'Empty user info attribute')
