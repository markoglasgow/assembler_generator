
from asm_grammar_spec import AsmGrammarSpec, AsmInstructionDefinition, TokenTypes
from parse_utils import ParseUtils
from enum import Enum


class TokenMatchType(Enum):
    NO_MATCH = 0
    PARTIAL_MATCH = 1
    EXACT_MATCH = 2


class AsmParser:

    def __init__(self, spec: AsmGrammarSpec):

        self.spec = spec  # type: AsmGrammarSpec
        self.ast = []

        self.line_num = 0
        self.line = ""
        self.line_pos = 0

        self.token_buffer = ""

    def get_ast(self):
        return self.ast

    def parse_asm_listing(self, input_file_path: str):

        with open(input_file_path, "r") as f:
            input_file = f.readlines()

        self.line_num = 0
        while self.line_num < len(input_file):
            self.line = input_file[self.line_num].strip()

            # Skip empty lines and comments
            # TODO: Make comment character configurable. Add support for comments on code lines.
            if len(self.line) == 0 or self.line.startswith(";"):
                self.line_num += 1
                continue

            self.parse_current_line()
            self.line_num += 1

        return

    def read_line_char(self, to_lower=True):
        next_char = ParseUtils.read_next_char(self.line, self.line_pos)
        if next_char is None:
            return False
        if to_lower:
            next_char = next_char.lower()
        self.token_buffer += next_char
        self.line_pos += 1
        return True

    def skip_line_whitespace(self):
        self.line_pos = ParseUtils.skip_whitespace(self.line, self.line_pos)
        return

    def reset_token_buffer(self):
        self.token_buffer = ""
        return

    def add_ast_node(self, node):
        self.ast.append(node)
        return

    def parse_current_line(self):

        self.reset_token_buffer()
        instruction_node = self.parse_instruction()

        self.add_ast_node(instruction_node)

        return

    def parse_instruction(self):

        instruction_defn = self.get_insn_defn("INSTRUCTION")  # type: AsmInstructionDefinition
        self.match_defn(instruction_defn)

        return -1

    def get_insn_defn(self, insn_defn_name: str):
        return self.spec.spec[insn_defn_name]

    def match_defn(self, defn: AsmInstructionDefinition):

        possible_patterns = defn.spec_patterns

        for defn_row in range(len(possible_patterns)):
            token_pattern = possible_patterns[defn_row]

            save_line_pos = self.line_pos
            save_token_buffer = self.token_buffer

            pattern_match = self.try_match_token_pattern(token_pattern)

            if pattern_match:
                return True
            else:
                self.line_pos = save_line_pos
                self.token_buffer = save_token_buffer
                continue

        return False

    def try_match_token_pattern(self, token_pattern):

        pattern_match = False
        for defn_col in range(len(token_pattern)):
            token_match = False
            current_token = token_pattern[defn_col]

            token_type = current_token[0]
            token_value = current_token[1]

            if token_type == TokenTypes.WHITESPACE:
                token_match = self.try_match_whitespace_token(token_value)
            elif token_type == TokenTypes.RAW_TOKEN:
                token_match = self.try_match_raw_token(token_value)
            elif token_type == TokenTypes.PLACEHOLDER:
                token_match = self.try_match_placeholder_token(token_value)
            else:
                print("ERROR. Unimplemented token type?")
                raise ValueError

            if token_match:
                pattern_match = True
                self.reset_token_buffer()
                continue
            else:
                pattern_match = False
                break

        return pattern_match

    def try_match_whitespace_token(self, token_value):
        token_match = False

        if self.read_line_char() is not None:
            if self.match_token(token_value) != TokenMatchType.NO_MATCH:
                self.skip_line_whitespace()
                token_match = True
            else:
                token_match = False

        return token_match

    def try_match_raw_token(self, token_value):
        token_match = False

        if self.read_line_char() is not None:
            match_type = self.match_token(token_value)
            while match_type == TokenMatchType.PARTIAL_MATCH:
                if not self.read_line_char():
                    match_type = TokenMatchType.NO_MATCH
                    break
                match_type = self.match_token(token_value)

            if match_type == TokenMatchType.NO_MATCH:
                token_match = False
            elif match_type == TokenMatchType.EXACT_MATCH:
                token_match = True

        return token_match

    def try_match_placeholder_token(self, token_value):
        token_match = False

        sub_defn = self.get_insn_defn(token_value)
        ret_val = self.match_defn(sub_defn)
        if ret_val is None or not ret_val:
            token_match = False
        else:
            token_match = True

        return token_match

    def match_token(self, token_val):

        if len(token_val) == 0:
            return TokenMatchType.NO_MATCH

        if token_val == self.token_buffer:
            return TokenMatchType.EXACT_MATCH
        elif token_val.startswith(self.token_buffer):
            return TokenMatchType.PARTIAL_MATCH
        else:
            return TokenMatchType.NO_MATCH
