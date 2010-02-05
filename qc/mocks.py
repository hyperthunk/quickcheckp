#!/usr/bin/env python
# Copyright (c) 2008, Tim Watson, all rights reserved.
"""
 Library support for creating mock and stub objects and using them in nose tests.
"""

from hamcrest.core.matcher_assert import assert_that
from hamcrest.core.core.is_ import is_
from hamcrest.library.collection.isin import is_in 
from new import instancemethod

def f_dummy(*args, **kwargs): pass

class TestDouble(object):
    """ Very simple test double implementation. """

    def __init__(self, delegate=None):
        self.delegate = delegate

    def respond_to(self, name='__call__', return_value=f_dummy):
        if not callable(return_value):
            self.set_response(lambda *args, **kwargs: return_value, name)
        else:
            self.set_response(return_value, name)

    #TODO: raise_error

    def __call__(self, *args, **kwargs):
        if self.callable_override:
            return self.overriden_special__call__(*args, **kwargs)
        super(TestDouble, self).__call__(*args, **kwargs)

    def ignore(self, name):
        self.respond_to(name, None)

    def set_response(self, response, name):
        if name == '__call__':
            self.callable_override = True
            self.respond_to('overriden_special__call__', response)
        else:
            setattr(self, name, instancemethod(response, self))    
    
    def __getattr__(self, name):
        if self.delegate is not None and hasattr(self.delegate, name):
            return getattr(self.delegate, name)
        #default behavior is to silently return self
        return lambda *args, **kwargs: self

class MockObject(TestDouble):

    def __init__(self, delegate=None, strict=False):
        TestDouble.__init__(self, delegate)
        self.expectations = {}
        self.received = {}
        self.strict = strict

    def expect(self, attr_name, count=None, *argv, **kw):
        if count is None: count = once()
        retval = kw.get('return_value', None)
        if kw.has_key('return_value'):
            del kw['return_value']
        self.expectations[attr_name] = (count, argv, kw)
        def handle_call(self, *args, **kwargs):
            count()
            calls = self.received.get(attr_name, [])
            calls.append((args, kwargs))
            self.received[attr_name] = calls
            return retval
        self.respond_to(attr_name, handle_call)

    def verify_expectations(self):
        for attr, (count, arg_matchers, kw_matchers) in self.expectations.iteritems():
            count.verify(attr)
            assert_that(attr, is_in(self.received),
                "expected to receive %s but was not recorded" % (attr)) #TODO: error message might help!
            for (args, kwargs) in self.received[attr]:
                map(lambda (arg, matcher): assert_that(arg, matcher),
                    zip(args, arg_matchers))
                #TODO: loop around the expected matchers not the actual inputs?
                for name, value in kwargs.iteritems():
                    assert_that(name, is_in(kw_matchers),
                        "expected named argument %s but was not recorded" % (name))
                    assert_that(value, kw_matchers[name])

    def __getattr__(self, name):
        if self.nonstrict():
            return TestDouble.__getattr__(self, name)
        raise AttributeError, "attribute aquisition: unexpected call to %s" % (name)

    def nonstrict(self):
        """indicates whether or not this mock is
        'strict' about expected method invocations"""
        return not (self.strict and (self.delegate is None))
    
# expecting invocation counts

class InvocationTracker(object):

    def __init__(self, expected_ccount=0):
        self.expected_ccount = expected_ccount
        self.ccount = 0

    def __call__(self): self.ccount += 1

    def verify(self, name):
        assert_that(self.fulfilled, is_(True),
            "expected %s to be called %s %s times, but was %s" %
            (name, self.checktype(), self.expected_ccount, self.ccount))

    def checktype(self): return 'exactly'

    def __check_criteria(self):
        if not self.count_ok():
            return False
        return True

    def count_ok(self):
        return self.ccount == self.expected_ccount

    fulfilled = property(__check_criteria)

class MinimumCallCountTracker(InvocationTracker):
    
    def checktype(self): return 'at least'
    
    def __call__(self):
        if self.count_ok():
            return
        InvocationTracker.__call__(self)

def exactly(call_count):
    """ creates a call count expectation of exactly the specified count """
    return InvocationTracker(expected_ccount=call_count)

def once():
    """ creates a call count expectation of exactly one """
    return exactly(1)

def twice():
    """ creates a call count expectation of exactly two """
    return exactly(2)

def at_least(times):
    """ creates a call count expectation for at least 'times' """
    return MinimumCallCountTracker(expected_ccount=times)

def with_(*args, **kwargs):
    """ creates a 'with' matcher for either 'args' or,
        if args is None, for 'kwargs'
    """
    #this is broken!
    for key in kwargs.iterkeys():
        kwargs[key] = with_(kwargs[key])
    [arg_spec, kwarg_spec] = [map(lambda x: is_(x), args) or None, kwargs or None]
    if arg_spec is None:
        return kwarg_spec
    if kwarg_spec is not None:
        return (tuple(arg_spec), kwarg_spec)
    if len(arg_spec) == 1:
        return arg_spec[0]
    else:
        return tuple(arg_spec)

args = with_
stub = TestDouble
mock = MockObject

def mocking(strict=False):
    def wrap(func):
        fncode = func.func_code
        nvars = fncode.co_argcount
        vars = list(fncode.co_varnames[:nvars])
        defaults = list(func.func_defaults)
            
        #if 'strict' in vars:
        #    idx = vars.index('strict')
        #    strict = defaults[idx]
        #    map(lambda list: list.pop(idx), [vars, defaults])
        #else:
        #    strict = False
        
        kwargs = {}
        map(lambda (name, type): configure(name, type, kwargs, strict),
            zip(vars[len(vars) - len(defaults): ], defaults))
        
        def mocking_executor(*args):
            ex = None
            try:
                return func(*args, **kwargs)
            except Exception, e:
                ex = e
                raise e
            finally:
                if not ex:
                    map(lambda (_,v): v.verify_expectations(), kwargs.iteritems())
        
        copy_attrs(mocking_executor, func)
        return mocking_executor
    return wrap

def copy_attrs(target, func):
    target.__doc__ = func.__doc__
    target.__name__ = func.__name__

def configure(name, default, kwargs, strict=False):
    if default is not None:
        kwargs[name] = mock(delegate=default, strict=strict)
    else:
        kwargs[name] = mock(strict=strict)
