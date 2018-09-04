import os
import sys

# This file is a test runner which functions by running the main script and checking the exit code to make sure nothing
# went wrong. It runs tests to assemble different code snippets for the x86, ARM, and Sigma16 architectures, and checks
# the assembled code against an expected disassembly listing where possible.

# To run tests without the disassembler, run with command line argument --without-disasm. Otherwise by default tests
# will run without checking disassembler output.
# Note that disassembly is done with Capstone. Make sure that Capstone is uncommented in requirements.txt, and that
# ENABLE_DISASSEMBLER is set to True in main.py to enable Capstone.


def with_disasm():
    test_string = """
        -s
        test/test_x86_spec.txt
        -a
        test/test_x86_listing.txt
        --print-ast
        --print-bitstream
        --imagebase=0x1000
        --print-disasm
        --disasm-arch=x86
        --check-disasm=test/test_x86_disasm.txt
        """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
            -s
            test/test_ARM_spec.txt
            -a
            test/test_ARM_listing.txt
            --print-ast
            --print-bitstream
            --imagebase=0x1000
            --print-disasm
            --disasm-arch=arm
            --check-disasm=test/test_ARM_disasm.txt
            """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                -s
                test/sigma16_spec.txt
                -a
                test/sigma16_Write.asm.txt
                --sigma16-labels
                --print-ast
                --print-bitstream
                --imagebase=0
                --write-sigma16=out.exe
                """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                    -s
                    test/sigma16_spec.txt
                    -a
                    test/sigma16_Add.asm.txt
                    --sigma16-labels
                    --print-ast
                    --print-bitstream
                    --imagebase=0
                    --write-sigma16=out.exe
                    """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                        -s
                        test/test_x86_spec.txt
                        -a
                        test/osx_x86_hello_world.txt
                        --print-ast
                        --print-bitstream
                        --imagebase=0x1000
                        --print-disasm
                        --disasm-arch=x86
                        --check-disasm=test/osx_x86_hello_world_disasm.txt
                        --write-object=out.exe
                        --template-path=bin_templates/osx/x86/HelloWorld32
                        """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                            -s
                            test/test_x86_spec.txt
                            -a
                            test/linux_x86_hello_world.txt
                            --print-ast
                            --print-bitstream
                            --imagebase=0x1000
                            --print-disasm
                            --disasm-arch=x86
                            --check-disasm=test/linux_x86_hello_world_disasm.txt
                            --write-object=out.exe
                            --template-path=bin_templates/linux/x86/HelloWorld32
                            """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
            -s
            test/test_x86_spec.txt
            -a
            test/windows_x86_hello_world.txt
            --print-ast
            --print-bitstream
            --imagebase=0x1000
            --print-disasm
            --disasm-arch=x86
            --check-disasm=test/windows_x86_hello_world_disasm.txt
            --write-object=out.exe
            --template-path=bin_templates/windows/x86/HelloWorld32
            """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    return


def without_disasm():
    test_string = """
            -s
            test/test_x86_spec.txt
            -a
            test/test_x86_listing.txt
            --print-ast
            --print-bitstream
            --imagebase=0x1000
            """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                -s
                test/test_ARM_spec.txt
                -a
                test/test_ARM_listing.txt
                --print-ast
                --print-bitstream
                --imagebase=0x1000
                """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                    -s
                    test/sigma16_spec.txt
                    -a
                    test/sigma16_Write.asm.txt
                    --sigma16-labels
                    --print-ast
                    --print-bitstream
                    --imagebase=0
                    --write-sigma16=out.exe
                    """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                        -s
                        test/sigma16_spec.txt
                        -a
                        test/sigma16_Add.asm.txt
                        --sigma16-labels
                        --print-ast
                        --print-bitstream
                        --imagebase=0
                        --write-sigma16=out.exe
                        """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                            -s
                            test/test_x86_spec.txt
                            -a
                            test/osx_x86_hello_world.txt
                            --print-ast
                            --print-bitstream
                            --imagebase=0x1000
                            --write-object=out.exe
                            --template-path=bin_templates/osx/x86/HelloWorld32
                            """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                                -s
                                test/test_x86_spec.txt
                                -a
                                test/linux_x86_hello_world.txt
                                --print-ast
                                --print-bitstream
                                --imagebase=0x1000
                                --write-object=out.exe
                                --template-path=bin_templates/linux/x86/HelloWorld32
                                """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    test_string = """
                -s
                test/test_x86_spec.txt
                -a
                test/windows_x86_hello_world.txt
                --print-ast
                --print-bitstream
                --imagebase=0x1000
                --write-object=out.exe
                --template-path=bin_templates/windows/x86/HelloWorld32
                """
    test_string = test_string.replace("\n", " ")
    if os.system("python main.py " + test_string) != 0:
        return

    return


def main():

    if len(sys.argv) >= 2 and sys.argv[1] == '--without-disasm':
        without_disasm()
        return
    else:
        with_disasm()
        return


if __name__ == '__main__':
    main()
