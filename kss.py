from typing import Dict, List, Optional, Set
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

        parts = string.replace('ТО\n', 'ТО ').split(' ТО ', 1)
        condition = parts[0]
        self.body = _parse_statement(parts[1], script_globals)

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
        lhs = expand_variables(self.lhs, variables)
        rhs = expand_variables(self.rhs, variables)

        if self.op == '>=':
            return int(lhs) >= int(rhs)
        elif self.op == '<=':
            return int(lhs) <= int(rhs)
        elif self.op == '>':
            return int(lhs) > int(rhs)
        elif self.op == '<':
            return int(lhs) < int(rhs)
        elif self.op == '=':
            return str(lhs) == str(rhs)
        else:
            raise RuntimeError()


def expand_variables(string: str, variables: Dict[str, object], dont_resolve: Set[str] = None) -> str:
    if not isinstance(string, str):
        string = str(string)

    result = ''
    var_name: Optional[str] = None

    if dont_resolve is None:
        dont_resolve = set()

    for char in string:
        if char == '{':
            if var_name is None:
                var_name = ''
            else:
                raise SyntaxError()
        elif char == '}':
            if var_name is None:
                raise SyntaxError()

            if var_name in dont_resolve:
                var_value = '{' + var_name + '}'
            elif var_name in variables:
                var_value = expand_variables(
                    str(variables.get(var_name, '{' + var_name + '}')),
                    variables,
                    dont_resolve
                )
            else:
                var_value = '{' + var_name + '}'
                dont_resolve.add(var_name)

            result += var_value
            var_name = None
        elif var_name is not None:
            var_name += char
        else:
            result += char

    if var_name is not None:
        raise SyntaxError()

    return result


def _parse_statement(string: str, script_globals: Dict[str, object]) -> Optional[Statement]:
    string = string.strip()

    if len(string) == 0:
        return None

    if string.startswith('ЕСЛИ '):
        return IfStmt(string[len('ЕСЛИ '):], script_globals)
    else:
        return BuiltinFnCallStmt(string, script_globals)


def parse(string: str, script_globals: Dict[str, object]) -> KristyScheduleScript:
    body: List[Statement] = []
    string = string.strip()

    for stmt_string in string.split(';'):
        stmt = _parse_statement(stmt_string, script_globals)

        if stmt:
            body.append(stmt)

    return KristyScheduleScript(string, body)
