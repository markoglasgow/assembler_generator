from asm_grammar_spec import AsmGrammarSpec
from asm_parser import AsmParser
from bitstream_gen import BitstreamGenerator
from ast_utils import pretty_print_ast
from asm_int_types import AsmIntTypes
from obj_writer import ObjectWriter

from capstone import *

TEST_NAME = "sigma16"
DISASSEMBLER = None
INPUT_EXPECTED_DISASM_LISTING = ""

# TEST_NAME = "test_x86"
# DISASSEMBLER = Cs(CS_ARCH_X86, CS_MODE_32)

# TEST_NAME = "test_ARM"
# DISASSEMBLER = Cs(CS_ARCH_ARM, CS_MODE_ARM)

INPUT_ASM_GRAMMAR_SPEC = "test/%s_spec.txt" % TEST_NAME

# INPUT_ASM_LISTING = "test/%s_listing.txt" % TEST_NAME
# INPUT_EXPECTED_DISASM_LISTING = "test/%s_disasm.txt" % TEST_NAME

# INPUT_ASM_LISTING = "test/osx_x86_hello_world.txt"

INPUT_ASM_LISTING = "test/sigma16_Add.asm.txt"

INPUT_BIN_TEMPLATE = "bin_templates/osx/x86/HelloWorld32"
OUTPUT_BIN = "out.exe"


def check_disassembly(raw_bytes):
    disassembly_str = ""
    for (address, size, mnemonic, op_str) in DISASSEMBLER.disasm_lite(raw_bytes, 0x1000):
        disassembly_str += "0x%x:\t%s\t%s\n" % (address, mnemonic, op_str)

    disassembly_str += "\n"

    with open(INPUT_EXPECTED_DISASM_LISTING, "r") as text_file:
        expected_disassembly = text_file.read()

    if disassembly_str != expected_disassembly:
        print("ERROR: Expected disassembly in '%s' does not match given disassembly: " % INPUT_EXPECTED_DISASM_LISTING)
        print(disassembly_str)
        raise ValueError

    print(disassembly_str)

    return


def main():

    AsmIntTypes.load_plugins()

    asm_grammar = AsmGrammarSpec()
    asm_grammar.read_spec(INPUT_ASM_GRAMMAR_SPEC)
    print("Read ASM grammar spec ok")

    # asm_parser = AsmParser(asm_grammar)
    asm_parser = AsmParser(asm_grammar, sigma16_labels=True)
    asm_parser.parse_asm_listing(INPUT_ASM_LISTING)
    print("Parsed ASM listing ok")

    print("\n\n")
    pretty_print_ast(asm_parser.ast)
    print("\n\n")

    bits_gen = BitstreamGenerator(asm_grammar, asm_parser.ast, imagebase=0)
    bits_gen.print_debug_bitstream()
    print("\n\n")

    raw_bytes = bits_gen.get_bytes()

    # check_disassembly(raw_bytes)

    # obj_writer = ObjectWriter(raw_bytes)
    # obj_writer.write_object(INPUT_BIN_TEMPLATE, OUTPUT_BIN)


if __name__ == '__main__':
    main()
