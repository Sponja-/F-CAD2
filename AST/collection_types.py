from typing import List, Type
from base import Class, IPrimitiveType, Object, forward_declarations
from base import NoneType, none_object, to_primitive_function
from base import OperatorCall, Constant
from logic import Bool
from numerical import Int


class Array(IPrimitiveType):
    def __init__(self, elements: List[Type[Object]]) -> None:
        self.elements = elements
        super().__init__(array_class)


def array_get_item(this: Array, index: Int) -> Object:
    assert(type(index) is Int)
    return this.elements[index.value]


def array_set_item(this: Array, index: Int, value: Type[Object]) -> NoneType:
    assert(type(index) is Int)
    this.elements[index.value] = value
    return none_object


def array_del_item(this: Array, index: Int):
    assert(type(index) is Int)
    del this.elements[index.value]
    return none_object


def array_combine(this: Array, other: Array) -> Array:
    return Array(this.elements + other.elements)


def array_length(this: Array):
    return Int(len(this.elements))


def array_add(this: Array, value: Type[Object]) -> NoneType:
    this.elements.append(value)
    return none_object


def array_insert(this: Array, index: Int, value: Type[Object]) -> NoneType:
    assert(type(index) is Int)
    this.elements.insert(index, value)
    return none_object


def array_pop(this: Array, index: Int) -> NoneType:
    assert(type(index) is Int)
    return this.elements.pop(index)


def array_equals(this: Array, other: Array) -> Bool:  # TODO
    if len(this.elements) != len(other.elements):
        return Bool(False)
    return Bool(all(OperatorCall("#equal", [Constant(elem1), Constant(elem2)]).eval({}).value
                for elem1, elem2 in zip(this.elements, other.elements)))


def array_to_bool(this: Array) -> Bool:
    return Bool(bool(len(this.elements)))


def array_contains(this: Array, value: Type[Object]) -> Bool:
    const_value = Constant(value)
    return Bool(any(OperatorCall("#equal", [Constant(elem), const_value]).eval({}).value
                    for elem in this.elements))


array_class = Class("array", {
    "#get_item_left":       to_primitive_function(array_get_item),
    "#set_item_0":          to_primitive_function(array_set_item),
    "#del_item_left":       to_primitive_function(array_del_item),
    "#add_left":            to_primitive_function(array_combine),
    "length":               to_primitive_function(array_length),
    "insert":               to_primitive_function(array_insert),
    "add":                  to_primitive_function(array_add),
    "pop":                  to_primitive_function(array_pop),
    "#equal":               to_primitive_function(array_equals),
    "#to_bool":             to_primitive_function(array_to_bool)
}, {})


forward_declarations["Array"] = Array
