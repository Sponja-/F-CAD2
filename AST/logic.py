from .base import Class, IPrimitiveType, forward_declarations, Object
from .base import IComputable, to_primitive_function
from typing import Dict, Type


class Bool(IPrimitiveType):
    def __init__(self, value: bool) -> None:
        self.value = value
        super().__init__(bool_class)


def try_bool(obj: Type[Object]):
    if type(obj) is Bool:
        return obj
    if obj.type.has_method("#to_bool"):
        return obj.type.get_method("#to_bool").operation.eval({"this": obj})
    raise f"Could not convert {obj} to bool"


class AndOperation(IComputable):
    def __init__(self, left: IComputable, right: IComputable) -> None:
        self.left = left
        self.right = right

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        left_obj = self.left.eval(locals)
        left_bool = try_bool(left_obj)
        if not left_bool.value:
            return left_obj
        return self.right.eval(locals)


class OrOperation(IComputable):
    def __init__(self, left: IComputable, right: IComputable) -> None:
        self.left = left
        self.right = right

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        left_obj = self.left.eval(locals)
        left_bool = try_bool(left_obj)
        if left_bool.value:
            return left_obj
        return self.right.eval(locals)


class NotOperation(IComputable):
    def __init__(self, value: IComputable) -> None:
        self.value = value

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        obj = self.value.eval(locals)
        return Bool(not try_bool(obj).value)


def bool_equal(this: Bool, other: Bool) -> Bool:
    return Bool(this.value == other.value)


def bool_not_equal(this: Bool, other: Bool) -> Bool:
    return Bool(this.value != other.value)


bool_class = Class("bool", {
    "#equal":       to_primitive_function(bool_equal),
    "#not_equal":   to_primitive_function(bool_not_equal)
}, {})


forward_declarations["Bool"] = Bool
