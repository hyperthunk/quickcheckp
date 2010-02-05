#!/usr/bin/env python

from unittest import TestCase

import sys
from functools import partial
import qc
from qc import *
from commons.matchers import matcher, is_, equal_to, assert_that, greater_than, instance_of, has_item, has_key
forall.verbose = '-q' in sys.argv
forall = partial(forall, tries=250)

from nose.plugins.attrib import attr

is_callable = matcher(callable)

@attr(assumes=True)
def test_assuming_kwargs():
    @forall(i=integers(high=10), s=strings)
    @assuming(i=greater_than(11), s=instance_of(basestring))
    def example(i):
        assert i > 11 #would fail if run....
        assert isinstance(s, int) #would also fail...
    example()

class MyException(Exception): pass

@attr(assumes=True)
def test_assumption_failure_disable_test_function():
    @assuming(instance_of(int))
    def example(i):
        raise MyException('we did not intend to run this code!!!')
    try:
        example(123)
        raise Exception('expected MyException to be thrown but was not...')
    except MyException:
        pass
    try:
        example('this should raise an assumption failure exception')
    except qc.AssumptionFalsified:
        pass

@attr(tests_runner=True)
def test_generative_forall():
    @qc.forall_lazy(tries=10, i=integers)
    def check_func(i):
        assert isinstance(i, int)
    for (fn, kw) in check_func():
        print 'checking %s' % fn.__name__
        assert_that(fn, is_callable)
        assert_that(kw, has_key('i'))

@qc.forall_lazy(i=integers)
def check_generator_in_use(i):
    assert_that(i, instance_of(int))

@attr(tests_runner=True)
def test_generator_in_use():
    for testcase in check_generator_in_use():
        yield testcase

@forall(i=integers)
def test_integers(i):
    assert type(i) == int
    assert i >= 0 and i <= 100

@forall(l=lists(items=integers))
def test_a_int_list(l):
    assert type(l) == list

@forall(ul=lists(items=unicodes))
def test_unicodes_list(ul):
    assert type(ul) == list
    if len(ul):
        assert type(ul[0]) == unicode

@forall(l=lists(items=integers, size=(10, 50)))
def test_lists_size(l):
    assert len(l) <= 50 and len(l) >= 10

@forall(u=unicodes)
def test_unicodes(u):
    assert type(u) == unicode

@forall(u=unicodes(size=(1,1)))
def test_unicodes_size(u):
    assert len(u) == 1

def random_int_unicode_tuple():
    return lambda: (evaluate(integers), evaluate(unicodes))

@forall(l=lists(items=random_int_unicode_tuple))
def test_a_tupled_list(l):
    for x in l:
        assert type(x[0]) == int and type(x[1]) == unicode

@forall(x=integers, y=integers)
def test_addition_associative(x, y):
    assert x + y == y + x

@forall(l=lists)
def test_reverse_reverse(l):
    assert list(reversed(list(reversed(l)))) == l

@forall(c=characters)
def test_characters(c):
    assert len(c) == 1

@forall(d=dicts(items=unicodes, values=integers))
def test_dicts(d):
    for x, y in d.iteritems():
        assert type(x) == unicode
        assert type(y) == int

@forall(d=dicts(items=unicodes, values=lists, size=(2, 2)))
def test_dicts_size(d):
    assert len(d) == 2
    for x, y in d.iteritems():
        assert type(x) == unicode
        assert type(y) == list

class BaseX(object): pass

@forall(t=classes(bases=(BaseX,)))
def test_type_generation_honors_bases(t):
    assert_that(t.__bases__,    has_item(BaseX))
    assert_that(t(),            instance_of(BaseX))

#@forall()
#def test_dict_preserved_during_type_generation(t):
#    pass

@forall(p=pairs(left=integers, right=strings))
def test_pairs(p):
    assert_that(len(p), 2)
    (l,r) = p
    assert_that(l, instance_of(int))
    assert_that(r, instance_of(str))
