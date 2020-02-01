from typing import List, Type
from base import Class, IPrimitiveType, Object, forward_declarations


array_class = Class("array", {}, {})


class Array(IPrimitiveType):
    def __init__(self, elements: List[Type[Object]]) -> None:
        self.elements = elements
        super().__init__(array_class)


forward_declarations["Array"] = Array
