from asm_grammar_spec import AsmGrammarSpec
from asm_parser import AsmParser
from bitstream_gen import BitstreamGenerator
from ast_utils import pretty_print_ast
from asm_int_types import AsmIntTypes
from obj_writer import ObjectWriter
from optparse import OptionParser

ENABLE_DISASSEMBLER = True

if ENABLE_DISASSEMBLER:
    from capstone import *

#TEST_NAME = "sigma16"
#INPUT_ASM_GRAMMAR_SPEC = "test/%s_spec.txt" % TEST_NAME
#IMAGEBASE = 0
#DISASSEMBLER = None
#INPUT_EXPECTED_DISASM_LISTING = ""
#INPUT_ASM_LISTING = "test/sigma16_Write.asm.txt"
#INPUT_ASM_LISTING = "test/sigma16_Add.asm.txt"

##################################################

#IMAGEBASE = 0x1000
#TEST_NAME = "test_x86"
#

# TEST_NAME = "test_ARM"

#INPUT_ASM_GRAMMAR_SPEC = "test/%s_spec.txt" % TEST_NAME
#
#INPUT_ASM_LISTING = "test/%s_listing.txt" % TEST_NAME
#INPUT_EXPECTED_DISASM_LISTING = "test/%s_disasm.txt" % TEST_NAME

##################################################

#IMAGEBASE = 0x1000
#INPUT_EXPECTED_DISASM_LISTING = "test/osx_x86_hello_world_disasm.txt"
#INPUT_ASM_GRAMMAR_SPEC = "test/test_x86_spec.txt"
#INPUT_ASM_LISTING = "test/osx_x86_hello_world.txt"
#INPUT_BIN_TEMPLATE = "bin_templates/osx/x86/HelloWorld32"
#OUTPUT_BIN = "out.exe"

##################################################

#IMAGEBASE = 0x08048310
#INPUT_EXPECTED_DISASM_LISTING = "test/linux_x86_hello_world_disasm.txt"
#INPUT_ASM_GRAMMAR_SPEC = "test/test_x86_spec.txt"
#INPUT_ASM_LISTING = "test/linux_x86_hello_world.txt"
#INPUT_BIN_TEMPLATE = "bin_templates/linux/x86/HelloWorld32"
#OUTPUT_BIN = "out.exe"

##################################################

# IMAGEBASE = 0x00401000
# INPUT_EXPECTED_DISASM_LISTING = "test/windows_x86_hello_world_disasm.txt"
# INPUT_ASM_GRAMMAR_SPEC = "test/test_x86_spec.txt"
# INPUT_ASM_LISTING = "test/windows_x86_hello_world.txt"
# INPUT_BIN_TEMPLATE = "bin_templates/windows/x86/HelloWorld32"
# OUTPUT_BIN = "out.exe"


def check_disassembly(raw_bytes, opts):

    if ENABLE_DISASSEMBLER and (opts.print_disasm or opts.disasm_path):
        disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
        if opts.disasm_arch == "arm":
            disassembler = Cs(CS_ARCH_ARM, CS_MODE_ARM)

        disassembly_str = ""
        for (address, size, mnemonic, op_str) in disassembler.disasm_lite(raw_bytes, opts.imagebase):
            disassembly_str += "0x%x:\t%s\t%s\n" % (address, mnemonic, op_str)

        disassembly_str += "\n"

        if opts.disasm_path:
            with open(opts.disasm_path, "r") as text_file:
                expected_disassembly = text_file.read()

            if disassembly_str != expected_disassembly:
                print("ERROR: Expected disassembly in '%s' does not match given disassembly: " % opts.disasm_path)
                print(disassembly_str)
                raise ValueError

        if opts.print_disasm:
            print(disassembly_str)

    return


def load_args():

    parser = OptionParser()

    parser.add_option("-s", "--spec-file", dest="spec_path",
                      help="Spec file of architecture being assembled. REQUIRED", metavar="FILE")

    parser.add_option("-a", "--asm-file", dest="asm_path",
                      help="Assembly source code file to be assembled. REQUIRED", metavar="FILE")

    parser.add_option("--sigma16-labels",
                      action="store_true", dest="sigma16_labels", default=False,
                      help="Parse labels as Sigma16 labels.")

    parser.add_option("--print-ast",
                      action="store_true", dest="print_ast", default=False,
                      help="Print AST of parsed assembly code.")

    parser.add_option("--print-bitstream",
                      action="store_true", dest="print_bitstream", default=False,
                      help="Print debug info about generated bitstream.")

    parser.add_option("--imagebase",
                      type=int, dest="imagebase", default=0x1000,
                      help="Specify memory address that generated code will be loaded at.")

    parser.add_option("--print-disasm",
                      action="store_true", dest="print_disasm", default=False,
                      help="Print disassembly of assembled machine code. Requires that ENABLE_DISASSEMBLER be set to \
                       'True' in main.py, and for Capstone dependency to be installed. --disasm-arch option must also \
                        be set if this option is set. \
                      ")

    parser.add_option("--disasm-arch",
                      type=str, dest="disasm_arch", default="",
                      help="""Specifies architecture of the disassembler. Possible options are 'x86' and 'arm'.""")

    parser.add_option("--check-disasm", dest="disasm_path",
                      help="Checks disassembly of generated machine code against a text file. Throws error if the \
                      listings don't match. Used for testing. --disasm-arch option must also be set if this option is set. \
                      ", metavar="FILE")

    parser.add_option("--write-bin", dest="bin_path",
                      help="""Specifies file where bytes of assembled machine code should be saved. """, metavar="FILE")

    parser.add_option("--write-sigma16", dest="sigma16_path",
                      help="""Specifies file where assembled sigma16 bytecode should be saved. """, metavar="FILE")

    parser.add_option("--write-object", dest="template_out_path",
                      help="Specifies output path of object file. Object file is generated by inserting assembled \
                                machine code into a template object file. Template object file that machine code will \
                                be inserted into must be specified via --write-template. \
                                  ", metavar="FILE")

    parser.add_option("--template-path", dest="template_in_path",
                      help="Path to template object file into which machine code will be inserted. Must be specified \
                                if --write-object is specified. By default, object templates are located in the \
                                bin_templates folder \
                           ", metavar="FILE")

    (opts, args) = parser.parse_args()

    error_str = ""

    if opts.spec_path is None:
        error_str += "ERROR: --spec-file is required\n"
    if opts.asm_path is None:
        error_str += "ERROR: --asm-file is required\n"

    if opts.print_disasm and opts.disasm_arch is None:
        error_str += "ERROR: If --print-disasm is set, --disasm-arch must also be set\n"

    if opts.disasm_path and opts.disasm_arch is None:
        error_str += "ERROR: If --check-disasm is set, --disasm-arch must also be set\n"

    if opts.template_out_path and not opts.template_in_path:
        error_str += "ERROR: If --write-object is set, --template-path must also be set\n"

    if not ENABLE_DISASSEMBLER and (opts.print_disasm or opts.disasm_arch or opts.disasm_path):
        error_str += "ERROR: Disassembler is not enabled. Please set ENABLE_DISASSEMBLER to 'True' in main.py, and" \
                     "make sure that Captstone has been installed. You can do this by uncommenting Capstone in requirements.txt" \
                     "and then rerunning 'pip install -r requirements.txt'"

    if len(opts.disasm_arch) > 0 and opts.disasm_arch != "x86" and opts.disasm_arch != "arm":
        error_str += "ERROR: --disasm-arch can only be 'x86' or 'arm'"

    if len(error_str) > 0:
        print("")
        print(error_str)
        print("====================================\n")

        parser.print_help()
        return None

    return opts


def main():

    opts = load_args()
    if opts is None:
        return

    bin_path = None
    if not opts.bin_path and not opts.sigma16_path and not opts.template_out_path:
        bin_path = "default.out"

    AsmIntTypes.load_plugins()

    asm_grammar = AsmGrammarSpec()
    asm_grammar.read_spec(opts.spec_path)
    print("Read ASM grammar spec ok")

    asm_parser = AsmParser(asm_grammar, sigma16_labels=opts.sigma16_labels)
    asm_parser.parse_asm_listing(opts.asm_path)
    print("Parsed ASM listing ok")

    if opts.print_ast:
        print("\n\n")
        pretty_print_ast(asm_parser.ast)
        print("\n\n")

    bits_gen = BitstreamGenerator(asm_grammar, asm_parser.ast, imagebase=opts.imagebase)
    if opts.print_bitstream:
        bits_gen.print_debug_bitstream()
        print("\n\n")

    raw_bytes = bits_gen.get_bytes()

    check_disassembly(raw_bytes, opts)

    obj_writer = ObjectWriter(raw_bytes)

    if opts.bin_path:
        obj_writer.write_bin(opts.bin_path)
    if bin_path:
        obj_writer.write_bin(bin_path)
    if opts.sigma16_path:
        obj_writer.write_sigma16_data(opts.sigma16_path)
    if opts.template_out_path and opts.template_in_path:
        obj_writer.write_object(opts.template_in_path, opts.template_out_path)

    return


if __name__ == '__main__':
    main()
