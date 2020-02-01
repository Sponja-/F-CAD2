from base import Class, Constant, OperatorCall
from base import to_primitive_function, IPrimitiveType
from typing import Union
from functools import wraps
import collection_types


class Numerical(IPrimitiveType):
    def __init__(self, value: Union[int, float], *args, **kwargs) -> None:
        self.value = value
        super().__init__(*args, **kwargs)


class Int(Numerical):
    def __init__(self, value: int) -> None:
        super().__init__(value, int_class)


class Float(Numerical):
    def __init__(self, value: float) -> None:
        super().__init__(value, float_class)


def numerical_compatible(fn):
    @wraps(fn)
    def numerical_compatible_fn(this, *args):
        result = fn(this.value, *[arg.value for arg in args])
        if type(result) is int:
            return Int(result)
        else:
            return Float(result)
    return numerical_compatible_fn


numerical_methods = {
    "operator_add":         (lambda x, y: x + y),
    "operator_substract":   (lambda x, y: x - y),
    "operator_multiply":    (lambda x, y: x * y),
    "operator_divide":      (lambda x, y: x / y),
    "operator_modulo":      (lambda x, y: x % y),
    "operator_exponent":    (lambda x, y: x ** y),
    "operator_opposite":    (lambda x: -x),
    "abs":                  (lambda x: abs(x))
}

int_class = Class("int",
                  {name: to_primitive_function(numerical_compatible(method))
                   for name, method in numerical_methods.items()}, {})

float_class = Class("float",
                    {name: to_primitive_function(numerical_compatible(method))
                     for name, method in numerical_methods.items()}, {})

print(OperatorCall("multiply", [OperatorCall("add", [Constant(Int(7)), Constant(Int(2))]), Constant(Int(2))]).eval({}).value)
