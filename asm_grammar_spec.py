
from parse_utils import ParseUtils
from enum import Enum
from typing import Dict, List


class BitfieldDefinition:

    def __init__(self, name, size):
        self.name = name
        self.size = size
        return


class TokenTypes(Enum):
    WHITESPACE = 1
    RAW_TOKEN = 2
    PLACEHOLDER = 3


class AsmInstructionDefinition:

    def __init__(self, name, line_num):
        self.name = name
        self.line_num = line_num
        self.spec_patterns = []
        self.only_raw_values = True
        return

    def add_pattern(self, pattern):
        self.spec_patterns.append(pattern)

        if self.only_raw_values:
            for p in pattern:
                if p[0] == TokenTypes.PLACEHOLDER:
                    self.only_raw_values = False
        return


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

    def read_spec(self, spec_file_path):
        with open(spec_file_path, "r") as f:
            input_file = f.readlines()

        self.parse_spec(input_file)
        self.validate_spec()

        return

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
                return line_num - 1

            bitfield_name_line_num = line_num
            bitfield_size_line_num = line_num+1

            if bitfield_size_line_num >= len(spec_file_lines):
                print("ERROR: EOL after line %s when attempting to read bitfield size" % (line_num+1))
                raise ValueError

            bitfield_name_line = spec_file_lines[bitfield_name_line_num]
            bitfield_size_line = spec_file_lines[bitfield_size_line_num]

            bitfield_name = self.parse_bitfield_name(bitfield_name_line, bitfield_name_line_num)
            bitfield_size = self.parse_bitfield_size(bitfield_size_line, bitfield_size_line_num)

            self.add_bitfield(BitfieldDefinition(bitfield_name, bitfield_size))

        print("ERROR: .ASM_INSTRUCTIONS is not present in spec file after .BIT_FIELDS")
        raise ValueError

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

        return bitfield_size

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
                print("ERROR: Duplicate instruction definition found: '%s' (line %s)" % (asm_defn.name, instr_defn_line))
                raise ValueError

            self.spec[asm_defn.name] = asm_defn

        return

    def parse_single_asm_instr_defn(self, start_line_num, spec_file_lines):

        line_num = start_line_num
        line = spec_file_lines[line_num].strip()

        definition_name = self.read_asm_defn_name(line, line_num)
        asm_defn = AsmInstructionDefinition(definition_name, line_num)

        line_num += 1

        while line_num < len(spec_file_lines):
            line = spec_file_lines[line_num].strip()
            pattern = None
            if len(line) > 0:
                pattern = self.read_asm_defn_pattern(line, line_num)
            line_num += 1
            if pattern is not None:
                if len(pattern) == 0:
                    break
                else:
                    asm_defn.add_pattern(pattern)

        if len(asm_defn.spec_patterns) == 0:
            print("ERROR: Empty instruction definition on line %s" % start_line_num)
            raise ValueError

        return asm_defn, line_num

    def read_asm_defn_name(self, line, line_num):

        name, pos = ParseUtils.read_identifier(line)

        if len(name) == 0:
            print("ERROR: Unable to read definition identifier on line %s." % line_num)
            raise ValueError

        # Expect a '=' after the identifier
        token, pos = ParseUtils.read_token(line, pos)

        if token != "=":
            print("ERROR: Expected '=' after definition identifier on line %s" % line_num)
            raise ValueError

        return name

    def read_asm_defn_pattern(self, line, line_num):

        pattern = []
        first_token, pos = ParseUtils.read_token(line, 0, break_chars=[' '], valid_chars={"|": "", ";": ""})

        if first_token == ";":
            return []

        elif first_token == "|":
            pos = ParseUtils.skip_whitespace(line, pos)

            while pos < len(line):
                next_char = ParseUtils.read_next_char(line, pos)
                if next_char is None:
                    print("ERROR: Expected asm instruction patterns on line %s after '|'." % line_num)
                    raise ValueError

                elif next_char == '%':
                    pos += 1
                    placeholder_name, pos = ParseUtils.read_identifier(line, pos)
                    next_char = ParseUtils.read_next_char(line, pos)
                    if next_char != "%":
                        print("ERROR: Expected asm definition identifier to be terminated with %% character on line %s." % line_num)
                        raise ValueError
                    pos += 1
                    pattern.append((TokenTypes.PLACEHOLDER, placeholder_name))

                elif next_char == ' ':
                    pattern.append((TokenTypes.WHITESPACE, " "))
                    pos = ParseUtils.skip_whitespace(line, pos)

                else:
                    next_token, pos = ParseUtils.read_token(line, pos, break_chars=[' ', '%'])
                    pattern.append((TokenTypes.RAW_TOKEN, next_token))

        else:
            print("ERROR: Expected ';' or '|' on line %s, got '%s' instead" % (line_num, first_token))
            raise ValueError

        return pattern

    # TODO: Detect recursion in spec.
    def validate_spec(self):

        if "INSTRUCTION" not in self.spec:
            print("Spec Validation Error: 'INSTRUCTION' instruction definition is not present in spec.")
            raise ValueError

        for insn_defn_name, insn_defn in self.spec.items():
            for pattern in insn_defn.spec_patterns:
                for pattern_item in pattern:
                    if pattern_item[0] == TokenTypes.PLACEHOLDER:
                        if pattern_item[1] not in self.spec:
                            print("Spec Validation Error: Instruction definition '%s' defined on line %s uses placeholder for undefined instruction definition '%s'" % (insn_defn_name, insn_defn.line_num, pattern_item[1]))
                            raise ValueError

        return
