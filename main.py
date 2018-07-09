from asm_grammar_spec import AsmGrammarSpec

INPUT_ASM_GRAMMAR_SPEC = "test_x86.txt"


def main():
    asm_grammar = AsmGrammarSpec()
    asm_grammar.read_spec(INPUT_ASM_GRAMMAR_SPEC)
    print("Read ASM grammar spec ok")


if __name__ == '__main__':
    main()
