from AST.base import ClassCreate, FunctionCreate, Assignment, Variable
from AST.base import IAssignable, FunctionCall, OperatorCall, MemberAccess
from AST.base import ConstructorCall, UnpackOperation, Constant, Destructuring
from AST.statements import StatementList, Statement, ReturnStatement
from AST.exceptions import RaiseStatement
from AST.logic import NotOperation, OrOperation, AndOperation
from AST.flow_control import BreakStatement, ContinueStatement, ConditionalExpression
from AST.flow_control import ConditionalStatement, WhileStatement, ForStatement
from AST.flow_control import ListComprehension, ContainsOperation
from AST.numerical import Int, Float
from AST.collection_types import ItemAccess, TupleConstant, ArrayConstant, DictionaryConstant
from AST.text import String
from typing import Any

from tokenizer import Tokenizer, TokenType


class Parser:

    comparation_operators = ('==', '!=', '<', '<=', '>', '>=')

    operator_names = {
        '==':   "#equal",
        '!=':   "#not_equal",
        '<':    "#lesser",
        '<=':   "#lesser_equal",
        '>':    "#greater",
        '>=':   "#greater_equal",
        'in':   "#contains",
        '+':    "#add",
        '-':    "#substract",
        '*':    "#multiply",
        '/':    "#divide",
        '%':    "#modulo",
        '^':    "#exponent"
    }

    def __init__(self, text):
        self.tokens = Tokenizer(text).get_token_list()
        self.pos = 0
        self.show_errors = True

    def error(self, message=""):
        if self.show_errors:
            print(f"Error on {self.token} at pos {self.pos}:\n\t{message}")
        raise SyntaxError

    @property
    def token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        self.pos -= 1
        self.error("Unexpected EOF")

    @property
    def next_token(self):
        if self.pos < len(self.tokens) - 1:
            return self.tokens[self.pos + 1]
        self.error("Unexpected EOF")

    @property
    def prev_token(self):
        if self.pos > 0:
            return self.tokens[self.pos - 1]
        self.error("Expected previous token")

    def eat(self, type: TokenType, value: Any = None):
        if self.token.type != type or (value is not None and self.token.value != value):
            self.error(f"Expected {type}" + (f"of value {value}" if value is not None else ""))
        else:
            value = self.token.value
            self.pos += 1
            return value

    def find_next(self, type: TokenType):
        start_pos = self.pos
        while self.token.type != type:
            self.pos += 1
        result = self.pos
        self.pos = start_pos
        return result

    def statement_block(self):
        if self.token.value != '{':
            return self.statement()
        self.eat(TokenType.GROUP)
        result = self.statement_list()
        self.eat(TokenType.GROUP, '}')
        return result

    def statement_list(self):
        s = self.statement()
        result = [s] if s is not None else []
        while self.token.value != '}' and self.token.type != TokenType.EOF:
            if self.prev_token.value != '}':
                self.eat(TokenType.SEMICOLON)
            s = self.statement()
            if s is not None:
                result.append(s)
        return StatementList(result)

    def statement(self):
        return self.special_statement()

    def special_statement(self):
        if self.token.value == "return":
            return ReturnStatement(self.expr_statement())
        if self.token.value == "raise":
            return RaiseStatement(self.expr_statement())
        if self.token.value == "break":
            self.eat(TokenType.KEYWORD)
            self.eat(TokenType.SEMICOLON)
            return BreakStatement()
        if self.token.value == "continue":
            self.eat(TokenType.KEYWORD)
            self.eat(TokenType.SEMICOLON)
            return ContinueStatement()
        return self.flow_statement()

    def name_list(self):
        names = [self.eat(TokenType.NAME)]
        while self.token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            names.append(self.eat(TokenType.NAME))
        return names

    def flow_statement(self):
        if self.token.type == TokenType.KEYWORD:
            if self.token.value == "if":
                self.eat(TokenType.KEYWORD)
                self.eat(TokenType.GROUP, '(')
                condition = self.expr()
                self.eat(TokenType.GROUP, ')')
                body = self.statement_block()
                if self.token.value == "else":
                    self.eat(TokenType.KEYWORD)
                    else_body = self.statement_block()
                else:
                    else_body = None
                return ConditionalStatement(condition, body, else_body)
            if self.token.value == "while":
                self.eat(TokenType.KEYWORD)
                self.eat(TokenType.GROUP, '(')
                condition = self.expr()
                self.eat(TokenType.GROUP, ')')
                body = self.statement_block()
                return WhileStatement(condition, body)
            if self.token.value == "for":
                self.eat(TokenType.KEYWORD)
                self.eat(TokenType.GROUP, '(')
                names = self.name_list()
                self.eat(TokenType.KEYWORD, "in")
                iterable = self.expr()
                self.eat(TokenType.GROUP, ')')
                body = self.statement_block()
                return ForStatement(names, iterable, body)
        return self.expr_statement()

    def expr_statement(self):
        result = Statement(self.expr())
        self.eat(TokenType.SEMICOLON)
        return result

    def expr(self):
        return self.class_definition()

    def class_definition(self):
        if self.token.value == "class":
            self.eat(TokenType.KEYWORD)
            name = self.eat(TokenType.NAME)
            if self.token.value == "extends":
                self.eat("KEYWORD")
                parent_name = self.eat(TokenType.NAME)
            else:
                parent_name = None
            methods = {}
            statics = {}
            self.eat(TokenType.GROUP, '{')
            while self.token.value != '}' and self.token.type != TokenType.EOF:
                if self.token.value == "static":
                    self.eat(TokenType.KEYWORD)
                    definition = self.function_definition()
                    statics[definition.object.name] = definition.value
                elif self.token.value == "function":
                    definition = self.function_definition()
                    methods[definition.object.name] = definition.value
                else:
                    assignment = self.assignment()
                    statics[assignment.object.name] = assignment.value
            return Assignment(Variable(name), ClassCreate(name, methods, statics, parent_name))
        return self.function_definition()

    def function_definition(self):
        if self.token.value == "function":
            self.eat(TokenType.KEYWORD)
            name = self.eat(TokenType.NAME)
            self.eat(TokenType.GROUP, '(')
            var_arg_name = None
            if self.token.type == TokenType.ELLIPSIS:
                names = []
                var_arg_name = self.eat(TokenType.NAME)
            else:
                names = [self.eat(TokenType.NAME)]
                while self.token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    if self.token.type == TokenType.ELLIPSIS:
                        self.eat(TokenType.ELLIPSIS)
                        var_arg_name = self.eat(TokenType.NAME)
                        break
                    else:
                        names.append(self.eat(TokenType.NAME))
            self.eat(TokenType.GROUP, ')')
            body = self.statement_block()
            return Assignment(Variable(name), FunctionCreate(body, names, var_arg_name))
        return self.assignment_expr()

    def assignment(self):
        var = self.list_comp_expr()
        if self.token.value == '=' and isinstance(var, IAssignable):
            self.eat(TokenType.OPERATOR)
            expr = self.assignment()
            return Assignment(var, expr)
        return var

    def list_comp_expr(self):
        operation = self.conditional_expr()
        if self.token.type == TokenType.SEPARATOR:
            self.eat(TokenType.KEYWORD)
            iter_vars = self.name_list()
            self.eat(TokenType.KEYWORD, "in")
            iterable = self.expr()
            if self.token.type == TokenType.COMMA:
                conditions = self.expr_list()
            else:
                conditions = []
            return ListComprehension(operation, iter_vars, iterable, conditions)
        return operation

    def conditional_expr(self):
        condition = self.logic_expr()
        if self.token.type == TokenType.QUESTION:
            self.eat(TokenType.QUESTION)
            if_expr = self.logic_expr()
            self.eat(TokenType.COLON)
            else_expr = self.logic_expr()
            return ConditionalExpression(condition, if_expr, else_expr)
        return condition

    def or_expr(self):
        value = self.and_expr()
        while self.token.value == "or":
            self.eat(TokenType.OPERATOR)
            value = OrOperation(value, self.and_expr())
        return value

    def and_expr(self):
        value = self.not_expr()
        while self.token.value == "and":
            self.eat(TokenType.OPERATOR)
            value = AndOperation(value, self.not_expr())
        return value

    def not_expr(self):
        if self.token.value == "not":
            self.eat(TokenType.OPERATOR)
            return NotOperation(self.not_expr())
        return self.in_expr()

    def in_expr(self):
        value = self.comparation_expr()
        if self.token.value == "in":
            self.eat(TokenType.OPERATOR)
            return ContainsOperation(value, self.expr())
        return value

    def comparation_expr(self):
        value = self.term_expr()
        if self.token.value in Parser.comparation_operators:
            operator = self.token.value
            self.eat(TokenType.OPERATOR)
            last_operand = self.term_expr()
            value = OperatorCall(Parser.operator_names[operator], [value, last_operand])
            while self.token.value in Parser.comparation_operators:  # Allows a < x < b
                operator = self.token.value
                self.eat(TokenType.OPERATOR)
                op = self.term_expr()
                value = AndOperation(value, OperatorCall(Parser.operator_names[operator], [last_operand, op]))
                last_operand = op
        return value

    def term_expr(self):
        value = self.factor_expr()
        while self.token.value in ('+', '-'):
            operator = self.token.value
            self.eat(TokenType.OPERATOR)
            value = OperatorCall(Parser.operator_names[operator], [value, self.factor_expr()])
        return value

    def factor_expr(self):
        value = self.power_expr()
        while self.token.value in ('*', '/', '%'):
            operator = self.token.value
            self.eat(TokenType.OPERATOR)
            value = OperatorCall(Parser.operator_names[operator], [value, self.power_expr()])
        return value

    def power_expr(self):
        value = self.trailer_expr()
        while self.token.value == '^':
            self.eat(TokenType.OPERATOR)
            value = OperatorCall("#exponent", [value, self.trailer_expr()])
        return value

    def expr_list(self, **kwargs):
        with_kwargs = kwargs.get("with_kwargs", False)
        start_symbol = self.token.value
        result = [self.expr()]
        kwarg_lines = []
        while self.token.type == TokenType.COMMA:
            if (with_kwargs and
               isinstance(result[-1], Assignment) and
               isinstance(result[-1].object, Variable) and
               start_symbol != '('):
                kv_pair = result.pop()
                kwarg_lines.append(String(kv_pair.object.name), kv_pair.value)
            self.eat(TokenType.COMMA)
            start_symbol = self.token.value
            result.append(self.expr())
        return result if not with_kwargs else (result, DictionaryConstant(kwarg_lines))

    def trailer_expr(self):
        value = self.atom()
        while self.token.value in ('(', '[') or self.token.type == TokenType.DOT:
            if self.token.type == TokenType.DOT:
                self.eat(TokenType.DOT)
                member_name = self.token.value
                self.eat(TokenType.NAME)
                return MemberAccess(value, member_name)
            if self.token.value == '(':
                self.eat(TokenType.GROUP)
                args, kwargs = self.expr_list(with_kwargs=True)
                value = FunctionCall(value, args, kwargs)
            if self.token.value == '[':
                self.eat(TokenType.GROUP)
                arguments = self.expr_list()
                self.eat(TokenType.GROUP, ']')
                value = ItemAccess(value, arguments)
        return value

    def atom(self):
        token = self.token

        if token.value == "new":
            self.eat(TokenType.KEYWORD)
            type = self.atom()
            self.eat(TokenType.GROUP, '(')
            args, kwargs = self.expr(with_kwargs=True)
            self.eat(TokenType.GROUP, ')')
            return ConstructorCall(type, args, kwargs)

        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Constant(Int(token.value)) if type(token.value) is int else Constant(Float(token.value))

        if token.type == TokenType.NAME:
            self.eat(TokenType.NAME)
            return Variable(token.value)

        if token.type == TokenType.STRING:
            self.eat(TokenType.STRING)
            return Constant(String(token.value))

        if token.type == TokenType.GROUP:
            if token.value == '(':
                self.eat(TokenType.GROUP)
                value = self.expr()
                if self.token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    value = TupleConstant([value] + self.expr_list())
                self.eat(TokenType.GROUP, ')')
                return value

            if token.value == '[':
                self.eat(TokenType.GROUP)
                value = ArrayConstant(self.expr_list())
                self.eat(TokenType.GROUP, ']')
                return value

            if token.value == '{':
                self.eat(TokenType.GROUP)
                key = self.expr()
                if isinstance(key, Variable):
                    if self.token.type == TokenType.COMMA:
                        self.eat(TokenType.COMMA)
                        key = Destructuring([key.name] + self.name_list())
                        self.eat(TokenType.GROUP, '}')
                        return key
                    elif self.token.key == '}':
                        key = Destructuring([key.name])
                        self.eat(TokenType.GROUP)
                        return key
                self.eat(TokenType.COLON)
                value = self.expr()
                lines = [(key, value)]
                while self.token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    key = self.expr()
                    if isinstance(key, UnpackOperation):
                        lines.append((key,))
                    else:
                        self.eat(TokenType.COLON)
                        value = self.expr()
                        lines.append((key, value))
                return DictionaryConstant(lines)

        if token.type == TokenType.ELLIPSIS:
            return UnpackOperation(self.expr())

        return None
