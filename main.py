from asm_grammar_spec import AsmGrammarSpec
from asm_parser import AsmParser
from bitstream_gen import BitstreamGenerator
from ast_utils import pretty_print_ast

INPUT_ASM_GRAMMAR_SPEC = "test_x86_spec.txt"
INPUT_ASM_LISTING = "test_x86_listing.txt"

# INPUT_ASM_GRAMMAR_SPEC = "test_ARM_spec.txt"
# INPUT_ASM_LISTING = "test_ARM_listing.txt"


def main():
    asm_grammar = AsmGrammarSpec()
    asm_grammar.read_spec(INPUT_ASM_GRAMMAR_SPEC)
    print("Read ASM grammar spec ok")

    asm_parser = AsmParser(asm_grammar)
    asm_parser.parse_asm_listing(INPUT_ASM_LISTING)
    print("Parsed ASM listing ok")

    print("\n\n")
    pretty_print_ast(asm_parser.ast)
    print("\n\n")

    bits_gen = BitstreamGenerator(asm_grammar, asm_parser.ast)
    bits_gen.print_debug_bitstream()
    print("\n\n")


if __name__ == '__main__':
    main()
