from typing import Dict, List
from kristybot import Kristy


class Statement:
    def __init__(self, string: str, script_globals: Dict[str, object]):
        self.string = string
        self.script_globals = script_globals

    def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        pass


class KristyScheduleScript:
    def __init__(self, string: str, body: List[Statement]):
        self.string = string
        self.body: List[Statement] = body
        self.variables: Dict[str, object] = {}

    def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        for stmt in self.body:
            stmt.execute(kristy, chat, variables)

    def __str__(self):
        return self.string

    def __repr__(self):
        return str(self)


class BuiltinFnCallStmt(Statement):
    def __init__(self, string: str, script_globals: Dict[str, object]):
        super().__init__(string, script_globals)

        if string.startswith('ОТПРАВИТЬ ТЕКСТ '):
            self.inner = BuiltinFnCallStmt.SendTextFn(string[len('ОТПРАВИТЬ ТЕКСТ '):], script_globals)
        elif string.startswith('ОТПРАВИТЬ ВЛОЖЕНИЕ '):
            self.inner = BuiltinFnCallStmt.SendAttachmentFn(string[len('ОТПРАВИТЬ ВЛОЖЕНИЕ '):], script_globals)
        elif string.startswith('ВЫПОЛНИТЬ СЦЕНАРИЙ '):
            self.inner = BuiltinFnCallStmt.ExecNamedScriptFn(string[len('ВЫПОЛНИТЬ СЦЕНАРИЙ '):], script_globals)
        elif string.startswith('ПЕРЕМЕННАЯ '):
            self.inner = BuiltinFnCallStmt.VarFn(string[len('ПЕРЕМЕННАЯ '):], script_globals)
        else:
            raise SyntaxError()

    def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        self.inner.execute(kristy, chat, variables)

    class SendTextFn(Statement):
        def __init__(self, string: str, script_globals: Dict[str, object]):
            super().__init__(string, script_globals)

        def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
            msg = expand_variables(self.string, variables)
            kristy.send(2E9+chat, msg)

    class SendAttachmentFn(Statement):
        def __init__(self, string: str, script_globals: Dict[str, object]):
            super().__init__(string, script_globals)

        def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
            attachment_tag = expand_variables(self.string, variables)
            attachment = kristy.db.get_attachment(chat, attachment_tag)
            kristy.send(2E9+chat, attachment["message"], attachment["attachments"])

    class ExecNamedScriptFn(Statement):
        def __init__(self, string: str, script_globals: Dict[str, object]):
            super().__init__(string, script_globals)

        def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
            script_name = expand_variables(self.string, variables)
            kristy.tt_data.named_scripts[chat][script_name].execute(kristy, chat, variables)

    class VarFn(Statement):
        def __init__(self, string: str, script_globals: Dict[str, object]):
            super().__init__(string, script_globals)

            parts = string.split('<-', 1)

            if len(parts) != 2:
                raise SyntaxError()

            self.var_name = parts[0].strip()

            if self.var_name in script_globals:
                raise SyntaxError()

            self.var_value = parts[1].strip()

        def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
            variables[self.var_name] = expand_variables(self.var_value, variables)


class IfStmt(Statement):
    def __init__(self, string: str, script_globals: Dict[str, object]):
        super().__init__(string, script_globals)

        parts = string.split(' ТО ', 1)
        condition = parts[0]
        self.body = BuiltinFnCallStmt(parts[1].strip(), script_globals)

        if condition.count('>=') == 1:
            self.op = '>='
            cmp_sides = condition.split('>=')
        elif condition.count('<=') == 1:
            self.op = '<='
            cmp_sides = condition.split('<=')
        elif condition.count('>') == 1:
            self.op = '>'
            cmp_sides = condition.split('>')
        elif condition.count('<') == 1:
            self.op = '<'
            cmp_sides = condition.split('<')
        elif condition.count('=') == 1:
            self.op = '='
            cmp_sides = condition.split('=')
        else:
            raise SyntaxError()

        if len(cmp_sides) != 2:
            raise SyntaxError()

        self.lhs = cmp_sides[0].strip()
        self.rhs = cmp_sides[1].strip()

    def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        if self._evaluate(kristy, chat, variables):
            self.body.execute(kristy, chat, variables)

    def _evaluate(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        lhs = int(expand_variables(self.lhs, variables))
        rhs = int(expand_variables(self.rhs, variables))

        if self.op == '>=':
            return lhs >= rhs
        elif self.op == '<=':
            return lhs <= rhs
        elif self.op == '>':
            return lhs > rhs
        elif self.op == '<':
            return lhs < rhs
        elif self.op == '=':
            return lhs == rhs
        else:
            raise RuntimeError()


def expand_variables(string: str, variables: Dict[str, object]) -> str:
    for var_name, var_value in variables.items():
        string = string.replace('{' + var_name + '}', expand_variables(str(var_value), variables))

    return string


def parse(string: str, script_globals: Dict[str, object]) -> KristyScheduleScript:
    body: List[Statement] = []
    string = string.strip()

    for stmt in string.split(';'):
        stmt = stmt.strip()

        if len(stmt) == 0:
            continue

        if stmt.startswith('ЕСЛИ '):
            body.append(IfStmt(stmt[len('ЕСЛИ '):], script_globals))
        else:
            body.append(BuiltinFnCallStmt(stmt, script_globals))

    return KristyScheduleScript(string, body)