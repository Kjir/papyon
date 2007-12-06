# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""Useful decorators"""

import sys
import warnings

def decorator(function):
    """decorator to be used on decorators, it preserves the docstring and
    function attributes of functions to which it is applied."""
    def new_decorator(f):
        g = decorator(f)
        g.__name__ = f.__name__
        g.__doc__ = f.__doc__
        g.__dict__.update(f.__dict__)
        return g
    new_decorator.__name__ = function.__name__
    new_decorator.__doc__ = function.__doc__
    new_decorator.__dict__.update(function.__dict__)
    return new_decorator


def rw_property(function):
    """This decorator implements read/write properties, as follow:
    
        @rw_property
        def my_property():
            "Documentation"
            def fget(self):
                return self._my_property
            def fset(self, value):
                self._my_property = value
    """
    keys = 'fget', 'fset', 'fdel'
    func_locals = {'doc' : function.__doc__}

    def probe_func(frame, event, arg):
        if event == 'return':
            locals = frame.f_locals
            func_locals.update(dict((k,locals.get(k)) for k in keys))
            sys.settrace(None)
        return probe_func
    sys.settrace(probe_func)
    function()
    return property(**func_locals)


@decorator
def deprecated(func):
    """This is a decorator which can be used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used."""
    def new_function(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    return new_function

@decorator
def unstable(func):
    """This is a decorator which can be used to mark functions as unstable API
    wise. It will result in a warning being emitted when the function is used."""
    def new_function(*args, **kwargs):
        warnings.warn("Call to unstable API function %s." % func.__name__,
                      category=FutureWarning)
        return func(*args, **kwargs)
    return new_function


