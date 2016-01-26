# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.instance import memoize
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.PlonePAS.interfaces.browser import IPASInfoView
from Products.PlonePAS.interfaces.browser import IPASMemberView
from Products.PlonePAS.interfaces.browser import IPASSearchView
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins \
    import ILoginPasswordExtractionPlugin
from zope.component import queryUtility
from zope.interface import implementer


@implementer(IPASInfoView)
class PASInfoView(BrowserView):

    def checkExtractorForInterface(self, interface):
        acl = getToolByName(aq_inner(self.context), "acl_users")
        plugins = acl.plugins.listPlugins(IExtractionPlugin)

        for plugin in plugins:
            if interface.providedBy(plugin[1]):
                return True

        return False

    @memoize
    def hasLoginPasswordExtractor(self):
        return self.checkExtractorForInterface(ILoginPasswordExtractionPlugin)

    @memoize
    def hasOpenIDExtractor(self):
        try:
            from plone.openid.interfaces import IOpenIdExtractionPlugin
        except ImportError:
            return False

        return self.checkExtractorForInterface(IOpenIdExtractionPlugin)

    def hasOpenIDdExtractor(self):
        # BBB Keeping method name with typo for backwards compatibility.
        return self.hasOpenIDExtractor()


@implementer(IPASMemberView)
class PASMemberView(BrowserView):

    @memoize
    def info(self, userid=None):
        pm = getToolByName(self.context, 'portal_membership')
        result = pm.getMemberInfo(memberId=userid)
        if result is None:
            # No such member: removed?  We return something useful anyway.
            return {
                'username': userid,
                'description': '',
                'language': '',
                'home_page': '',
                'name_or_id': userid,
                'location': '',
                'fullname': ''
            }
        result['name_or_id'] = result.get('fullname') or \
            result.get('username') or userid
        return result


@implementer(IPASSearchView)
class PASSearchView(BrowserView):

    @staticmethod
    def extractCriteriaFromRequest(request):
        criteria = request.form.copy()

        for key in ["form.submitted", "submit", 'b_start', 'b_size']:
            if key in criteria:
                del criteria[key]

        for (key, value) in criteria.items():
            if not value:
                del criteria[key]

        return criteria

    @staticmethod
    def merge(results, key):
        output = {}
        for entry in results:
            id = entry[key]
            if id not in output:
                output[id] = entry.copy()
            else:
                buf = entry.copy()
                buf.update(output[id])
                output[id] = buf

        return output.values()

    def sort(self, results, sort_key):
        idnormalizer = queryUtility(IIDNormalizer)

        def key_func(a):
            return idnormalizer.normalize(a.get(sort_key, a))
        return sorted(results, key=key_func)

    def searchUsers(self, sort_by=None, **criteria):
        self.pas = getToolByName(self.context, "acl_users")
        results = self.merge(self.pas.searchUsers(**criteria), "userid")
        if sort_by is not None:
            results = self.sort(results, sort_by)
        return results

    def searchUsersByRequest(self, request, sort_by=None):
        criteria = self.extractCriteriaFromRequest(request)
        return self.searchUsers(sort_by=sort_by, **criteria)

    def searchGroups(self, sort_by=None, **criteria):
        self.pas = getToolByName(self.context, "acl_users")
        results = self.merge(self.pas.searchGroups(**criteria), "groupid")
        if sort_by is not None:
            results = self.sort(results, sort_by)
        return results

    def searchGroupsByRequest(self, request):
        criteria = self.extractCriteriaFromRequest(request)
        return self.searchGroups(**criteria)

    def getPhysicalPath(self):
        # We call various PAS methods which can be ZCached. The ZCache
        # infrastructure relies on getPhysicalPath on the context being
        # available, which this view does not have, it not being a
        # persistent object. So we fake things and return the physical path
        # for our context.
        return self.context.getPhysicalPath()
