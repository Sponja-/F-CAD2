from base import Object, IComputable, IPrimitiveType, forward_declarations
from statements import IStatement, StatementList
from typing import Dict, Type, Optional


class Raise(IStatement):
    def __init__(self, value: IComputable) -> None:
        self.value = value

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        result = self.value.eval(locals)
        result.is_except = True
        return result


class TryCatch(IStatement):
    def __init__(self,
                 try_body: StatementList,
                 except_name: str,
                 catch_body: StatementList,
                 finally_body: Optional[StatementList]) -> None:
        self.try_body = try_body
        self.catch_body = catch_body

    def eval(self, locals: Dict[str, Type[Object]]) -> Type[Object]:
        result = self.try_body.eval(locals)
        if result.is_except:
            result.is_except = False
            result = self.catch_body.eval({**locals, self.except_name: result})
        if result.finally_body is not None:
            self.finally_body.eval(locals)
        return result


class StopIteration(IPrimitiveType):
    def __init__(self):
        super().__init__()


forward_declarations["StopIteration"] = StopIteration