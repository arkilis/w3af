'''
reqResDBHandler.py

Copyright 2007 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

import core.data.kb.knowledgeBase as kb
import core.controllers.outputManager as om
import re
from core.controllers.w3afException import w3afException
from core.data.db.persist import persist

class reqResDBHandler:
    '''
    A handler for the database that stores requests and responses.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        pass
    
    def _initDB( self ):
        if kb.kb.getData('gtkOutput', 'db') == []:
            return False
        else:
            # Restore it from the kb
            self._db = kb.kb.getData('gtkOutput', 'db')
            return True
    
    def searchById( self, search_id ):
        '''
        @return: A request object that has an id == search_id
        '''
        if not self._initDB():
            raise w3afException('The database is not initialized yet.')
        else:
            try:
                result = self._db.retrieve_all( 'id = ' + str(int(search_id)) )
                return result
            except Exception, e:
                raise e

    def validate(self, text):
        '''
        Validates if the text matches the regular expression
        
        @param text: the text to validate
        @return: True if the text is ok.
        '''
        #FIXME: This re is buggy
        self._match = re.match('^(?:((?:id|uri)) (=|>|>=|<=|<|<>|like) ([\w\'\" /:\.]+)( (and|or) )?)*$', text )
        if self._match:
            return True
        else:
            return False

    def search(self, search_data, result_limit=-1, order_data=[]):
        '''Make complex search.
        search_data = [(name, value, operator), ...]
        '''

        if not self._initDB():
            raise w3afException('The database is not initialized yet.')

        where = "1=1"
        for item in search_data:
            oper = "="
            value = item[1]
            if len(item) > 2:
                oper = item[2]
            if isinstance(value, str):
                value = "'" + value + "'"
            else:
                value = str(value)
            where += " AND (" + item[0] + " " + oper + " " + value + ")"

        orderby = ""
        for item in order_data:
            orderby += item[0] + " " + item[1] + ","
        orderby = orderby[:-1]

        try:
            result = self._db.retrieve_all(where, result_limit=result_limit,
                    orderby=orderby)
            return result
        except w3afException:
            raise w3afException('You performed an invalid search. Please verify your syntax.')

    def searchByString( self, search_string, result_limit=-1 ):
        '''
        @return: A request object that matches the search string.
        '''
        if not self._initDB():
            raise w3afException('The database is not initialized yet.')
        else:
            try:
                result = self._db.retrieve_all( search_string, result_limit=result_limit )
                return result
            except w3afException:
                raise w3afException('You performed an invalid search. Please verify your syntax.')
