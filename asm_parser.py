from asm_int_types import AsmIntTypes
from asm_grammar_spec import AsmGrammarSpec, AsmInstructionDefinition, TokenTypes, BitfieldModifier, ModifierTypes
from parse_utils import ParseUtils
from enum import Enum
from typing import List, Dict


class TokenMatchType(Enum):
    NO_MATCH = 0
    PARTIAL_MATCH = 1
    EXACT_MATCH = 2


class ASTNode:

    def __init__(self, token_type=None, token_value=None, child_nodes=None, bitfield_modifiers=None):
        self.token_type = token_type        # type: TokenTypes
        self.token_value = token_value      # type: str
        self.original_line = ""             # type: str
        self.original_line_num = -1         # type: int
        self.labels = []                    # type: List[str]
        if child_nodes is None:
            self.child_nodes = []
        else:
            self.child_nodes = child_nodes
        if bitfield_modifiers is None:
            self.bitfield_modifiers = []                  # type: List[BitfieldModifier]
        else:
            self.bitfield_modifiers = bitfield_modifiers  # type: List[BitfieldModifier]
        return

    def set_original_line(self, line: str, line_num: int):
        self.original_line = line
        self.original_line_num = line_num
        return


class AsmParser:

    def __init__(self, spec: AsmGrammarSpec):

        self.spec = spec        # type: AsmGrammarSpec
        self.ast = []           # type: List[ASTNode]

        self.labels_map = {}    # type: Dict[int, str]

        self.input_file = ""
        self.line_num = 0
        self.line = ""
        self.line_pos = 0

        self.token_buffer = ""

        self.max_parsed_depth = 0
        self.error_parsed_buffer = ""
        self.error_expected_buffer = ""
        self.error_bad_buffer = ""
        self.expected_stack = []

    def get_ast(self):
        return self.ast

    def parse_asm_listing(self, input_file_path: str):

        with open(input_file_path, "r") as f:
            self.input_file = f.readlines()

        self.parse_labels()
        self.parse_asm()
        self.assign_labels()

        return

    def parse_labels(self):

        self.line_num = 0
        while self.line_num < len(self.input_file):
            self.line = self.input_file[self.line_num].strip()

            # Skip empty lines and comments
            # TODO: Make comment character configurable. Add support for comments on code lines.
            if len(self.line) == 0 or self.line.startswith(";"):
                self.line_num += 1
                continue

            self.parse_line_labels()
            self.line_num += 1

        return

    def parse_asm(self):

        self.line_num = 0
        while self.line_num < len(self.input_file):
            self.line = self.input_file[self.line_num].strip()

            # Skip empty lines and comments
            # TODO: Make comment character configurable. Add support for comments on code lines.
            if len(self.line) == 0 or self.line.startswith(";"):
                self.line_num += 1
                continue

            self.parse_current_line()
            self.line_num += 1

        return

    def read_line_char(self, to_lower=True, valid_chars=None):
        next_char = ParseUtils.read_next_char(self.line, self.line_pos)
        if next_char is None:
            return False
        if valid_chars is not None:
            if next_char not in valid_chars:
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

        self.reset_error_buffer()
        self.reset_token_buffer()
        self.line_pos = 0

        # If there is a label on this line, skip over reading it.
        if self.line_num in self.labels_map:
            self.line_pos = len(self.labels_map[self.line_num] + ":")
            self.line_pos = ParseUtils.skip_whitespace(self.line, self.line_pos)
            # If the rest of the line is whitespace, there is no instruction to parse, so immediately return.
            if self.line_pos == len(self.line):
                return

        instruction_node = self.parse_instruction()  # type: ASTNode
        instruction_node.set_original_line(self.line, self.line_num)

        self.add_ast_node(instruction_node)

        return

    def parse_instruction(self) -> ASTNode:

        instruction_defn = self.get_insn_defn("INSTRUCTION")  # type: AsmInstructionDefinition
        is_match, children, bitfield_modifiers = self.match_defn(instruction_defn, top_level=True)

        if not is_match:
            print("Assembler ERROR: Unable to parse INSTRUCTION on line %s" % (self.line_num+1))
            print("PARSED: " + self.error_parsed_buffer)
            print("EXPECTED: " + self.error_expected_buffer)
            print("INSTEAD GOT: " + self.error_bad_buffer)
            raise ValueError

        return ASTNode(TokenTypes.PLACEHOLDER, "INSTRUCTION", children, bitfield_modifiers)

    def get_insn_defn(self, insn_defn_name: str):
        return self.spec.spec[insn_defn_name]

    def match_defn(self, defn: AsmInstructionDefinition, top_level=False):

        possible_patterns = defn.spec_patterns

        for defn_row in range(len(possible_patterns)):
            token_pattern = possible_patterns[defn_row].token_patterns
            bitfield_modifiers = possible_patterns[defn_row].bitfield_modifiers

            save_line_pos = self.line_pos
            save_token_buffer = self.token_buffer
            save_expected_stack = self.expected_stack.copy()

            pattern_match, children = self.try_match_token_pattern(token_pattern)

            if top_level and pattern_match:
                # Check if the rest of the line is empty if we're trying to match the
                # top-level pattern
                pattern_match = self.is_rest_empty()
                if not pattern_match:
                    self.error_expected_empty_endline()

            if pattern_match:
                bitfield_modifiers = self.process_int_placeholders(bitfield_modifiers, children)
                return True, children, bitfield_modifiers
            else:
                self.line_pos = save_line_pos
                self.token_buffer = save_token_buffer
                self.expected_stack = save_expected_stack
                continue

        return False, [], []

    def try_match_token_pattern(self, token_pattern):

        pattern_match = False
        child_nodes = []

        for defn_col in range(len(token_pattern)):
            # noinspection PyUnusedLocal
            token_match = False
            # noinspection PyUnusedLocal
            bitfield_modifiers = []

            ast_node = None
            placeholder_children = None
            current_token = token_pattern[defn_col]

            token_type = current_token[0]
            token_value = current_token[1]

            self.push_expected(token_type, token_value)

            if token_type == TokenTypes.WHITESPACE:
                token_match = self.try_match_whitespace_token(token_value)
            elif token_type == TokenTypes.INT_TOKEN:
                token_match, ast_node = self.try_match_int_token(token_value)
            elif token_type == TokenTypes.RAW_TOKEN:
                token_match, ast_node = self.try_match_raw_token(token_value)
            elif token_type == TokenTypes.PLACEHOLDER:
                token_match, placeholder_children, bitfield_modifiers = self.try_match_placeholder_token(token_value)
            else:
                print("ERROR. Unimplemented token type?")
                raise ValueError

            if token_match:
                pattern_match = True

                if ast_node is not None:
                    child_nodes.append(ast_node)
                if placeholder_children is not None:
                    placeholder_node = ASTNode(TokenTypes.PLACEHOLDER, token_value, placeholder_children, bitfield_modifiers)
                    child_nodes.append(placeholder_node)

                self.reset_token_buffer()
                continue
            else:

                self.pop_expected()

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

    def try_match_int_token(self, token_value):
        token_match = False
        ast_node = ASTNode()

        valid_chars = AsmIntTypes.get_valid_chars(token_value)

        if self.read_line_char(to_lower=False, valid_chars=valid_chars) is not False:
            while self.read_line_char(to_lower=False, valid_chars=valid_chars):
                token_match = False

            if AsmIntTypes.validate_integer(token_value, self.token_buffer):
                ast_node = ASTNode(TokenTypes.INT_TOKEN, token_value + " " + self.token_buffer, None)
                token_match = True

        return token_match, ast_node

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
                ast_node = ASTNode(TokenTypes.RAW_TOKEN, token_value, None)

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

    def process_int_placeholders(self, bitfield_modifiers: List[BitfieldModifier], children: List[ASTNode]) -> List[BitfieldModifier]:
        processed_bitfields = []
        for b in bitfield_modifiers:

            if b.modifier_type == ModifierTypes.MODIFIER:
                processed_bitfields.append(b)

            elif b.modifier_type == ModifierTypes.INT_PLACEHOLDER:
                found_child = False
                int_placeholder_name = b.modifier_value
                for ast_node in children:
                    if ast_node.token_type == TokenTypes.INT_TOKEN and ast_node.token_value.startswith(int_placeholder_name + " "):
                        found_child = True
                        raw_int_string = ast_node.token_value[len(int_placeholder_name + " "):]
                        int_bit_string = AsmIntTypes.emit_bits(int_placeholder_name, raw_int_string)

                        if not self.is_valid_bitstring(int_bit_string):
                            print("ERROR: Emit of a '%s' with value '%s' returned bitstring '%s', which is invalid. Bitstrings may only contain 1 and 0 characters." % (int_placeholder_name, raw_int_string, int_bit_string))
                            raise ValueError

                        bitfield_defn_index = self.spec.bitfield_indexes_map[b.bitfield_name]
                        bitfield_defn = self.spec.bitfields[bitfield_defn_index]
                        if len(int_bit_string) != bitfield_defn.size:
                            print("ERROR: When parsing a '%s' with value '%s', the plugin returned the bitstream '%s' of length %s. However, the bitfield named '%s' (which this bitstream value is being assigned to) expects a bitstream of length %s" % (int_placeholder_name, raw_int_string, int_bit_string, len(int_bit_string), b.bitfield_name, bitfield_defn.size))
                            raise ValueError

                        b.modifier_type = ModifierTypes.MODIFIER
                        b.modifier_value = int_bit_string
                        processed_bitfields.append(b)
                        break

                if not found_child:
                    print("ERROR: We have a placeholder bitfield modifier '%s', but none of the child AST nodes are of type INT_TOKEN with a matching name." % int_placeholder_name)
                    raise ValueError

            else:
                print("ASSERT ERROR: Unknown type of bitfield modifier being used?")
                raise ValueError
        return processed_bitfields

    def is_valid_bitstring(self, bitstring):
        for c in bitstring:
            if c == '0' or c == '1':
                continue
            else:
                return False
        return True

    def reset_error_buffer(self):
        self.max_parsed_depth = 0
        self.error_parsed_buffer = ""
        self.error_expected_buffer = ""
        self.error_parsed_buffer = ""
        self.expected_stack = []
        return

    def push_expected(self, token_type, token_value):
        if token_type == TokenTypes.RAW_TOKEN:
            self.expected_stack.append("'" + token_value + "'")
        elif token_type == TokenTypes.WHITESPACE:
            self.expected_stack.append("' '")
        elif token_type == TokenTypes.INT_TOKEN:
            self.expected_stack.append(token_value)
        elif token_type == TokenTypes.PLACEHOLDER:
            self.expected_stack.append('%' + token_value + '%')
        return

    def pop_expected(self):

        if len(self.expected_stack) > self.max_parsed_depth:
            self.build_error_message()

        del self.expected_stack[-1]
        return

    def build_error_message(self):
        self.error_expected_buffer = self.expected_stack[-1]
        self.error_bad_buffer = self.token_buffer + self.line[self.line_pos:]
        self.max_parsed_depth = len(self.expected_stack)

        self.error_parsed_buffer = ""
        for parsed_token in self.expected_stack[:-1]:
            self.error_parsed_buffer += parsed_token + " "

        return

    def error_expected_empty_endline(self):
        if len(self.expected_stack) > self.max_parsed_depth:
            self.error_expected_buffer = "<< rest of line should be empty >>"
            self.error_bad_buffer = self.token_buffer[-1:] + self.line[self.line_pos:]
            self.max_parsed_depth = len(self.expected_stack)

            self.error_parsed_buffer = ""
            for parsed_token in self.expected_stack:
                self.error_parsed_buffer += parsed_token + " "

        return

    def parse_line_labels(self):

        # TODO: Maybe allow for labels of a different format from "label_name:"
        if ":" not in self.line:
            return

        possible_label, pos = ParseUtils.read_token(self.line, 0, break_chars=[' ', ':'], valid_chars=ParseUtils.valid_identifier_chars_map)
        end_char = ParseUtils.read_next_char(self.line, pos)

        if end_char is not None and end_char == ":":
            self.labels_map[self.line_num] = possible_label

        return

    # Assigns labels to AST nodes.
    def assign_labels(self):

        # First build a list where each entry of the list corresponds to a line num. The list keeps track of which
        # AST node a label would point to, if there was a label on that line.
        assignment_list = [-1] * len(self.input_file)
        for ast_index, ast_node in enumerate(self.ast):
            if ast_node.original_line_num >= 0:
                idx = ast_node.original_line_num
                while idx >= 0:
                    if assignment_list[idx] == -1:
                        assignment_list[idx] = ast_index
                        idx -= 1
                    else:
                        break

        # Now go through the map of labels. For each label, look up which AST node is belongs to, and then assign it
        # to that AST node.
        for label_line_num in self.labels_map:
            ast_idx = assignment_list[label_line_num]
            self.ast[ast_idx].labels.append(self.labels_map[label_line_num])

        return
