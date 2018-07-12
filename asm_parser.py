
from asm_grammar_spec import AsmGrammarSpec, AsmInstructionDefinition, TokenTypes


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
        
        return