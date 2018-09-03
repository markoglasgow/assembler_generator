from asm_int_types import AsmIntTypes
from asm_grammar_spec import AsmGrammarSpec, AsmInstructionDefinition, TokenTypes, BitfieldModifier, ModifierTypes
from parse_utils import ParseUtils
from enum import Enum
from typing import List, Dict


# This module is responsible for parsing the input assembly source code. It takes as input the AsmGrammarSpec (the
# information from the parsed spec file) and the assembly source code, and as output it produces an AST).

# This enum describes the different types of matches that the token matcher can produce.
# NO_MATCH - no match was made at all
# PARTIAL_MATCH - tokens in token buffer so far partially match expected tokens. Keep parsing
# EXACT_MATCH - tokens in token buffer exactly match expected tokens.
class TokenMatchType(Enum):
    NO_MATCH = 0
    PARTIAL_MATCH = 1
    EXACT_MATCH = 2


# This object is the building block of the AST, which is the ultimate output of this module. Each line of the parsed
# assembly code will be translated to a root ASTNode of type INSTRUCTION. In turn, each of these INSTRUCTION nodes will
# have child_node which describe the parsed instruction. Those child nodes in turn may have children etc...
#
# token_type - type of parsed token, corresponds to asm_grammar_spec.TokenTypes
# token_value - value of token, depends on what type of token it is. Usually used to identify the token, or describe
#               what was parsed to produce this ASTNode
# original_line - raw contents of original line that was parsed to produce this node. Only present if a node is an
#                   INSTRUCTION node. Is useful for debugging
# original_line_num - original line number of the instruction parsed to produce this ASTNode. Only present if a node
#                       is an INSTRUCTION node. Useful for debugging and printing error messages.
# labels            - list of labels associated with this ASTNode.
# node_bitfields    - bitfield modifiers associated with this node. These bitfield modifiers typically come from the
#                       token pattern which was matched by the parsed to produce this ASTNode
# address           - pseudo-memory-address of the node in the assembled bitstream. Essential for correctly computing
#                       relative offsets and memory references of labels during bitstream generation.
class ASTNode:

    def __init__(self, token_type=None, token_value=None, child_nodes=None, bitfield_modifiers=None):
        self.token_type = token_type        # type: TokenTypes
        self.token_value = token_value      # type: str
        self.original_line = ""             # type: str
        self.original_line_num = -1         # type: int
        self.labels = []                    # type: List[str]
        self.node_bitfields = None
        self.address = 0
        if child_nodes is None:
            self.child_nodes = []                         # type: List[ASTNode]
        else:
            self.child_nodes = child_nodes                # type: List[ASTNode]
        if bitfield_modifiers is None:
            self.bitfield_modifiers = []                  # type: List[BitfieldModifier]
        else:
            self.bitfield_modifiers = bitfield_modifiers  # type: List[BitfieldModifier]
        return

    def set_original_line(self, line: str, line_num: int):
        self.original_line = line
        self.original_line_num = line_num
        return

    def set_node_bitfields(self, bitfields):
        self.node_bitfields = bitfields
        return

    def set_node_address(self, address):
        self.address = address
        for child_node in self.child_nodes:
            child_node.set_node_address(address)
        return


# Singleton object responsible for parsing the input assembly source code
# spec - AsmGrammarSpec object describing the architecture that will be parsed
# sigma16_labels - Sigma16 labels are a bit different than regular labels in other assembler languages, and should be
#                    parsed in a special way. This flag will enable that special parsing.
#
# Object fields
# spec          - reference to AsmGrammarSpec object describing the architecture
# ast           - output of this module. Is a list of ASTNodes. Each ASTNode in the list is an INSTRUCTION node which
#                   corresponds to a line of parsed assembly code. It in turns have child nodes which describe the
#                   parsed line of assembly code.
# labels_map    - dictionary which allows us to look up if a label is on a line of code
# all_labels    - keeps track of all parsed labels and their line. Can look up label by name
# input_file    - lines of the input assembly source code.
# line_num      - number of current line being parsed in the assembly source code
# line          - contents of the current assembly line being parsed
# line_pos      - position of the parser at the current line that is being parsed
# token_buffer  - special buffer into which the line's characters are read in one-by-one, and then the parser attempts
#                   to match the characters in this buffer against different expected token patterns.
# max_parsed_depth - this is for parser error handling. Keeps track of the max depth of the expected stack when parsing
#                       the current line of code
# error_parsed_buffer   - this will hold the deepest stack of tokens the parser was able to parse on the current line.
#                           If there is an error, the parser will display this stack to let the user know what it was
#                           able to parse on the current line, and where it errored out.
# error_expected_buffer - This buffers shows the user what it was expecting to parse.
# error_bad_buffer      - This buffer shows to the user what the parser read instead of what it was expecting.
# expected_stack        - This is the actual expected stack, which will keep track of what the parser has parsed so far
#                           and what it expects next. The 'deepest' expected stack for a line will be saved to
#                           'error_parsed_buffer', and will be displayed to the user in case of a parse error.
class AsmParser:

    def __init__(self, spec: AsmGrammarSpec, sigma16_labels=False):

        self.spec = spec        # type: AsmGrammarSpec
        self.ast = []           # type: List[ASTNode]

        self.labels_map = {}    # type: Dict[int, str]
        self.all_labels = {}    # type: Dict[str, int]

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

        self.sigma16_labels = sigma16_labels

    def get_ast(self):
        return self.ast

    # Entrypoint for this module, responsible for kicking off the parsing of the inputted assembly code.
    def parse_asm_listing(self, input_file_path: str):

        with open(input_file_path, "r") as f:
            self.input_file = f.readlines()

        self.parse_labels()
        self.parse_asm()
        self.assign_labels()

        return

    # This is the first pass of the parser. It goes over each line of assembly code, and recognizes and parses any
    # labels that might be on that line.
    def parse_labels(self):

        self.line_num = 0
        while self.line_num < len(self.input_file):
            self.line = self.input_file[self.line_num]

            # Skip empty lines and comments
            # TODO: Make comment character configurable. Add support for comments on code lines.
            if len(self.line.strip()) == 0 or self.line.strip().startswith(";"):
                self.line_num += 1
                continue

            self.parse_line_labels()
            self.line_num += 1

        return

    # This is the second pass of the parser. It goes across each line of assembly code and parses it.
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

    # Helper method to read a character from the current position in the line, and place it in the token buffer.
    # Returns True is read was successful, False if an error occured (for example, invalid char or eol).
    # to_lower - cast the character to lowercase automatically
    # valid_chars - if character read is not in valid_chars, return False to indicate we have read an invalid character.
    #               also do not increase position.
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

    # Helper method to let us skip over a string of whitespace characters at the current position in a line.
    def skip_line_whitespace(self):
        self.line_pos = ParseUtils.skip_whitespace(self.line, self.line_pos)
        return

    def reset_token_buffer(self):
        self.token_buffer = ""
        return

    def add_ast_node(self, node: ASTNode):
        self.ast.append(node)
        return

    # Method responsible for parsing the current line of assembly code.
    def parse_current_line(self):

        self.reset_error_buffer()
        self.reset_token_buffer()
        self.line_pos = 0

        # If there is a label on this line, skip over reading it.
        if self.line_num in self.labels_map:
            self.line_pos = len(self.labels_map[self.line_num])
            if not self.sigma16_labels:
                self.line_pos += len(":")
            self.line_pos = ParseUtils.skip_whitespace(self.line, self.line_pos)
            # If the rest of the line is whitespace, there is no instruction to parse, so immediately return.
            if self.line_pos == len(self.line):
                return

        instruction_node = self.parse_instruction()  # type: ASTNode
        instruction_node.set_original_line(self.line, self.line_num)

        self.add_ast_node(instruction_node)

        return

    # Parses an instruction at the current position of the current line of assembly code. Returns an ASTNode containing
    # the parsed instruction, or displays an error describing why it wasn't able to parse the instruction.
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

    # Get an instruction definition by name from the spec.
    def get_insn_defn(self, insn_defn_name: str):
        return self.spec.spec[insn_defn_name]

    # Match an instruction definition to the characters at the current position. If successful, return any child nodes
    # produced by the match, along with the bitfield modifiers of the current token pattern that was matched.
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

    # Try to match a token pattern from an instruction definition against the characters at the current position. If
    # successful, return any child AST nodes produced by the match.
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

            # Push the token we are expecting to match on the expected stack
            self.push_expected(token_type, token_value)

            # Different types of match functions will be used depending on the type of token being matched.
            if token_type == TokenTypes.WHITESPACE:
                token_match = self.try_match_whitespace_token(token_value)
            elif token_type == TokenTypes.INT_TOKEN:
                token_match, ast_node = self.try_match_int_token(token_value)
            elif token_type == TokenTypes.LABEL_TOKEN:
                token_match, ast_node = self.try_match_label_token(token_value)
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

    # Try to match a whitespace token. Means the parser expects a string of whitespace characters at the current position
    def try_match_whitespace_token(self, token_value):
        token_match = False

        if self.read_line_char() is not False:
            if self.match_token(' ') != TokenMatchType.NO_MATCH or self.match_token('\t') != TokenMatchType.NO_MATCH:
                self.skip_line_whitespace()
                token_match = True
            else:
                token_match = False

        return token_match

    # Try to match an int token. Means the parser expects a string of characters from a character whitelist (the whitelist
    # comes from the plugin system) to be present at the current position.
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

    # Try to match a label. Means the parser expects for there to be an alphanumeric identifier at the current position.
    def try_match_label_token(self, token_value):
        token_match = False
        ast_node = ASTNode()

        valid_chars = ParseUtils.valid_identifier_chars

        if self.read_line_char(to_lower=False, valid_chars=valid_chars) is not False:
            while self.read_line_char(to_lower=False, valid_chars=valid_chars):
                continue

            if self.token_buffer in self.all_labels:
                ast_node = ASTNode(TokenTypes.LABEL_TOKEN, token_value + " " + self.token_buffer, None)
                token_match = True
            else:
                # print("ERROR: Unknown label '%s' on line '%s'" % (self.token_buffer, (self.line_num+1)))
                # raise ValueError
                token_match = False

        return token_match, ast_node

    # Try to match a raw token. Means the parser expects EXACTLY token_value to be at the current position.
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

    # Matches a placeholder token. This is done by looking up the placeholder token, and then trying to recursively
    # match it. Returns any children produced by such a match.
    def try_match_placeholder_token(self, token_value):
        sub_defn = self.get_insn_defn(token_value)
        return self.match_defn(sub_defn)

    # Responsible for matching a token against the characters in the token buffer.
    # NO_MATCH - means the token buffer does not equal the expected token value
    # PARTIAL_MATCH - characters in token buffer partially match expected token value. Signals to the parser to keep
    #                   reading characters into the token buffer in hopes of producing a match.
    # EXACT_MATCH - characters in token buffer exactly match expected token value.
    def match_token(self, token_val):

        if len(token_val) == 0:
            return TokenMatchType.NO_MATCH

        if token_val == self.token_buffer:
            return TokenMatchType.EXACT_MATCH
        elif token_val.startswith(self.token_buffer):
            return TokenMatchType.PARTIAL_MATCH
        else:
            return TokenMatchType.NO_MATCH

    # Checks if the rest of the current line is empty, and contains no more code.
    def is_rest_empty(self):
        while self.read_line_char() is not False:
            c = self.token_buffer[-1:]

            # TODO: Add support for other comment characters. Check that comment char is not in string literal.
            if c == ';':
                return True
            elif c == ' ' or c == '\t':
                continue
            else:
                return False

        return True

    # Once an instruction definition is matched and parsed, it might have placeholder bitfield modifiers for ints.
    # The actual values of these int placeholders will be held in INT_TOKENS, which are children of the topmost matched
    # node. So for each INT_PLACEHOLDER bitfield modifier, iterate across all child nodes and find the INT_TOKEN containing
    # its placeholder value, emit the correct bits, and then set the INT_PLACEHOLDER to be a regular bitfield modifier which
    # is simply setting the bits emitted by the plugin.
    def process_int_placeholders(self, bitfield_modifiers: List[BitfieldModifier], children: List[ASTNode]) -> List[BitfieldModifier]:
        processed_bitfields = []
        for b in bitfield_modifiers:

            if b.modifier_type == ModifierTypes.MODIFIER or b.modifier_type == ModifierTypes.LABEL_PLACEHOLDER:
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

                        new_modifier = BitfieldModifier(ModifierTypes.MODIFIER, b.bitfield_name, int_bit_string)
                        processed_bitfields.append(new_modifier)
                        break

                if not found_child:
                    print("ERROR: We have a placeholder bitfield modifier '%s', but none of the child AST nodes are of type INT_TOKEN with a matching name." % int_placeholder_name)
                    raise ValueError

            else:
                print("ASSERT ERROR: Unknown type of bitfield modifier being used?")
                raise ValueError
        return processed_bitfields

    # Check if a bitstring is 1's and 0's.
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

    # Push the next expected token onto the expected stack.
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

    # In case a match doesn't happen, pop the expected token off the expected stack. If this is the 'deepest' expected
    # stack so far, then save it so that later it can be used to display an error message if need be.
    def pop_expected(self):

        if len(self.expected_stack) > self.max_parsed_depth:
            self.build_error_message()

        del self.expected_stack[-1]
        return

    # Build the error message from the expected stack. This shows the user what tokens were parsed so far, what was
    # expected by the parser, and what the parser read instead of what was expected. Also shows line number.
    def build_error_message(self):
        self.error_expected_buffer = self.expected_stack[-1]
        self.error_bad_buffer = self.token_buffer + self.line[self.line_pos:]
        self.max_parsed_depth = len(self.expected_stack)

        self.error_parsed_buffer = ""
        for parsed_token in self.expected_stack[:-1]:
            self.error_parsed_buffer += parsed_token + " "

        return

    # Shows an error message indicating the rest of the line wasn't empty when it should have been.
    def error_expected_empty_endline(self):
        if len(self.expected_stack) > self.max_parsed_depth:
            self.error_expected_buffer = "<< rest of line should be empty >>"
            self.error_bad_buffer = self.token_buffer[-1:] + self.line[self.line_pos:]
            self.max_parsed_depth = len(self.expected_stack)

            self.error_parsed_buffer = ""
            for parsed_token in self.expected_stack:
                self.error_parsed_buffer += parsed_token + " "

        return

    # Parses the labels on a line. Handles 'regular' labels of type 'label:' or Sigma16 labels which are simply the
    # first word on a line of text.
    def parse_line_labels(self):

        # TODO: Maybe allow for labels of a different format from "label_name:"
        if self.sigma16_labels:
            if self.line[0] == ' ' or self.line[0] == '\t':
                return
        else:
            self.line = self.line.strip()
            if ":" not in self.line:
                return

        possible_label, pos = ParseUtils.read_token(self.line, 0, break_chars=[' ', '\t', ':'], valid_chars=ParseUtils.valid_identifier_chars_map)
        end_char = ParseUtils.read_next_char(self.line, pos)

        is_label = False
        if self.sigma16_labels and end_char is not None and (end_char == " " or end_char == '\t'):
            is_label = True
        elif end_char is not None and end_char == ":":
            is_label = True

        if is_label:
            if possible_label in self.all_labels:
                print("ERROR: Duplicate label '%s' on lines %s and %s" % (possible_label, self.line_num+1, self.all_labels[possible_label]+1))
                raise ValueError
            self.labels_map[self.line_num] = possible_label
            self.all_labels[possible_label] = self.line_num

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
