from typing import List, Type
from base import Class, IPrimitiveType, Object, forward_declarations
from base import none_object, to_primitive_function
from numerical import Int


def array_get_item(this, index):
    assert(type(index) is Int)
    return this.elements[index.value]


def array_set_item(this, index, value):
    assert(type(index) is Int)
    this.elements[index.value] = value
    return none_object


def array_del_item(this, index):
    assert(type(index) is Int)
    del this.elements[index.value]
    return none_object


def array_combine(this, other):
    return Array(this.elements + other.elements)


def array_length(this):
    return Int(len(this.elements))


def array_insert(this, index, value):
    assert(type(index) is Int)
    this.elements.insert(index, value)
    return none_object


def array_add(this, value):
    this.elements.append(value)
    return none_object


def array_pop(this, index):
    assert(type(index) is Int)
    return this.elements.pop(index)


array_class = Class("array", {
    "operator_get_item":      to_primitive_function(array_get_item),
    "operator_set_item":      to_primitive_function(array_set_item),
    "operator_del_item":      to_primitive_function(array_del_item),
    "operator_add_left":      to_primitive_function(array_combine),
    "length":                 to_primitive_function(array_length),
    "insert":                 to_primitive_function(array_insert),
    "add":                    to_primitive_function(array_add),
    "pop":                    to_primitive_function(array_pop)
}, {})


class Array(IPrimitiveType):
    def __init__(self, elements: List[Type[Object]]) -> None:
        self.elements = elements
        super().__init__(array_class)


forward_declarations["Array"] = Array
