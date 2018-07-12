from asm_grammar_spec import AsmGrammarSpec
from asm_parser import AsmParser

INPUT_ASM_GRAMMAR_SPEC = "test_x86_spec.txt"
INPUT_ASM_LISTING = "test_x86_listing.txt"


def main():
    asm_grammar = AsmGrammarSpec()
    asm_grammar.read_spec(INPUT_ASM_GRAMMAR_SPEC)

    #asm_parser = AsmParser(asm_grammar)
    #asm_parser.parse_asm_listing(INPUT_ASM_LISTING)

    print("Read ASM grammar spec ok")


if __name__ == '__main__':
    main()
