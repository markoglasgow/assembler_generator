import os


def main():

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


if __name__ == '__main__':
    main()
