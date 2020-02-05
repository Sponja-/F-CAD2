from .base import Class, IPrimitiveType, Object, forward_declarations
from .base import NoneType, none_object, to_primitive_function
from .base import OperatorCall, Constant
from .logic import Bool
from .numerical import Int
from .exceptions import Raise, StopIteration
from typing import List, Type, Dict


class Tuple(IPrimitiveType):
    def __init__(self, elements) -> None:
        self.elements = elements
        self.iter_current = 0
        super().__init__(tuple_class)


def tuple_get_item(this: Tuple, index: Int) -> Type[Object]:
    assert(type(index) is Int)
    return this.elements[index.value]


def tuple_combine(this: Tuple, other: Tuple) -> Tuple:
    return Tuple(this.elements + other.elements)


def tuple_length(this: Tuple) -> Int:
    return Int(len(this.elements))


def tuple_equal(this: Tuple, other: Tuple) -> Bool:
    if len(this.elements) != len(other.elements):
        return Bool(False)
    return Bool(all(OperatorCall("#equal", [Constant(elem1), Constant(elem2)]).eval({}).value
                for elem1, elem2 in zip(this.elements, other.elements)))


def tuple_hash(this: Tuple) -> Int:
    return Int(hash(this.elements))


def tuple_to_bool(this: Tuple) -> Bool:
    return Bool(bool(len(this.elements)))


def tuple_contains(this: Tuple, value: Type[Object]) -> Bool:
    const_value = Constant(value)
    return Bool(any(OperatorCall("#equal", [Constant(elem), const_value]).eval({}).value
                    for elem in this.elements))


def tuple_iter(this: Tuple) -> Tuple:
    this.iter_current = 0
    return this


def tuple_next(this: Tuple) -> Type[Object]:
    if this.iter_current <= len(this.elements):
        result = this.elements[this.iter_current]
        this.iter_current += 1
        return result
    else:
        return Raise(Constant(StopIteration)).eval({})


tuple_class = Class("tuple", {
    "#get_item_left":   to_primitive_function(tuple_get_item),
    "#add_left":        to_primitive_function(tuple_combine),
    "length":           to_primitive_function(tuple_length),
    "#equal":           to_primitive_function(tuple_equal),
    "#hash":            to_primitive_function(tuple_hash),
    "#to_bool":         to_primitive_function(tuple_to_bool),
    "#contains":        to_primitive_function(tuple_contains),
    "#iter":            to_primitive_function(tuple_iter),
    "#next":            to_primitive_function(tuple_next)
}, {})


class Array(IPrimitiveType):
    def __init__(self, elements: List[Type[Object]]) -> None:
        self.elements = elements
        self.iter_current = 0
        super().__init__(array_class)


def array_get_item(this: Array, index: Int) -> Object:
    assert(type(index) is Int)
    return this.elements[index.value]


def array_set_item(this: Array, index: Int, value: Type[Object]) -> Type[Object]:
    assert(type(index) is Int)
    this.elements[index.value] = value
    return value


def array_del_item(this: Array, index: Int) -> Type[Object]:
    assert(type(index) is Int)
    value = this.elements[index.value]
    del this.elements[index.value]
    return value


def array_combine(this: Array, other: Array) -> Array:
    return Array(this.elements + other.elements)


def array_length(this: Array):
    return Int(len(this.elements))


def array_add(this: Array, value: Type[Object]) -> NoneType:
    this.elements.append(value)
    return this


def array_insert(this: Array, index: Int, value: Type[Object]) -> NoneType:
    assert(type(index) is Int)
    this.elements.insert(index, value)
    return this


def array_equal(this: Array, other: Array) -> Bool:  # TODO
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


def array_iter(this: Array) -> Array:
    this.iter_current = 0
    return this


def array_next(this: Array) -> Array:
    if this.iter_current <= len(this.elements):
        result = this.elements[this.iter_current]
        this.iter_current += 1
        return result
    else:
        return Raise(Constant(StopIteration)).eval({})


array_class = Class("array", {
    "#get_item_left":       to_primitive_function(array_get_item),
    "#set_item_0":          to_primitive_function(array_set_item),
    "#del_item_left":       to_primitive_function(array_del_item),
    "#add_left":            to_primitive_function(array_combine),
    "length":               to_primitive_function(array_length),
    "insert":               to_primitive_function(array_insert),
    "add":                  to_primitive_function(array_add),
    "#equal":               to_primitive_function(array_equal),
    "#to_bool":             to_primitive_function(array_to_bool),
    "#contains":            to_primitive_function(array_contains),
    "#iter":                to_primitive_function(array_iter),
    "#next":                to_primitive_function(array_next)
}, {})


forward_declarations["Array"] = Array


class Dictionary(IPrimitiveType):
    def __init__(self, values: Dict[Type[Object], Type[Object]]):
        self.values = values
        super().__init__(dictionary_class)


def dict_get_item(this: Dictionary, index: Type[Object]) -> Type[Object]:
    return this.value[index]


def dict_set_item(this: Dictionary, index: Type[Object], value: Type[Object]) -> Type[Object]:
    this.values[index] = value
    return value


def dict_del_item(this: Dictionary, index: Type[Object]) -> Type[Object]:
    value = this.values[index]
    del this.values[index]
    return value


def dict_combine(this: Dictionary, other: Dictionary) -> Dictionary:
    return Dictionary({**this.values, **other.values})


def dict_update(this: Dictionary, other: Dictionary) -> Dictionary:
    this.values.update(other.values)
    return this


def dict_keys(this: Dictionary) -> Tuple:
    return Tuple(this.values.keys())


def dict_values(this: Dictionary) -> Tuple:
    return Tuple(this.values.values())


def dict_items(this: Dictionary) -> Tuple:
    return Tuple((Tuple(pair) for pair in zip(this.values.keys(), this.values.values())))


def dict_iter(this: Dictionary) -> Tuple:
    keys = this.type.get_method("keys").eval({"this": this})
    return keys.type.get_method("#iter").eval({"this": keys})


dictionary_class = Class("dictionary", {
    "#get_item_left":       to_primitive_function(dict_get_item),
    "#set_item_0":          to_primitive_function(dict_set_item),
    "#del_item_left":       to_primitive_function(dict_del_item),
    "#add_left":            to_primitive_function(dict_combine),
    "update":               to_primitive_function(dict_update),
    "keys":                 to_primitive_function(dict_keys),
    "values":               to_primitive_function(dict_values),
    "items":                to_primitive_function(dict_items),
    "dict_iter":            to_primitive_function(dict_iter),
}, {})
