from base import IComputable, Object, none_object, Variable
from typing import Type, Dict, Iterable


class Assignment(IComputable):
    def __init__(self, object: Type[IComputable], value: Type[IComputable]) -> None:
        self.object = object
        self.value = value

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        self.object.eval(locals).set_value(self.value.eval(locals))
        return none_object


class Return(IComputable):
    def __init__(self, value: Type[IComputable]):
        self.value = value

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        result = self.value.eval(locals)
        result.is_return = True
        return result


class Statement(IComputable):
    def __init__(self, expression: Type[IComputable]):
        self.expression = expression

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        result = self.expression.eval(locals)
        if result.is_return:
            result.is_return = False
            return result
        return None


class StatementList(IComputable):
    def __init__(self,
                 statements: Iterable[Statement],
                 scoped: bool = True) -> None:
        self.statements = statements
        self.scoped = scoped

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        old_globals: Dict[str, Object] = {}
        for statement in StatementList:
            if (isinstance(statement.expression, Assignment) and
               isinstance(statement.expression.object, Variable)):
                name = statement.expression.object.name
                old_globals[name] = Variable.table.get(name, None)
            result = statement.eval(locals)
            if result is not None:
                return result
        return none_object
