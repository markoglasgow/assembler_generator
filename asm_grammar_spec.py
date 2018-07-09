
from parse_utils import ParseUtils
from enum import Enum


class PatternTypes(Enum):
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
                if p[0] == PatternTypes.PLACEHOLDER:
                    self.only_raw_values = False
        return


class AsmGrammarSpec:

    def __init__(self):
        self.parsed_asm_instruction_types = False
        self.spec = {}
        return

    def read_spec(self, spec_file_path):
        input_file = ""
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

            if line == ".ASM_INSTRUCTIONS":
                if self.parsed_asm_instruction_types:
                    print("ERROR: duplicate .ASM_INSTRUCTIONS directive (line %s)" % line_num)
                    raise ValueError

                self.parse_asm_instructions_spec(line_num, spec_file_lines)
                self.parsed_asm_instruction_types = True
                break

            line_num += 1

        if not self.parsed_asm_instruction_types:
            print("ERROR: .ASM_INSTRUCTIONS directive was not found in spec file!")
            raise ValueError

        return

    def parse_asm_instructions_spec(self, start_line_num, spec_file_lines):

        line_num = start_line_num
        if not spec_file_lines[line_num].startswith(".ASM_INSTRUCTIONS"):
            print("ERROR: Parsing asm instructions directive, but current line doesn't start with .ASM_INSTRUCTIONS (line %s)" % line_num)
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
                    pattern.append((PatternTypes.PLACEHOLDER, placeholder_name))

                elif next_char == ' ':
                    pattern.append((PatternTypes.WHITESPACE, " "))
                    pos = ParseUtils.skip_whitespace(line, pos)

                else:
                    next_token, pos = ParseUtils.read_token(line, pos, break_chars=[' ', '%'])
                    pattern.append((PatternTypes.RAW_TOKEN, next_token))

        else:
            print("ERROR: Expected ';' or '|' on line %s, got '%s' instead" % (line_num, first_token))
            raise ValueError

        return pattern

    def validate_spec(self):

        if "INSTRUCTION" not in self.spec:
            print("Spec Validation Error: 'INSTRUCTION' instruction definition is not present in spec.")
            raise ValueError

        for insn_defn_name, insn_defn in self.spec.items():
            for pattern in insn_defn.spec_patterns:
                for pattern_item in pattern:
                    if pattern_item[0] == PatternTypes.PLACEHOLDER:
                        if pattern_item[1] not in self.spec:
                            print("Spec Validation Error: Instruction definition '%s' defined on line %s uses placeholder for undefined instruction definition '%s'" % (insn_defn_name, insn_defn.line_num, pattern_item[1]))
                            raise ValueError

        return
