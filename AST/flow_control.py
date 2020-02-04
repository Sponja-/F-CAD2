from .base import IComputable, Object, none_object
from .base import forward_declarations, unpack
from .statements import IStatement, StatementList
from .logic import try_bool
from typing import Dict, Type, Optional, List


class IfElseStatement(IStatement):
    def __init__(self,
                 condition: Type[IComputable],
                 if_body: StatementList,
                 else_if_body: Optional[StatementList] = None) -> None:
        self.condition = condition
        self.if_body = if_body

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        if try_bool(self.condition.eval(locals)).value:
            return self.if_body.eval(locals)
        elif self.else_body is not None:
            return self.else_body.eval(locals)


class BreakMarker:
    def __init__(self):
        self.is_return = True


class BreakStatement(IStatement):  # Needs to be returned
    def eval(self, locals: Dict[str, Type[Object]]) -> BreakMarker:
        return BreakMarker()


class ContinueMarker:
    def __init__(self):
        self.is_return = True


class ContinueStatement(IStatement):
    def eval(self, locals: Dict[str, Type[Object]]) -> ContinueMarker:
        return ContinueMarker()


class WhileStatement(IStatement):
    def __init__(self,
                 condition: Type[IComputable],
                 body: StatementList) -> None:
        self.condition = condition
        self.body = body

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        while try_bool(self.condition.eval(locals)).value:
            result = self.body.eval(locals)
            if type(result) is BreakMarker:
                break
            if type(result) is ContinueMarker:
                continue
            if result.is_return or result.is_except:
                return result
        return none_object


class ForStatement(IStatement):
    def __init__(self,
                 iterable: IComputable,
                 iter_vars: List[str],
                 body: StatementList):
        self.iterable = iterable
        self.iter_vars = iter_vars
        self.body = body

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        obj = self.iterable.eval(locals)
        iterator = obj.type.get_method("#iter").operation.eval({"this": obj})
        value = iterator.type.get_method("#next").operation.eval({"this": iterator})
        while type(value) is not forward_declarations["StopIteration"]:
            vars = [value]
            if len(self.iter_vars) > 1:
                vars = unpack(value)
            add_locals = {}
            for name, var in zip(self.iter_vars, vars):
                add_locals[name] = var
            result = self.body.eval({**locals, **add_locals})
            if type(result) is BreakMarker:
                break
            if type(result) is ContinueMarker:
                continue
            if result.is_return or result.is_except:
                return result
        return none_object
