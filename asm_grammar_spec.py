from asm_int_types import AsmIntTypes
from parse_utils import ParseUtils
from enum import Enum
from typing import Dict, List, Optional

# This module is responsible for parsing the custom ADL spec file, which describes the assembler architecture. Once the
# parsing is done, all information will be held in an AsmGrammarSpec object, which will be passed to the assembly
# parser for use while parsing the assembly source code


# This object holds the name and size of each possible bitfield in an instruction of the specified architecture
class BitfieldDefinition:

    def __init__(self, name, size):
        self.name = name
        self.size = size
        return


# These are the different types of tokens possible for use in the parser.
# WHITESPACE - 1 or more whitespace characters
# RAW_TOKEN - A token which is simply a string which must be matched
# PLACEHOLDER - A placeholder token which is expanded into another instruction definition
# INT_TOKEN - Int which should be parsed and emitted by a plugin
# LABEL_TOKEN - Label which should be parsed and emitted by a plugin
class TokenTypes(Enum):
    WHITESPACE = 1
    RAW_TOKEN = 2
    PLACEHOLDER = 3
    INT_TOKEN = 4
    LABEL_TOKEN = 5


# This enum describes the different possible types of Bitfield Modifiers.
# MODIFIER - Regular modifier, sets some bitfield (specified by name) to some value
# INT_PLACEHOLDER - Set a bitfield to a bitstream emitted by a plugin, which generates bitstream from parsed int
# LABEL_PLACEHOLDER - Set a bitfield to a bitstream emitted by a plugin, which generates bitstream for label
class ModifierTypes(Enum):
    MODIFIER = 1
    INT_PLACEHOLDER = 2
    LABEL_PLACEHOLDER = 3


# This object contains the type, name (of bitfield to modify), and value (to set bitfield to) of a bitfield modifier.
class BitfieldModifier:

    def __init__(self, modifier_type, bitfield_name, modifier_value):
        self.modifier_type = modifier_type
        self.bitfield_name = bitfield_name
        self.modifier_value = modifier_value


# Object which contains a token pattern and its bitfield modifiers of an instruction definition parsed from the
# spec file
class DefinitionPattern:

    def __init__(self, token_patterns, bitfield_modifiers):
        self.token_patterns = token_patterns
        self.bitfield_modifiers = bitfield_modifiers  # type: List[BitfieldModifier]


# Object contains information for a single instruction definition parsed from the spec file.
# name - name of instruction definition
# line - which line instruction definition appears on in the spec file.
# spec_patterns - list of token patterns (and their corresponding bitfield modifiers) in the instruction definition
# only_raw_values - flag used only during debugging
class AsmInstructionDefinition:

    def __init__(self, name, line_num):
        self.name = name
        self.line_num = line_num
        self.spec_patterns = []  # type: List[DefinitionPattern]
        self.only_raw_values = True
        return

    def add_pattern(self, pattern: DefinitionPattern):
        self.spec_patterns.append(pattern)

        # TODO: Potentially remove this code
        if self.only_raw_values:
            for p in pattern.token_patterns:
                if p[0] == TokenTypes.PLACEHOLDER:
                    self.only_raw_values = False
        return


# This object holds all the information from the parsed spec file.
# spec - dictionary which allows the program to look up any instruction definition by name
# bitfields - list of all possible bitfields, in a given order
# bitfield_indexes_map - lets program look up index of bitfield in 'bitfields' list by its name
class AsmGrammarSpec:

    def __init__(self):
        self.parsed_asm_instruction_types = False
        self.parsed_bitfields_definitions = False
        self.spec = {}  # type: Dict[str, AsmInstructionDefinition]

        self.bitfields = []  # type: List[BitfieldDefinition]
        self.bitfield_indexes_map = {}  # type: Dict[str, int]

        return

    def add_bitfield(self, bitfield: BitfieldDefinition):
        self.bitfields.append(bitfield)
        self.bitfield_indexes_map[bitfield.name] = len(self.bitfields) - 1
        return

    # Entrypoint for this module, responsible for reading spec file and parsing it, and then validating it for common
    # errors
    def read_spec(self, spec_file_path):
        with open(spec_file_path, "r") as f:
            input_file = f.readlines()

        self.parse_spec(input_file)
        self.validate_spec()

        return

    # This function receives all the lines of the spec file and parses them one-by-one
    def parse_spec(self, spec_file_lines):

        line_num = 0

        while line_num < len(spec_file_lines):
            line = spec_file_lines[line_num].strip()

            # Skip empty lines and comments
            if len(line) == 0 or line.startswith("//"):
                line_num += 1
                continue

            if line == ".BIT_FIELDS":
                if self.parsed_bitfields_definitions:
                    print("ERROR: duplicate .BIT_FIELDS directive (line %s)" % (line_num+1))
                    raise ValueError

                line_num = self.parse_bitfield_definitions(line_num, spec_file_lines)
                self.parsed_bitfields_definitions = True
                continue

            elif line == ".ASM_INSTRUCTIONS":
                if self.parsed_asm_instruction_types:
                    print("ERROR: duplicate .ASM_INSTRUCTIONS directive (line %s)" % (line_num+1))
                    raise ValueError

                self.parse_asm_instructions_spec(line_num, spec_file_lines)
                self.parsed_asm_instruction_types = True
                break

            line_num += 1

        if not self.parsed_asm_instruction_types:
            print("ERROR: .ASM_INSTRUCTIONS directive was not found in spec file!")
            raise ValueError

        if not self.parsed_bitfields_definitions:
            print("ERROR: .BIT_FIELDS directive was not found in spec file!")
            raise ValueError

        return

    # This function is responsible for parsing the bitfield definitions, which specify the names and sizes of all
    # possible bitfields in an instruction in this architecture. The function keeps parsing until it hits the end
    # of the file, or the .ASM_INSTRUCTIONS directive. The function will start parsing from the .BIT_FIELDS directive.
    def parse_bitfield_definitions(self, start_line_num, spec_file_lines):

        line_num = start_line_num
        if not spec_file_lines[line_num].startswith(".BIT_FIELDS"):
            print("ERROR: Parsing bitfield definitions, but current line doesn't start with .BIT_FIELDS (line %s)" % (line_num+1))

        line_num += 1

        while line_num < len(spec_file_lines):

            line = spec_file_lines[line_num].strip()

            # Skip empty lines and comments
            if len(line) == 0 or line.startswith("//"):
                line_num += 1
                continue

            if line == ".ASM_INSTRUCTIONS":
                return line_num

            bitfield_name_line_num = line_num
            bitfield_size_line_num = line_num+1

            if bitfield_size_line_num >= len(spec_file_lines):
                print("ERROR: EOL after line %s when attempting to read bitfield size" % (line_num+1))
                raise ValueError

            bitfield_name_line = spec_file_lines[bitfield_name_line_num].strip()
            bitfield_size_line = spec_file_lines[bitfield_size_line_num].strip()

            bitfield_name = self.parse_bitfield_name(bitfield_name_line, bitfield_name_line_num)
            bitfield_size = self.parse_bitfield_size(bitfield_size_line, bitfield_size_line_num)

            self.add_bitfield(BitfieldDefinition(bitfield_name, bitfield_size))

            line_num += 2

        print("ERROR: .ASM_INSTRUCTIONS is not present in spec file after .BIT_FIELDS")
        raise ValueError

    # Parses and returns the name of a bitfield from a bitfield definition.
    def parse_bitfield_name(self, name_line: str, line_num: int):

        if not name_line.startswith("name:"):
            print("ERROR: Bitfield definition name on line %s must start with 'name:'" % (line_num+1))
            raise ValueError

        pos = len("name:")
        pos = ParseUtils.skip_whitespace(name_line, pos)

        bitfield_name, pos = ParseUtils.read_identifier(name_line, pos)

        # After reading the name of the bitfield, make sure the rest of the line is empty.
        if not ParseUtils.is_rest_empty(name_line, pos):
            print("ERROR: Extra characters present on line %s after bitfield name" % (line_num+1))
            raise ValueError

        return bitfield_name

    # Parses and returns the size of a bitfield from a bitfield definition
    def parse_bitfield_size(self, size_line: str, line_num: int):
        if not size_line.startswith("size:"):
            print("ERROR: Bitfield definition size on line %s must start with 'size:'" % (line_num+1))
            raise ValueError

        pos = len("size:")
        pos = ParseUtils.skip_whitespace(size_line, pos)

        bitfield_size, pos = ParseUtils.read_number(size_line, pos)

        # After reading the name of the bitfield, make sure the rest of the line is empty.
        if not ParseUtils.is_rest_empty(size_line, pos):
            print("ERROR: Extra characters present on line %s after bitfield size" % (line_num+1))
            raise ValueError

        try:
            bitfield_size = int(bitfield_size)
        except ValueError:
            print("ERROR: Unable to parse the number for bitfield size on line %s" % (line_num+1))
            raise ValueError

        return bitfield_size

    # This function starts from the .ASM_INSTRUCTIONS, and is responsible for parsing the instruction definitions of
    # the spec file all the way to the end of the file.
    def parse_asm_instructions_spec(self, start_line_num, spec_file_lines):

        line_num = start_line_num
        if not spec_file_lines[line_num].startswith(".ASM_INSTRUCTIONS"):
            print("ERROR: Parsing asm instructions directive, but current line doesn't start with .ASM_INSTRUCTIONS (line %s)" % (line_num+1))
            raise ValueError

        line_num += 1

        while line_num < len(spec_file_lines):

            line = spec_file_lines[line_num].strip()

            # Skip empty lines and comments
            if len(line) == 0 or line.startswith("//"):
                line_num += 1
                continue

            instr_defn_line = line_num
            asm_defn, line_num = self.parse_single_asm_instr_defn(line_num, spec_file_lines)

            if asm_defn.name in self.spec:
                print("ERROR: Duplicate instruction definition found: '%s' (line %s)" % (asm_defn.name, instr_defn_line+1))
                raise ValueError

            self.spec[asm_defn.name] = asm_defn

        return

    # Responsible for parsing a single instruction definition in the spec file. An instruction definition starts with
    # a name, followed by a list of token patterns, and ends with a ;.  Each token pattern can also optionally have
    # associated bitfield modifiers.
    def parse_single_asm_instr_defn(self, start_line_num, spec_file_lines):

        line_num = start_line_num
        line = spec_file_lines[line_num].strip()

        definition_name = self.read_asm_defn_name(line, line_num)
        asm_defn = AsmInstructionDefinition(definition_name, line_num)

        line_num += 1

        while line_num < len(spec_file_lines):
            line = spec_file_lines[line_num].strip()
            line_num += 1

            if len(line) > 0:
                pattern = self.read_asm_defn_pattern(line, line_num)
                if pattern is None:
                    break
                else:
                    asm_defn.add_pattern(pattern)

        if len(asm_defn.spec_patterns) == 0:
            print("ERROR: Empty instruction definition on line %s" % (start_line_num+1))
            raise ValueError

        return asm_defn, line_num

    # Responsible for parsing and returning the name of an instruction definition
    def read_asm_defn_name(self, line, line_num):

        name, pos = ParseUtils.read_identifier(line)

        if len(name) == 0:
            print("ERROR: Unable to read definition identifier on line %s." % (line_num+1))
            raise ValueError

        # Expect a '=' after the identifier
        token, pos = ParseUtils.read_token(line, pos)

        if token != "=":
            print("ERROR: Expected '=' after definition identifier on line %s" % (line_num+1))
            raise ValueError

        return name

    # Function is responsible for reading a token pattern and its associated bitfield modifiers. Can also return and
    # stop parsing if it detects a ; character (which denotes the end of the instruction definition).
    # Each token pattern's line must begin with |. It is followed by a list of raw tokens/whitespace tokens/placeholders
    # A placeholder token is surrounded by %% characters
    # Optionally, a list of bitfield modifiers (denoted with :: characters) can come after a token pattern.
    def read_asm_defn_pattern(self, line, line_num) -> Optional[DefinitionPattern]:

        pattern_tokens = []
        bitfield_modifiers = []
        first_token, pos = ParseUtils.read_token(line, 0, break_chars=[' ', '\t'], valid_chars={"|": "", ";": ""})

        if first_token == ";":
            return None

        elif first_token == "|":
            pos = ParseUtils.skip_whitespace(line, pos)

            while pos < len(line):
                next_char = ParseUtils.read_next_char(line, pos)
                if next_char is None:
                    print("ERROR: Expected asm instruction patterns on line %s after '|'." % (line_num+1))
                    raise ValueError

                elif next_char == '%':
                    pos += 1
                    placeholder_name, pos = ParseUtils.read_identifier(line, pos)
                    next_char = ParseUtils.read_next_char(line, pos)
                    if next_char != "%":
                        print("ERROR: Expected asm definition identifier to be terminated with %% character on line %s." % (line_num+1))
                        raise ValueError
                    pos += 1
                    pattern_tokens.append((TokenTypes.PLACEHOLDER, placeholder_name))

                elif next_char == ' ' or next_char == '\t':
                    pattern_tokens.append((TokenTypes.WHITESPACE, " "))
                    pos = ParseUtils.skip_whitespace(line, pos)

                elif next_char == ':':
                    pos += 1
                    next_char = ParseUtils.read_next_char(line, pos)
                    if next_char == ':':
                        pos += 1
                        str_modifiers = line[pos:]
                        bitfield_modifiers = self.read_bitfield_modifiers(str_modifiers, line_num)

                        if pattern_tokens[-1][0] == TokenTypes.WHITESPACE:
                            del pattern_tokens[-1]

                        break
                    else:
                        print("ERROR: Unexpected ':' character on line %s" % (line_num+1))
                        raise ValueError

                # TODO: Is it wise, handling comma characters in a special way like this?
                elif next_char == ',' or next_char == '[' or next_char == ']':
                    pos += 1
                    pattern_tokens.append((TokenTypes.RAW_TOKEN, next_char))

                else:
                    # TODO: Audit [ and ] in the break chars.
                    next_token, pos = ParseUtils.read_token(line, pos, break_chars=[' ', '\t', '%', '[', ']'])
                    if next_token.startswith("int_"):
                        if not AsmIntTypes.is_defined_type(next_token):
                            print("ERROR: int of type '%s' is not defined in any plugin. Line: %s" % (next_token, line_num+1))
                            raise ValueError
                        pattern_tokens.append((TokenTypes.INT_TOKEN, next_token))
                    elif next_token.startswith("label_"):
                        if not AsmIntTypes.is_defined_type(next_token):
                            print("ERROR: label of type '%s' is not defined in any plugin. Line: %s" % (next_token, line_num+1))
                            raise ValueError
                        pattern_tokens.append((TokenTypes.LABEL_TOKEN, next_token))
                    else:
                        pattern_tokens.append((TokenTypes.RAW_TOKEN, next_token))

        else:
            print("ERROR: Expected ';' or '|' on line %s, got '%s' instead" % ((line_num+1), first_token))
            raise ValueError

        return DefinitionPattern(pattern_tokens, bitfield_modifiers)

    # Parse and return the list of bitfield modifiers associated with the current token pattern.
    def read_bitfield_modifiers(self, raw_bitfield_modifiers: str, line_num: int) -> List[BitfieldModifier]:

        modifiers_arr = []
        modifiers_str_arr = raw_bitfield_modifiers.split("::")
        for m_str in modifiers_str_arr:
            modifier_string = m_str.replace(" ", "").replace("\t", "")
            modifiers_arr.append(self.parse_modifier_string(modifier_string, line_num))

        return modifiers_arr

    # Parses a single bitfield modifier string and returns a BitfieldModifier object holding its information.
    def parse_modifier_string(self, modifier_string, line_num) -> BitfieldModifier:

        if "=" in modifier_string:
            modifier_arr = modifier_string.split("=")

            if len(modifier_arr) != 2:
                print("ERROR: Unable to parse bitfield modifier '%s' on line %s" % (modifier_string, line_num+1))
                raise ValueError

            bitfield_name = modifier_arr[0]
            if bitfield_name not in self.bitfield_indexes_map:
                print("ERROR: Trying to assign to unknown bitfield '%s' in bitfield modifier on line '%s" % (bitfield_name, line_num+1))
                raise ValueError

            if modifier_arr[1].startswith("%") and modifier_arr[1].endswith("%"):
                placeholder_name = modifier_arr[1][1:-1]
                if placeholder_name.startswith("int_"):
                    if not AsmIntTypes.is_defined_type(placeholder_name):
                        print("ERROR: Unknown bitfield modifier int placeholder '%s' on line %s. Please make sure that this int type is defined in a plugin." % (modifier_arr[1], line_num + 1))
                        raise ValueError
                    return BitfieldModifier(ModifierTypes.INT_PLACEHOLDER, bitfield_name, placeholder_name)
                elif placeholder_name.startswith("label_"):
                    if not AsmIntTypes.is_defined_type(placeholder_name):
                        print("ERROR: Unknown bitfield modifier label placeholder '%s' on line %s. Please make sure that this label type is defined in a plugin." % (modifier_arr[1], line_num + 1))
                        raise ValueError
                    return BitfieldModifier(ModifierTypes.LABEL_PLACEHOLDER, bitfield_name, placeholder_name)
                else:
                    print("ERROR: Unknown type of bitfield modifier placeholder '%s' on line '%s'" % (modifier_arr[1], line_num + 1))
                    raise ValueError

            bitfield_value = self.read_modifier_value(modifier_arr[1])
            if bitfield_value is None:
                print("ERROR: Unable to parse bitfield modifier value '%s' on line %s" % (modifier_arr[1], line_num + 1))
                raise ValueError

            return BitfieldModifier(ModifierTypes.MODIFIER, bitfield_name, bitfield_value)

        else:
            print("ERROR: Unable to parse bitfield modifier '%s' on line %s" % (modifier_string, line_num + 1))
            raise ValueError

    # Validates the value of a bitfield modifier (can only be 1's and 0's). Returns the validated value.
    def read_modifier_value(self, value_string):
        # TODO: Maybe store these values as BitArray instead of a string of 1's and 0's?
        for c in value_string:
            if c == '0' or c == '1':
                continue
            else:
                return None
        return value_string

    # TODO: Detect recursion in spec.
    # Validates the parsed spec for common errors, so they don't crash the assembler later.
    def validate_spec(self):

        if "INSTRUCTION" not in self.spec:
            print("Spec Validation Error: 'INSTRUCTION' instruction definition is not present in spec.")
            raise ValueError

        for insn_defn_name, insn_defn in self.spec.items():
            for pattern in insn_defn.spec_patterns:
                for pattern_item in pattern.token_patterns:
                    if pattern_item[0] == TokenTypes.PLACEHOLDER:
                        if pattern_item[1] not in self.spec:
                            print("Spec Validation Error: Instruction definition '%s' defined on line %s uses placeholder for undefined instruction definition '%s'" % (insn_defn_name, insn_defn.line_num+1, pattern_item[1]))
                            raise ValueError

        return
