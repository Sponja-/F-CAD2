from .base import IComputable, Object, none_object
from .base import unpack, Variable
from .statements import IStatement, StatementList
from .logic import try_bool
from typing import Type, Optional, List


class IfElseStatement(IStatement):
    def __init__(self,
                 condition: Type[IComputable],
                 if_body: StatementList,
                 else_if_body: Optional[StatementList] = None) -> None:
        self.condition = condition
        self.if_body = if_body

    def eval(self, scope_path: tuple) -> Type[Object]:
        if try_bool(self.condition.eval(scope_path)).value:
            return self.if_body.eval(scope_path)
        elif self.else_body is not None:
            return self.else_body.eval(scope_path)


class BreakMarker:
    def __init__(self):
        self.is_return = True


class BreakStatement(IStatement):  # Needs to be returned
    def eval(self, scope_path: tuple) -> BreakMarker:
        return BreakMarker()


class ContinueMarker:
    def __init__(self):
        self.is_return = True


class ContinueStatement(IStatement):
    def eval(self, scope_path: tuple) -> ContinueMarker:
        return ContinueMarker()


class WhileStatement(IStatement):
    def __init__(self,
                 condition: Type[IComputable],
                 body: StatementList) -> None:
        self.condition = condition
        self.body = body

    def eval(self, scope_path: tuple) -> Type[Object]:
        while try_bool(self.condition.eval(scope_path)).value:
            result = self.body.eval(scope_path)
            if type(result) is BreakMarker:
                break
            if type(result) is ContinueMarker:
                continue
            if result.is_return or result.is_except:
                return result
        return none_object


class ForStatement(IStatement):
    def __init__(self,
                 iter_vars: List[str],
                 iterable: IComputable,
                 body: StatementList):
        self.iter_vars = iter_vars
        self.iterable = iterable
        self.body = body

    def eval(self, scope_path: tuple) -> Type[Object]:
        for value in self.iterable.eval(scope_path):
            vars = [value]
            if len(self.iter_vars) > 1:
                vars = unpack(value)
            for name, var in zip(self.iter_vars, vars):
                Variable(name).set_value(scope_path, var)
            result = self.body.eval(scope_path)
            if type(result) is BreakMarker:
                break
            if type(result) is ContinueMarker:
                continue
            if result.is_return or result.is_except:
                return result
        return none_object
