from .base import IPrimitiveType, Class, to_primitive_function
from .base import register_primitive, Object, none_object, Constant
from .logic import Bool
from .numerical import Int, Float
from .exceptions import RaiseStatement, StopIteration
from typing import Type


class String(IPrimitiveType):
    def __init__(self, value: str = None):
        self.value = value
        self.iter_current = 0
        super().__init__(string_class)

    def __repr__(self):
        return self.value


def string_constructor(this: String, arg: Type[Object]):
    this.value = arg.call("#to_string").value
    return none_object


def string_get_item(this: String, index: Int) -> String:
    assert(type(index) is Int)
    return String(this.value[index.value])


def string_set_item(this: String, index: Int, value: String) -> String:
    assert(type(index) is Int)
    assert(len(value.value) == 1)
    this.value[index.value] = value.value
    return value


def string_del_item(this: String, index: Int) -> String:
    assert(type(index) is Int)
    result = String(this.value[index.value])
    del this.value[index.value]
    return result


def string_combine(this: String, other: String) -> String:
    return String(this.value + other.value)


def string_equal(this: String, other: String):
    return Bool(this.value == other.value)


def string_not_equal(this: String, other: String):
    return Bool(this.value != other.value)


def string_to_int(this: String) -> Int:
    return Int(int(this.value))


def string_to_float(this: String) -> Float:
    return Float(float(this.value))


def string_to_string(this: String) -> String:
    return String(this.value)


def string_hash(this: String) -> Int:
    return Int(hash(this.value))


def string_iter(this: String) -> String:
    this.iter_current = 0
    return this


def string_next(this: String) -> String:
    if this.iter_current <= len(this.elements):
        result = String(this.elements[this.iter_current])
        this.iter_current += 1
        return result
    else:
        return RaiseStatement(Constant(StopIteration)).exec(())


def static_string_call(this: Class, arg: Type[Object]) -> String:
    return arg.call("#to_string")


string_class = Class("string", {
    "constructor":      to_primitive_function(string_constructor),
    "#get_item":        to_primitive_function(string_get_item),
    "#set_item":        to_primitive_function(string_set_item),
    "#del_item":        to_primitive_function(string_del_item),
    "#append_left":     to_primitive_function(string_combine),
    "#equal":           to_primitive_function(string_equal),
    "#not_equal":       to_primitive_function(string_not_equal),
    "#to_int":          to_primitive_function(string_to_int),
    "#to_float":        to_primitive_function(string_to_float),
    "#to_string":       to_primitive_function(string_to_string),
    "#hash":            to_primitive_function(string_hash),
    "#iter":            to_primitive_function(string_iter),
    "#next":            to_primitive_function(string_next)
}, {
    "#call":            to_primitive_function(static_string_call)
})

register_primitive("string", String, string_class)
