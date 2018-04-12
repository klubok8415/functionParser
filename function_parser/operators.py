import math

import re

from expressions.core import Value
from function_parser.lexis.lexis_element import LexisElement
from function_parser.lexis_helper import startswith, endswith, split
from function_parser.parser import ParsingData


class Operator:
    def parse(self, lexis_string, braces_pairs, element_pattern):
        raise NotImplementedError()

    def get_determinants(self):
        raise NotImplementedError()


class Prefix(Operator):
    TYPE_NAME = "prefix"

    def __init__(self, name, operation):
        self.name = name
        self.operation = operation

    def parse(self, lexis_string, braces_pairs, element_pattern):
        if not startswith(lexis_string, [LexisElement(self.name, Prefix.TYPE_NAME)]):
            return []

        return [ParsingData(
            self.operation,
            [lexis_string[1:]]
        )]

    def get_determinants(self):
        return [
            lambda s: [LexisElement(self.name, Prefix.TYPE_NAME)] if s.startswith(self.name) else []
        ]



class FunctionOperator(Operator):
    def __init__(self, name, operation, args_number):
        self.name = name
        self.operation = operation
        self.args_number = args_number

    def parse(self, lexis_string, braces_pairs, element_pattern):
        converted_name = element_pattern.findall(self.name)

        if startswith(lexis_string, converted_name + ["("]) and endswith(lexis_string, [")"]):
            args = [a for a in split(lexis_string[len(converted_name) + 1:-1], ',')]

            if len(args) == self.args_number:
                return [ParsingData(self.operation, args, [])]
        return []


class Brace(Operator):
    def __init__(self, opening_name, closing_name, operation=None):
        self.opening_name = opening_name
        self.closing_name = closing_name
        self.operation = operation

    def parse(self, lexis_string, braces_pairs, element_pattern):
        converted_opening_name = element_pattern.findall(self.opening_name)
        converted_closing_name = element_pattern.findall(self.closing_name)

        if startswith(lexis_string, converted_opening_name) and endswith(lexis_string, converted_closing_name):
            lexis_string = lexis_string[len(converted_opening_name):-len(converted_closing_name)]

            braces_counter = 0
            if converted_opening_name != converted_closing_name:
                for i in range(len(lexis_string)):
                    if startswith(lexis_string[i:], converted_opening_name):
                        braces_counter += 1
                    elif startswith(lexis_string[i:], converted_closing_name):
                        braces_counter -= 1

                        if braces_counter < 0:
                            return []

            return [ParsingData(
                self.operation,
                [lexis_string]
            )]
        return []


class VariableOperator(Operator):
    TYPE_NAME = "variable"

    def parse(self, lexis_string, braces_pairs, element_pattern):
        if startswith(lexis_string, [LexisElement("x", VariableOperator.TYPE_NAME)]):
            v = Value(0)
            return [ParsingData(v, [], [v])]
        return []

    def get_determinants(self):
        return [
            lambda s: [LexisElement("x", VariableOperator.TYPE_NAME)] if s.startswith("x") else []
        ]


class ConstantOperator(Operator):
    TYPE_NAME = "constant"
    E = "e"
    PI = "pi"

    def parse(self, lexis_string, braces_pairs, element_pattern):
        first_element = lexis_string[0][0]

        if first_element.type != ConstantOperator.TYPE_NAME:
            return []

        if first_element.string == ConstantOperator.E:
            value = math.e
        elif first_element.string == ConstantOperator.PI:
            value = math.pi
        else:
            try:
                value = float(first_element.string)
            except ValueError:
                return []
        return [ParsingData(Value(value), [])]

    @staticmethod
    def constant_determinant(string):
        m = re.match(r'^([\d.]+|' + ConstantOperator.E + '|' + ConstantOperator.PI + ')', string)

        return [] if m is None else [LexisElement(m.group(0), ConstantOperator.TYPE_NAME)]

    def get_determinants(self):
        return [self.constant_determinant]


class InfixOperator(Operator):
    def __init__(self, name, operation):
        self.name = name
        self.operation = operation

    def parse(self, lexis_string, braces_pairs, element_pattern):
        opening_braces = [element_pattern.findall(pair[0]) for pair in braces_pairs]
        closing_braces = [element_pattern.findall(pair[1]) for pair in braces_pairs]
        braces_counters = [0] * len(braces_pairs)
        result = []
        converted_name = element_pattern.findall(self.name)

        for i in range(len(lexis_string) - 1, -1, -1):
            for b in opening_braces:
                if startswith(lexis_string[i:], b):
                    braces_counters[opening_braces.index(b)] += 1

            for b in closing_braces:
                if startswith(lexis_string[i:], b):
                    braces_counters[closing_braces.index(b)] -= 1

            if all(b == 0 for b in braces_counters) \
                    and startswith(lexis_string[i:], converted_name) \
                    and (len(converted_name) > 0 or i != 0):

                result += [ParsingData(
                    self.operation,
                    [
                        lexis_string[:i],
                        lexis_string[i + len(converted_name):],
                    ]
                )]
        return result
