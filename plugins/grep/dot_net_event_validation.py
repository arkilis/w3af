'''
dot_net_event_validation.py

Copyright 2008 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
import re

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from core.data.kb.info import Info


class dot_net_event_validation(GrepPlugin):
    '''
    Grep every page and identify the ones that have viewstate and don't have event validation.

    :author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)

        vs_regex = r'<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value=".*?" />'
        self._viewstate = re.compile(vs_regex, re.IGNORECASE | re.DOTALL)

        ev_regex = r'<input type="hidden" name="__EVENTVALIDATION" '
        ev_regex += 'id="__EVENTVALIDATION" value=".*?" />'
        self._eventvalidation = re.compile(ev_regex, re.IGNORECASE | re.DOTALL)

        encryptedvs_regex = r'<input type="hidden" name="__VIEWSTATEENCRYPTED" '
        encryptedvs_regex += 'id="__VIEWSTATEENCRYPTED" value=".*?" />'
        self._encryptedVs = re.compile(
            encryptedvs_regex, re.IGNORECASE | re.DOTALL)

        self._already_analyzed = ScalableBloomFilter()

    def grep(self, request, response):
        '''
        If I find __VIEWSTATE and empty __EVENTVALIDATION => vuln.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        '''
        if not response.is_text_or_html():
            return

        # First verify if we havent analyzed this URI yet
        if request.get_url() in self._already_analyzed:
            return

        self._already_analyzed.add(request.get_url())

        res = self._viewstate.search(response.get_body())
        if res:

            # I have __viewstate!, verify if event validation is enabled
            if not self._eventvalidation.search(response.get_body()):
                desc = 'The URL: "%s" has .NET Event Validation disabled.'\
                       ' This programming/configuration error should be'\
                       ' manually verified.'
                desc = desc % response.get_url()
                i = Info('.NET Event Validation is disabled', desc,
                         response.id, self.get_name())
                i.set_url(response.get_url())
                i.add_to_highlight(res.group())
                
                self.kb_append(self, 'dot_net_event_validation', i)

            if not self._encryptedVs.search(response.get_body()):
                # Nice! We can decode the viewstate! =)
                desc = 'The URL: "%s" has .NET ViewState encryption disabled.'\
                       ' This programming/configuration error could be exploited'\
                       ' to decode the viewstate contents.'
                desc = desc % response.get_url()
                
                i = Info('.NET ViewState encryption is disabled', desc,
                         response.id, self.get_name())
                i.set_url(response.get_url())
                
                self.kb_append(self, 'dot_net_event_validation', i)

    def get_long_desc(self):
        '''
        :return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        ASP.NET implements a method to verify that every postback comes from the
        corresponding control, which is called EventValidation. In some cases the
        developers disable this kind of verifications by adding
        EnableEventValidation="false" to the .aspx file header, or in the web.config
        or system.config files.

        This plugin finds pages that have event validation disabled. In some
        cases, if you analyze the logic of the program and event validation
        is disabled, you'll be able to bypass authorizations or some other
        controls.
        '''
