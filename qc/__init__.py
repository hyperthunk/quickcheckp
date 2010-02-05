#!/usr/bin/env python
"""
Taken from http://github.com/dbravender/gp_through_unit_tests.
Modifications/additions by Tim Watson.
"""

import string
import random
import types
import os
from functools import partial
from commons.matchers import kwmatch

__all__ = (
    'evaluate',
    'integers',
    'strings',
    'lists',
    'tuples',
    'pairs',
    'sets',
    'stubs',
    'classes',
    'dicts',
    'unicodes',
    'characters',
    'assuming',
    'forall',
    'forall_lazy',
    'NewClassWrapper'
)

def evaluate(lazy_value):
    if isinstance(lazy_value, NewClassWrapper):
        return lazy_value.gen()
    while hasattr(lazy_value, '__call__'):
        lazy_value = lazy_value()
    return lazy_value

def integers(low=0, high=100):
    return lambda: random.randint(low, high)

def strings(low=0, high=100, letters=True, digits=True):
    strall = letters and string.letters or '' + \
             digits and string.digits or ''
    return lambda: "".join(random.sample(strall, min(len(strall), \
                                        random.randint(low, high))))

def lists(items=integers, size=(0, 100)):
    return lambda: [evaluate(items) \
                    for _ in xrange(random.randint(size[0], size[1]))]

def tuples(items=integers, size=2):
    def gen_tuple():
        return tuple([evaluate(items) for _ in xrange(0, size)])
    return gen_tuple

#pairs = partial(tuples, size=2)
def pairs(left=integers,right=integers):
    def gen_pair():
        return (evaluate(left),evaluate(right))
    return gen_pair

def sets(items=integers, size=(0, 100)):
    return lambda: set([evaluate(items) \
                        for _ in xrange(random.randint(size[0], size[1]))])
    
def stubs(cls=None, **kwargs):
    if cls:
        Stub = cls
    else:
        class Stub(object): pass
    def stub():
        obj = Stub()
        for (k,v) in kwargs.items():
            setattr(obj, k, evaluate(v))
        return obj
    return stub

class NewClassWrapper(object):
    def __init__(self, generator):
        self.gen = generator

    def __call__(self, *args, **kwargs):
        return evaluate(self.gen)

def classes(name=strings(low=2, high=20, letters=True, digits=False), bases=(object,), dict={}):
    def newclass():
        return type('Class_%s' % name(), bases, {})
    return NewClassWrapper(newclass)

def dicts(items=integers, values=integers, size=(0, 100)):
    def fun():
        x = {}
        for _ in xrange(random.randint(size[0], size[1])):
            item = evaluate(items)
            while item in x:
                item = evaluate(items)
            x.update({evaluate(items): evaluate(values)})
        return x
    return fun

def unicodes(size=(0, 100), minunicode=0, maxunicode=255):
    return lambda: u''.join(unichr(random.randint(minunicode, maxunicode)) \
                            for _ in xrange(random.randint(size[0], size[1])))

characters = partial(unicodes, size=(1, 1))

class AssumptionFalsified(Exception): pass

def assuming(predicate=None, **kw):
    def wrap(f):
        def wrapped(*args, **kwargs):
            if predicate is not None:
                match = len(args) > 0 and predicate.matches(*args) or False
            else:
                match = True
            if len(args) > 0 or predicate is None:
                if len(kwargs) > 0:
                    match = match and kwmatch(**kw).matches(**kwargs)
            elif len(kwargs) > 0:
                rules = [ kwargs[name] for name in kwargs.iterkeys() ]
                match = match and predicate.matches(*rules)
            if match:
                return f(*args, **kwargs)
            else:
                raise AssumptionFalsified()
        wrapped.__name__ = f.__name__
        return wrapped
    return wrap

def forall(tries=100, **kwargs):
    def wrap(f):
        def wrapped():
            for i in xrange(tries):
                random_kwargs = (dict((name, evaluate(lazy_value)) \
                                 for (name, lazy_value) in kwargs.iteritems()))
                if forall.verbose or os.environ.has_key('QC_VERBOSE'):
                    from pprint import pprint
                    pprint(random_kwargs)
                try:
                    f(**random_kwargs)
                except AssumptionFalsified:
                    pass
        wrapped.__name__ = f.__name__
        return wrapped
    return wrap
forall.verbose = False # if enabled will print out the random test cases

def forall_lazy(tries=100, **kwargs):
    def wrap(f):
        def wrapped():
            for i in xrange(tries):
                random_kwargs = (dict((name, evaluate(lazy_value)) \
                                 for (name, lazy_value) in kwargs.iteritems()))
                if forall.verbose or os.environ.has_key('QC_VERBOSE'):
                    from pprint import pprint
                    pprint(random_kwargs)
                def test_runner(kw):
                    f(**kw)
                test_runner.description = "test case %i for %s" % (i, f.__name__)
                yield (test_runner, random_kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return wrap
forall_lazy.verbose = False
