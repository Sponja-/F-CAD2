from base import IComputable, Object, none_object, Variable
from typing import Type, Dict, Iterable, Optional


class Assignment(IComputable):
    def __init__(self, object: Type[IComputable], value: Type[IComputable]) -> None:
        self.object = object
        self.value = value

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        self.object.eval(locals).set_value(self.value.eval(locals))
        return none_object


class Return(IComputable):
    def __init__(self, value: Type[IComputable]):
        self.value = value

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        result = self.value.eval(locals)
        result.is_return = True
        return result


class IStatement(IComputable):
    def exec(self, locals: Dict[str, Type[Object]]) -> Optional[Type[Object]]:
        result = self.eval(locals)
        if result.is_return:
            return result
        return None


class ExprStatement(IComputable):
    def __init__(self, expression: Type[IComputable]):
        self.expression = expression

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        return self.expression.eval(locals)


class StatementList(IComputable):
    def __init__(self,
                 statements: Iterable[Type[IStatement]],
                 scoped: bool = True) -> None:
        self.statements = statements
        self.scoped = scoped

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        old_globals: Dict[str, Object] = {}
        for statement in self.statements:
            if (isinstance(statement.expression, Assignment) and
               isinstance(statement.expression.object, Variable)):
                name = statement.expression.object.name
                old_globals[name] = Variable.table.get(name, None)
            result = statement.exec(locals)
            if result is not None:
                return result
        return none_object
