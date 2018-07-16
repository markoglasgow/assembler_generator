
from asm_grammar_spec import AsmGrammarSpec, AsmInstructionDefinition, TokenTypes
from parse_utils import ParseUtils
from enum import Enum
from typing import List


class TokenMatchType(Enum):
    NO_MATCH = 0
    PARTIAL_MATCH = 1
    EXACT_MATCH = 2


class ASTNode:

    def __init__(self, token_type=None, token_value=None, child_nodes=None):
        self.token_type = token_type    # type: TokenTypes
        self.token_value = token_value  # type: str
        if child_nodes is None:
            self.child_nodes = []
        else:
            self.child_nodes = child_nodes


class AsmParser:

    def __init__(self, spec: AsmGrammarSpec):

        self.spec = spec  # type: AsmGrammarSpec
        self.ast = []     # type: List[ASTNode]

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

    def add_ast_node(self, node: ASTNode):
        self.ast.append(node)
        return

    def parse_current_line(self):

        self.reset_token_buffer()
        self.line_pos = 0

        instruction_node = self.parse_instruction()  # type: ASTNode

        self.add_ast_node(instruction_node)

        return

    def parse_instruction(self) -> ASTNode:

        instruction_defn = self.get_insn_defn("INSTRUCTION")  # type: AsmInstructionDefinition
        is_match, children = self.match_defn(instruction_defn, top_level=True)

        if not is_match:
            print("Assembler ERROR: Unable to parse INSTRUCTION on line %s" % (self.line_num+1))
            raise ValueError

        return ASTNode(TokenTypes.PLACEHOLDER, "INSTRUCTION", children)

    def get_insn_defn(self, insn_defn_name: str):
        return self.spec.spec[insn_defn_name]

    def match_defn(self, defn: AsmInstructionDefinition, top_level=False):

        possible_patterns = defn.spec_patterns

        for defn_row in range(len(possible_patterns)):
            token_pattern = possible_patterns[defn_row]

            save_line_pos = self.line_pos
            save_token_buffer = self.token_buffer

            pattern_match, children = self.try_match_token_pattern(token_pattern)

            if top_level and pattern_match:
                # Check if the rest of the line is empty if we're trying to match the
                # top-level pattern
                pattern_match = self.is_rest_empty()

            if pattern_match:
                return True, children
            else:
                self.line_pos = save_line_pos
                self.token_buffer = save_token_buffer
                continue

        return False, []

    def try_match_token_pattern(self, token_pattern):

        pattern_match = False
        child_nodes = []

        for defn_col in range(len(token_pattern)):
            token_match = False
            ast_node = None
            placeholder_children = None
            current_token = token_pattern[defn_col]

            token_type = current_token[0]
            token_value = current_token[1]

            if token_type == TokenTypes.WHITESPACE:
                token_match = self.try_match_whitespace_token(token_value)
            elif token_type == TokenTypes.RAW_TOKEN:
                token_match, ast_node = self.try_match_raw_token(token_value)
            elif token_type == TokenTypes.PLACEHOLDER:
                token_match, placeholder_children = self.try_match_placeholder_token(token_value)
            else:
                print("ERROR. Unimplemented token type?")
                raise ValueError

            if token_match:
                pattern_match = True

                if ast_node is not None:
                    child_nodes.append(ast_node)
                if placeholder_children is not None:
                    placeholder_node = ASTNode(TokenTypes.PLACEHOLDER, token_value, placeholder_children)
                    child_nodes.append(placeholder_node)

                self.reset_token_buffer()
                continue
            else:
                pattern_match = False
                child_nodes = []
                break

        return pattern_match, child_nodes

    def try_match_whitespace_token(self, token_value):
        token_match = False

        if self.read_line_char() is not False:
            if self.match_token(token_value) != TokenMatchType.NO_MATCH:
                self.skip_line_whitespace()
                token_match = True
            else:
                token_match = False

        return token_match

    def try_match_raw_token(self, token_value):
        token_match = False
        ast_node = ASTNode()

        if self.read_line_char() is not False:
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
                ast_node = ASTNode(TokenTypes.RAW_TOKEN, token_value)

        return token_match, ast_node

    def try_match_placeholder_token(self, token_value):
        sub_defn = self.get_insn_defn(token_value)
        return self.match_defn(sub_defn)

    def match_token(self, token_val):

        if len(token_val) == 0:
            return TokenMatchType.NO_MATCH

        if token_val == self.token_buffer:
            return TokenMatchType.EXACT_MATCH
        elif token_val.startswith(self.token_buffer):
            return TokenMatchType.PARTIAL_MATCH
        else:
            return TokenMatchType.NO_MATCH

    def is_rest_empty(self):
        while self.read_line_char() is not False:
            c = self.token_buffer[-1:]

            # TODO: Add support for other comment characters. Check that comment char is not in string literal.
            if c == ';':
                return True
            elif c == ' ':
                continue
            else:
                return False

        return True
