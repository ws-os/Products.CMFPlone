# -*- coding: utf-8 -*-
from AccessControl import getSecurityManager
from cStringIO import StringIO
from plone import api
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.memoize.instance import memoize
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.permissions import ManagePortal
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getUtility
from zope.i18nmessageid import MessageFactory

import csv

_ = MessageFactory('plone')


def absolutize_path(path, context=None, is_source=True):
    """Check whether object exist to the provided `path`.
       Assume relative paths are relative to `context`;
       reject relative paths if `context` is None.
       Return a 2-tuple: (absolute redirection path,
       an error message if something goes wrong and otherwise '').
    """

    portal = getUtility(ISiteRoot)
    err = None
    if path is None or path == '':
        err = (is_alias and _(u"You have to enter an alias.")
               or _(u"You have to enter a target."))
    else:
        if path.startswith('/'):
            context_path = "/".join(portal.getPhysicalPath())
            path = "{0}{1}".format(context_path, path)
        else:
            if context is None:
                err = (is_alias and _(u"Alias path must start with a slash.")
                       or _(u"Target path must start with a slash."))
            else:
                # What case should this be?
                context_path = "/".join(context.getPhysicalPath()[:-1])
                path = "{0}/{1}".format(context_path, path)
        if not err and is_source:
            # Check whether obj exists at source path
            result = api.content.find(path={"query": path})
            if len(result) == 0:
                err = _(u"The provided source path does not point to an object.")
        if not err and not is_source:
            # Check whether obj exists at target path
            result = api.content.find(path={"query": path})
            if len(result) != 0:
                err = _(u"The provided target path does already exist.")
    return path, err

class RedirectsView(BrowserView):
    template = ViewPageTemplateFile('redirects-manage.pt')

    def redirects(self):
        storage = getUtility(IRedirectionStorage)
        portal = getUtility(ISiteRoot)
        context_path = "/".join(self.context.getPhysicalPath())
        portal_path = "/".join(portal.getPhysicalPath())
        redirects = storage.redirects(context_path)
        for redirect in redirects:
            path = redirect[len(portal_path):]
            yield {
                'redirect': redirect,
                'path': path,
            }

    def __call__(self):
        storage = getUtility(IRedirectionStorage)
        request = self.request
        form = request.form
        status = IStatusMessage(self.request)
        errors = {}

        if 'form.button.Add' in form:
            redirection, err = absolutize_path(form.get('redirection'), is_source=False)
            if err:
                errors['redirection'] = err
                status.addStatusMessage(err, type='error')
            else:
                del form['redirection']
                storage.add(redirection, "/".join(self.context.getPhysicalPath()))
                status.addStatusMessage(_(u"Alias added."), type='info')
        elif 'form.button.Remove' in form:
            redirects = form.get('redirects', ())
            for redirect in redirects:
                storage.remove(redirect)
            if len(redirects) > 1:
                status.addStatusMessage(_(u"Aliases removed."), type='info')
            else:
                status.addStatusMessage(_(u"Alias removed."), type='info')

        return self.template(errors=errors)

    @memoize
    def view_url(self):
        return self.context.absolute_url() + '/@@manage-aliases'


class RedirectsControlPanel(BrowserView):

    template = ViewPageTemplateFile('redirects-controlpanel.pt')

    def __init__(self, context, request):
        super(RedirectsControlPanel, self).__init__(context, request)
        self.errors = []
        # list of tuples: (line_number, absolute_redirection_path, err_msg, target)

    def redirects(self):
        """ Get existing redirects from the redirection storage.
            Return dict with the strings redirect, path and redirect-to.
            Strip the id of the instance from path and redirect-to if
            it is present. (Seems to be always true)
            If id of instance is not present in path the var 'path' and
            'redirect' are equal.
        """
        storage = getUtility(IRedirectionStorage)
        portal = getUtility(ISiteRoot)
        portal_path = "/".join(portal.getPhysicalPath())
        portal_path_len = len(portal_path)
        for redirect in storage:
            if redirect.startswith(portal_path):
                path = redirect[portal_path_len:]
            else:
                path = redirect
            redirectto = storage.get(redirect)
            if redirectto.startswith(portal_path):
                redirectto = redirectto[portal_path_len:]
            yield {
                'redirect': redirect,
                'path': path,
                'redirect-to': redirectto,
            }

    def __call__(self):
        storage = getUtility(IRedirectionStorage)
        portal = getUtility(ISiteRoot)
        request = self.request
        form = request.form
        status = IStatusMessage(self.request)

        if 'form.button.Remove' in form:
            redirects = form.get('redirects', ())
            for redirect in redirects:
                storage.remove(redirect)
            if len(redirects) == 0:
                status.addStatusMessage(_(u"No aliases selected for removal."), type='info')
            elif len(redirects) > 1:
                status.addStatusMessage(_(u"Aliases removed."), type='info')
            else:
                status.addStatusMessage(_(u"Alias removed."), type='info')
        elif 'form.button.Add' in form:
            self.add(form['redirection'], form['target_path'], portal, storage, status)
        elif 'form.button.Upload' in form:
            self.upload(form['file'], portal, storage, status)

        return self.template()

    def add(self, redirection, target, portal, storage, status):
        """Add the redirections from the form. If anything goes wrong, do nothing."""

        abs_redirection, err = absolutize_path(redirection, is_source=True)
        abs_target, target_err = absolutize_path(target, is_source=False)

        if err and target_err:
            err = "{0} {1}".format(err, target_err)
        elif target_err:
            err = target_err
        else:
            if abs_redirection == abs_target:
                err = _(u"Aliases that point to themselves will cause"
                        u"an endless cycle of redirects.")
                # TODO: detect indirect recursion

        if not err:
            storage.add(abs_redirection, abs_target)
            status.addStatusMessage(_(u"Alias {0} &rarr; {1} added.").format(abs_redirection, abs_target),
                                    type='info')

    def upload(self, file, portal, storage, status):
        """Add the redirections from the CSV file `file`. If anything goes wrong, do nothing."""

        # No file picked. Theres gotta be a better way to handle this.
        if not file.filename:
            status.addStatusMessage(_(u"Please pick a file to upload."), type='info')
            return
        # Turn all kinds of newlines into LF ones. The csv module doesn't do
        # its own newline sniffing and requires either \n or \r.
        file = StringIO('\n'.join(file.read().splitlines()))

        # Use first two lines as a representative sample for guessing format,
        # in case one is a bunch of headers.
        dialect = csv.Sniffer().sniff(file.readline() + file.readline())
        file.seek(0)

        successes = []  # list of tuples: (abs_redirection, target)
        had_errors = False
        for i, fields in enumerate(csv.reader(file, dialect)):
            if len(fields) == 2:
                redirection, target = fields
                abs_redirection, err = absolutize_path(redirection, is_alias=True)
                abs_target, target_err = absolutize_path(target, is_alias=False)
                if err and target_err:
                    err = "%s %s" % (err, target_err)  # sloppy w.r.t. i18n
                elif target_err:
                    err = target_err
                else:
                    if abs_redirection == abs_target:
                        # TODO: detect indirect recursion
                        err = _(u"Aliases that point to themselves will cause"
                                u"an endless cycle of redirects.")
            else:
                err = _(u"Each line must have 2 columns.")

            if not err:
                if not had_errors:  # else don't bother
                    successes.append((abs_redirection, abs_target))
            else:
                had_errors = True
                self.errors.append(dict(line_number=i+1, line=dialect.delimiter.join(fields),
                                        message=err))

        if not had_errors:
            for abs_redirection, abs_target in successes:
                storage.add(abs_redirection, abs_target)
            status.addStatusMessage(_(u"%i aliases added.") % len(successes), type='info')

    @memoize
    def view_url(self):
        return self.context.absolute_url() + '/@@redirection-controlpanel'
