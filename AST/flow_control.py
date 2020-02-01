from base import IComputable, Object
from statements import IStatement, StatementList
from logic import try_bool
from typing import Dict, Type, Optional


class IfElseStatement(IStatement):
    def __init__(self,
                 condition: IComputable,
                 body: StatementList,
                 else_body: Optional[StatementList] = None) -> None:
        self.condition = condition
        self.body = body

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        if try_bool(self.condition.eval(locals)).value:
            return self.body.eval(locals)
        elif self.else_body is not None:
            return self.else_body.eval(locals)


class WhileStatement(IStatement):
    def __init__(self, condition: IComputable, body: StatementList) -> None:
        self.condition = condition
        self.body = body

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        while try_bool(self.condition.eval(locals)).value:
            result = self.body.eval(locals)
            if result.is_return:  # TODO: Implement break
                return result
