# A Generic Assembler Generator

The generic assembler generator, or generic assembler for short, is an assembler capable of producing machine code for any custom architecture specified by the user.

The generic assembler takes two inputs:
  - An architecture specification written in a custom ADL (architecture description language).
  - An assembly source code file.
  
Its output is the binary machine code of the assembled code.

To get the generic assembler up and running on your machine, check out the [Installation](#installation) section.

To quickly run some examples see the [Quick Start](#quick-start) section.

To view a short walkthrough on specifying your own architecture and then assembling machine code for it, check out the [Tutorial](#tutorial) section.

To view the documentation, check out the [Documentation](#documentation) section.

--------

## Installation

### OSX Installation

Before installing, make sure Python and Xcode are installed. Then `cd` to the directory where the code is located, and execute the following commands to set up a virtual environment with the program dependencies installed in it:

```sh
$ python3 -m venv env/
$ source env/bin/activate
$ pip install -r requirements.txt
```

### Linux (Ubuntu) Installation

`cd` to the directory where the code is located, and execute the following commands to install all dependencies and set up a virtual environment:

```sh
$ sudo apt-get update
$ sudo apt-get install build-essential python3 python3-venv
$ python3 -m venv env/
$ source env/bin/activate
$ pip install wheel
$ pip install -r requirements.txt
```

### Windows Installation

Before installing, make sure Python 3 for Windows (https://www.python.org/downloads/windows/) is installed and available in the PATH. Then `cd` to the directory where the code is located, and execute the following commands to set up a virtual environment with the program dependencies installed in it:

```sh
> python -m venv env/
> env\Scripts\activate.bat
> pip install -r requirements_windows.txt
```

### After Installation

After installation, run the following command to run all tests to make sure everything is working properly:

```sh
$ python run_tests.py
```

If you had problems installing the Capstone dependency, you can edit `main.py` to set `ENABLE_DISASSEMBLER = False`, and then run the tests without the disassembler like so:

```sh
$ python run_tests.py --without-disasm
```

### Installation Problems?

The generic assembler uses the Capstone disassembler library for some tests to disassemble generated machine code and make sure it was assembled correctly. If you have problems installing Capstone on your machine, please consult their documentation here: https://www.capstone-engine.org/documentation.html

Otherwise you can run the generic assembler without Capstone support by editing `main.py` and setting `ENABLE_DISASSEMBLER = False` at the top of the file. Note that this will disable all features and tests which rely on the disassembler.

--------

## Quick Start

### Quick Start OSX

To use the generic assembler to assemble a "Hello World" x86 program and generate a test binary, execute the following command:
`python main.py -s test/test_x86_spec.txt -a test/osx_x86_hello_world.txt --print-ast --print-bitstream --imagebase=0x1000 --print-disasm --disasm-arch=x86 --check-disasm=test/osx_x86_hello_world_disasm.txt --write-object=out.exe --template-path=bin_templates/osx/x86/HelloWorld32`

To then execute the generated binary:
`chmod a+x out.exe; ./out.exe`

You should see the following output:
`HELLO WORLD!`

### Quick Start Linux

To use the generic assembler to assemble a "Hello World" x86 program and generate a test binary, execute the following command:
`python main.py -s test/test_x86_spec.txt -a test/linux_x86_hello_world.txt --print-ast --print-bitstream --imagebase=0x1000 --print-disasm --disasm-arch=x86 --check-disasm=test/linux_x86_hello_world_disasm.txt --write-object=out.exe --template-path=bin_templates/linux/x86/HelloWorld32`

To then execute the generated binary:
`chmod a+x out.exe; ./out.exe`

You should see the following output:
`HELLO WORLD!`

### Quick Start Windows

To use the generic assembler to assemble a "Hello World" x86 program and generate a test binary, execute the following command:
`python main.py -s test/test_x86_spec.txt -a test/windows_x86_hello_world.txt --print-ast --print-bitstream --imagebase=0x1000 --print-disasm --disasm-arch=x86 --check-disasm=test/windows_x86_hello_world_disasm.txt --write-object=out.exe --template-path=bin_templates/windows/x86/HelloWorld32`

To then execute the generated binary:
`out.exe`

You should see the following output:
`HELLO WORLD!`

--------

## Tutorial

The following tutorial will walk you through specifying a subset of the x86 architecture using the custom ADL, assembling code with the generic assembler using this spec, and optionally running it. Please make sure you have set up all dependencies and have a terminal open in an activated Python virtualenv, as described in the [Installation](#installation) section.

### Specifying the x86 subset

We will begin by specifying a subset of the x86 architecture using the custom ADL which includes the `push`, `pop`, `jmp`, and `ret` instructions. Create a file called `x86_subset.txt` in the `test` folder. 

Populate the file with the following contents:

```

////////////////////////////////////////
.BIT_FIELDS

name: short_opcode
size: 5

name: full_opcode
size: 8

name: opcode
size: 6

name: opcode_d
size: 1

name: opcode_s
size: 1

name: reg
size: 3

name: immediate_32
size: 32

////////////////////////////////////////
.ASM_INSTRUCTIONS

INSTRUCTION = 
| %JUMP_IMMEDIATE%
| %PUSH_INSTRUCTION%
| %POP_REG%
| %TINY_INSTRUCTION%
;

JUMP_IMMEDIATE =
| jmp label_x86_rel_32_bit_branch               :: opcode=1110 10 :: opcode_d=0 :: opcode_s=1 :: immediate_32=%label_x86_rel_32_bit_branch%
;

PUSH_INSTRUCTION = 
| push %32_BIT_REG%								:: short_opcode=0101 0
| push %32_BIT_IMMEDIATE%                       :: opcode=0110 10 :: opcode_d=0 :: opcode_s=0
;

POP_REG = 
| pop %32_BIT_REG%								:: short_opcode=0101 1
;

TINY_INSTRUCTION = 
| ret 											:: full_opcode=1100 0011
| nop 											:: full_opcode=1001 0000
;

32_BIT_REG =
| eax                                           :: reg=000
| ecx                                           :: reg=001
;

32_BIT_IMMEDIATE = 
| int_32_bits                                   :: immediate_32=%int_32_bits%
| label_x86_imm_32_bits                         :: immediate_32=%label_x86_imm_32_bits%
;

```

The `BIT_FIELDS` directive indicates that the bitfields will be defined beneath in that section of the file. Each bitfield must have a `name`, followed by `size` on the next line. `name` is the name that the bitfield will be referred to with, while `size` is the number of bits that make up this bitfield.

In this example, only a limited number of x86 bitfields are defined. There are 3 types of x86 instructions which can be defined with these bitfields:

  - `full_opcode` which defines an instruction that takes up a single byte and has no operands. In this case they are `ret` and `nop`
  - `short_opcode` which defines an instruction with a single register operand, followed by `reg` which defines the register being used. Examples are `push eax` and `pop eax`
  - `opcode`, `opcode_d`, and `opcode_s` are bitfields present in most x86 instructions, followed by `immediate_32` which is a 32 bit immediate field. In this example, the immediate field will hold either the contents of a `push` instruction, or the relative offset of a `branch` instruction.
 
The `ASM_INSTRUCTIONS` directive indicates that instruction definitions will be defined below in that section of the file.

The very first instruction definition which must always be defined is the `INSTRUCTION` instruction definition. This instruction definition can then be expanded into other instruction definitions with placeholder tokens. Placeholder tokens are simply the name of an instruction definition surrounded by % characters. In this case, the other types of instruction definitions are:

  - `JUMP_IMMEDIATE`
  - `PUSH_INSTRUCTION`
  - `POP_REG`
  - `TINY_INSTRUCTION`

The `JUMP_IMMEDIATE` definition is for x86 branch instructions. The assembly code for these instructions must begin with the `jmp` instruction, followed by a label.  

To the right of the `jmp` token pattern you will notice a list of elements delimited with `::` characters. This list is called a list of 'bitfield modifiers', and they indicate to the generic assembler what bitfields should be set to what value in the instruction bitstream if this token pattern is matched in the assembly source code. 

Most bitfield modifiers are of the form `name`=`value`, where `name` is the name of some bitfield while `value` is a string of 1's and 0's specifying the binary string which the bitfield should be set to.

In rare cases, such as with the `jmp` token pattern, the bitfield's value cannot be known ahead of time, but must be calculated by a plugin. In this case, the bitfield modifier is specified like so:
`immediate_32=%label_x86_rel_32_bit_branch%`

... which indicates that the `immediate_32` bitfield will be set to some bitstream which is calculated by a plugin which handles the `x86_rel_32_bit_branch` label data type. To see more information about how plugins are used to generate bitstreams see the [Documentation](#documentation)

Note that if a bitfield is not set with a bitfield modifier, it will be ignored during generation of the instruction bitstream.

The `PUSH_INSTRUCTION` instruction definition defines x86 `push` instructions which can either push a 32 bit value to the stack, or the contents of a register. Placeholder tokens are used both for immediate values and registers (`32_BIT_REG` and `32_BIT_IMMEDIATE`). Only the 32 bit `eax` and `ecx` registers are present in this example to keep it simple

`POP_REG` defines x86 `pop register` instructions. It's very simple and of similar form to the `push` instruction definition.

`TINY_INSTRUCTION` defines small 8-bit (1 byte) instructions which have no operands. In this case `nop` and `ret`.

After defining the x86 subset using the custom ADL, lets write some assembly code for it. Create a file called `x86_asm.txt` in the `test` folder, and populate it with the following text:

```
push 1
push ecx
pop ecx
pop eax
jmp _return
nop
_return:
ret
```

This is a simple assembler program which attempts to use all the instructions defined in `x86_subset.txt`. When run it will set `eax` to `1` and then simply return.

To assemble this test program using the x86 subset spec, and inject it into a binary file while printing debug information to the console, execute the following command:

`python main.py -s test/x86_subset.txt -a test/x86_asm.txt --print-ast --print-bitstream --imagebase=0x1000 --print-disasm --disasm-arch=x86  --write-object=out.exe --template-path=bin_templates/osx/x86/HelloWorld32`

Note: you should change `osx` in the `--template-path` argument to either `windows` or `linux` if you're running on those OS.

Here is an explanation of the command line flags:

  - `-s test/x86_subset.txt` Read the custom ADL architecture specification from the 'test/x86_subset.txt' file.
  - `-a test/x86_asm.txt` Read the assembly source code to be assembled from the 'test/x86_asm.txt' file.
  - `--print-ast` Print the AST (abstract syntax tree) of the parsed program. 
  - `--print-bitstream` Print the bitstream debug info when generating the bitsteam of the assembled machine code instructions
  - `--imagebase=0x1000` When assembling the machine code, assume that the machine code will be loaded into memory at location `0x1000`.
  - `--print-disasm` Print the Capstone disassembly of the assembled machine code.
  - `--disasm-arch=x86` Configure the Capstone disassembler to disassemble for the x86 architecture.
  - `--write-object=out.exe` Write an executable binary file called 'out.exe'
  - `--template-path=bin_templates/osx/x86/HelloWorld32` Inject the assembled machine code into the given binary template file at `bin_templates/osx/x86/HelloWorld32`. This expects for a text file to be present at `bin_templates/osx/x86/HelloWorld32.info` containing 2 lines of text. The first line should specify the offset in the binary file where the assembled machine code should be injected, while the second line should specify the maximum possible size of the injected machine code.




--------

## Documentation

--------
