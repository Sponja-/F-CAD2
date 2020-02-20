from .base import Class, forward_declarations, register_class
from .base import to_primitive_function, IPrimitiveType, Object, create_none
from .logic import Bool
from typing import Union, Callable, Type
from functools import wraps


class Numerical(IPrimitiveType):
    def __init__(self, value: Union[int, float], *args, **kwargs) -> None:
        self.value = value
        super().__init__(*args, **kwargs)


class Int(Numerical):
    def __init__(self, value: int = 0) -> None:
        super().__init__(value, int_class)


class Float(Numerical):
    def __init__(self, value: float = 0) -> None:
        super().__init__(value, float_class)


def numerical_compatible(fn: Callable):
    @wraps(fn)
    def numerical_compatible_fn(this: Int, other):
        assert(type(other) in [Int, Float, Bool])
        result = fn(this.value, other.value)
        if type(result) is int:
            return Int(result)
        elif type(result) is float:
            return Float(result)
        elif type(result) is bool:
            return Bool(result)
    return numerical_compatible_fn


def numerical_to_bool(this: Type[Numerical]) -> Bool:
    return Bool(bool(this.value))


def numerical_hash(this: Type[Numerical]) -> Int:
    return Int(hash(this.value))


def numerical_to_string(this: Type[Numerical]):
    return forward_declarations["string"](str(this.value))


def int_constructor(this: Int, arg: Type[Object]) -> Type[Object]:
    this.value = int(arg.call("#to_int").value)
    return create_none()


def float_constructor(this: Int, arg: Type[Object]) -> Type[Object]:
    this.value = float(arg.call("#to_float").value)
    return create_none()


def static_int_call(this: Class, arg: Type[Object]) -> Int:
    return arg.call("#to_int")


def static_float_call(this: Class, arg: Type[Object]) -> Float:
    return arg.call("#to_float")


numerical_methods = {
    "#add":                 (lambda x, y: x + y),
    "#substract_left":      (lambda x, y: x - y),
    "#multiply":            (lambda x, y: x * y),
    "#divide_left":         (lambda x, y: x / y),
    "#modulo_left":         (lambda x, y: x % y),
    "#exponent_left":       (lambda x, y: x ** y),
    "#equal":               (lambda x, y: x == y),
    "#not_equal":           (lambda x, y: x != y),
    "#lesser_left":         (lambda x, y: x < y),
    "#lesser_equal_left":   (lambda x, y: x <= y),
    "#greater_left":        (lambda x, y: x > y),
    "#greater_equal_left":  (lambda x, y: x >= y),
    "#substract_right":     (lambda x, y: y - x),
    "#divide_right":        (lambda x, y: y / x),
    "#modulo_right":        (lambda x, y: y % x),
    "#exponent_right":      (lambda x, y: y ** x),
    "#lesser_right":        (lambda x, y: y < x),
    "#lesser_equal_right":  (lambda x, y: y <= x),
    "#greater_right":       (lambda x, y: y > x),
    "#greater_equal_right": (lambda x, y: y >= x)

}

int_methods = {name: to_primitive_function(numerical_compatible(method))
               for name, method in numerical_methods.items()}
int_methods["constructor"] = to_primitive_function(int_constructor)
int_methods["#to_bool"] = to_primitive_function(numerical_to_bool)
int_methods["#hash"] = to_primitive_function(numerical_hash)
int_methods["#to_string"] = to_primitive_function(numerical_to_string)


int_class = Class("int", int_methods, {
    "#call":        to_primitive_function(static_int_call)
})

float_methods = {name: to_primitive_function(numerical_compatible(method))
                 for name, method in numerical_methods.items()}
float_methods["constructor"] = to_primitive_function(float_constructor)
float_methods["#to_bool"] = to_primitive_function(numerical_to_bool)
float_methods["#hash"] = to_primitive_function(numerical_hash)
float_methods["#to_string"] = to_primitive_function(numerical_to_string)


float_class = Class("float", float_methods, {
    "#call":        to_primitive_function(static_float_call)
})

register_class("int", Int, int_class)
register_class("float", Float, float_class)
