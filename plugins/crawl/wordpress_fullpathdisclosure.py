'''
wordpress_username_enumeration.py

Copyright 2011 Andres Riancho

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

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.exceptions import w3afRunOnce
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.data.kb.info import Info


class wordpress_fullpathdisclosure(CrawlPlugin):
    '''
    Try to find the path where the WordPress is installed
    :author: Andres Tarantini ( atarantini@gmail.com )
    '''

    CHECK_PATHS = ['wp-content/plugins/akismet/akismet.php',
                   'wp-content/plugins/hello.php']

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._exec = True

    def crawl(self, fuzzable_request):
        '''
        :param fuzzable_request: A fuzzable_request instance that contains
                                     (among other things) the URL to test.
        '''
        if not self._exec:
            raise w3afRunOnce()
        else:
            # Check if there is a wordpress installation in this directory
            domain_path = fuzzable_request.get_url().get_domain_path()
            wp_unique_url = domain_path.url_join('wp-login.php')
            response = self._uri_opener.GET(wp_unique_url, cache=True)

            # If wp_unique_url is not 404, wordpress = true
            if not is_404(response):
                # Only run once
                self._exec = False

                extracted_paths = self._extract_paths(domain_path)
                self._force_disclosures(domain_path,
                                        self.CHECK_PATHS + extracted_paths)

    def _extract_paths(self, domain_path):
        '''
        :param domain_path: The URL object pointing to the current wordpress
                            installation
        :return: A list with the paths that might trigger full path disclosures

        TODO: Will fail if WordPress is running on a Windows server due to
              paths manipulation.
        '''
        theme_paths = []
        wp_root_response = self._uri_opener.GET(domain_path, cache=True)

        if not is_404(wp_root_response):
            response_body = wp_root_response.get_body()

            theme_regexp = '%swp-content/themes/(.*)/style.css' % domain_path
            theme = re.search(theme_regexp, response_body, re.IGNORECASE)
            if theme:
                theme_name = theme.group(1)
                for fname in ('header', 'footer'):
                    path_fname = 'wp-content/themes/%s/%s.php' % (
                        theme_name, fname)
                    theme_paths.append(path_fname)

        return theme_paths

    def _force_disclosures(self, domain_path, potentially_vulnerable_paths):
        '''
        :param domain_path: The path to wordpress' root directory
        :param potentially_vulnerable_paths: A list with the paths I'll URL-join
                                             with @domain_path, GET and parse.
        '''
        for pvuln_path in potentially_vulnerable_paths:

            pvuln_url = domain_path.url_join(pvuln_path)
            response = self._uri_opener.GET(pvuln_url, cache=True)

            if is_404(response):
                continue

            response_body = response.get_body()
            if 'Fatal error: ' in response_body:
                desc = 'Analyze the HTTP response body to find the full path'\
                       ' where wordpress was installed.'
                i = Info('WordPress path disclosure', desc, response.id,
                         self.get_name())
                i.set_url(pvuln_url)
                
                kb.kb.append(self, 'info', i)
                om.out.information(i.get_desc())
                break

    def get_long_desc(self):
        '''
        :return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin try to find the path in the server where WordPress is
        installed.
        '''
