from .base import Object, IComputable, IPrimitiveType, Class, ConstructorCall
from .base import Variable, create_none, register_class, Constant
from .statements import StatementList
from typing import Type, Optional


class RaiseStatement(IComputable):
    def __init__(self, value: IComputable) -> None:
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        result = self.value.eval(scope_path)
        raise result


class TryCatch(IComputable):
    def __init__(self,
                 try_body: StatementList,
                 except_name: str,
                 catch_body: StatementList,
                 finally_body: Optional[StatementList]) -> None:
        self.try_body = try_body
        self.except_name = except_name
        self.catch_body = catch_body
        self.finally_body = finally_body

    def eval(self, scope_path: tuple) -> Type[Object]:
        catch_result = None
        finally_result = None
        try:
            result = self.try_body.eval(scope_path)
        except Exception:
            Variable(self.except_name).set_value(scope_path, result)
            catch_result = self.catch_body.eval(scope_path)
        finally:
            if result.finally_body is not None:
                finally_result = self.finally_body.eval(scope_path)
        return (catch_result if catch_result.is_return else
                finally_result if catch_result.is_return else
                create_none())


class StopIteration(IPrimitiveType, Exception):
    def __init__(self):
        super().__init__(StopIteration_class)


StopIteration_class = Class("StopIteration", {})


def raise_stop_iter():
    return RaiseStatement(ConstructorCall(Constant(StopIteration_class), [])).eval(())


register_class("StopIteration", StopIteration, StopIteration_class)
