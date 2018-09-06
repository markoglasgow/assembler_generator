# A Generic Assembler Generator

The generic assembler generator, or generic assembler for short, is an assembler capable of producing machine code for any custom architecture specified by the user.

The generic assembler takes two inputs:
  - An architecture specification written in a custom ADL (architecture description language).
  - An assembly source code file.
  
Its output is the binary machine code of the assembled code.

To get the generic assembler up and running on your machine, check out the [Installation](#installation) section.

To quickly run some examples see the [Quick Start](#quick-start) section.

To view a detailed walkthrough on specifying your own architecture and then assembling machine code for it, check out the [Tutorial](#tutorial) section.

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

Upon executing this command, you will see three different types of output in the terminal, and a file called `out.exe` will be created in the current directory. You can execute `out.exe` and it should return without doing anything (indicating that it ran and exited cleanly, which is what the test assembly program is supposed to do).

The first type of output visible in the terminal will be a debug representation of the AST. The AST node of each parsed instruction will be present, indicating which token patterns were matched when parsing the instruction, and which bitfield modifiers are set for each token pattern. For example:

```
push ecx
INSTRUCTION                                                                                                             
    PUSH_INSTRUCTION    :: short_opcode=01010 
        'push'                                                                                                          
        32_BIT_REG      :: reg=001 
            'ecx'    
```

... indicates that `push ecx` was parsed as a `PUSH_INSTRUCTON` with a `push` raw token, and a `32_BIT_REG` which was resolved to be `ecx`. The following bitfield modifiers are set due to the token patterns which were matched:

  - `short_opcode`=`01010 `
  - `reg`=`001 `

The second type of output visible in the terminal is the debug info of the bitstream generator. This shows for each instruction what bitfields are set to what value, and what the output bytes are. For example:

```
push ecx
  short_opcode    reg
--------------  -----
         01010    001
Bytes (padded): 
51 
```

... indicates that the `push ecx` instruction has two bitfields set:
  - `short_opcode`=`01010 `
  - `reg`=`001 `

These bitfields when put together into a bitstream generate the hexadecimal `0x51h` byte, which is the correct machine code for the `push ecx` instruction.

The final type of output present in the terminal is the Capstone disassembly of the assembled machine code:

```
0x1000:	push	1
0x1005:	push	ecx
0x1006:	pop	ecx
0x1007:	pop	eax
0x1008:	jmp	0x100e
0x100d:	nop	
0x100e:	ret
```

This is a useful sanity check which lets you make sure that the outputted machine code matches the input assembly source code.

This concludes the tutorial. In this tutorial we saw:
  - how to define an architecture using the custom ADL
  - how to write a small assembly program using the architecture
  - how to pass the architecture spec and the assembly code to the generic assembler for assembling
  - how to interpret and use the output of the generic assembler.

For more information on the different features of the generic assembler, please see the [Documentation](#documentation) section below.

--------

## Documentation

### Custom ADL

The custom ADL (architecture description language) is used to specify the assembly language syntax and machine code generation rules that will be used by the generic assembler to assemble machine code for an architecture. The custom ADL is divided into two sections, and is passed to the generic assembler as a text file.

The first section of the custom ADL starts with the `.BIT_FIELDS` directive. All statements below the `.BIT_FIELDS` directive will describe a potential bitfield in the encoded instruction. Each bitfield is defined by two text fields spanning two lines. The first is `name`, the other is `size`. For example:

```
name: test
size: 3
```

... will define a bitfield named `test` with a size of `3` bits. The bitfield declarations will continue until the `.ASM_INSTRUCTIONS` directive.

### Instruction Definitions

The `.ASM_INSTRUCTIONS` signals the beginning of the second part of the specification file. In this file, the assembly language syntax will be specified, along with which bitfields should be set to properly encode an instruction.

The second part of the specification is composed of a list of instruction definitions. Each instruction definition takes the following form:

```
DATA_PROCESSING_MNEMONICS =
| add 					:: opcode=0100
| sub 					:: opcode=0010
;
```

The instruction definition is divided into three parts. The first line of each instruction definition begins with the name of the instruction definition, followed by the '=' character.

Underneath the name of the instruction definition are one or more token patterns. Token patterns describe a series of tokens which must be matched for the instruction definition to be correctly identified.

The instruction definition ends with a `;` character on the last line, which indicates the end of the instruction definition.

### Token Patterns

The most important part of each instruction definition are the token patterns. There are 4 different types of token patterns:

  - raw tokens - strings of characters which must be matched
  - placeholder tokens - placeholders which will be expanded into other instruction definitions
  - int tokens - indicating an integer should be present at this point in the token pattern. The verification and bitstream generation of the integer is usually handled by a plugin.
  - label tokens - indicating that a reference to a label should be present at this point in the token pattern. Again, bitstream generation for labels is handled by the plugin system.

Raw tokens are the simplest, and are simply a string of characters which must be present for a token pattern to be a match. For example, in the following instruction definition:

```
DATA_PROCESSING_MNEMONICS =
| add 					:: opcode=0100
| sub 					:: opcode=0010
;
```

`add` and `sub` are raw tokens.

Placeholder tokens are the name of some other instruction definition, surrounded by % characters. The generic assembler will automatically expand placeholder tokens using the token patterns from the other specified instruction definition. For example:

```
PUSH_INSTRUCTION = 
| push %32_BIT_REG%								:: short_opcode=0101 0
;

32_BIT_REG =
| eax                                           :: reg=000
| ecx                                           :: reg=001
;
```

`%32_BIT_REG%` is a placeholder token for the `32_BIT_REG` instruction definition. This placeholder token is expanded into two raw token patterns which match `eax` and `ecx`. Thus the above instruction definitions will match both the `push eax` and `push ecx` instructions. 

Placeholder tokens are useful for eliminating repetition in specs and reusing certain instructions definitions across multiple different instructions. 

Int tokens look like raw tokens, except they begin with the `int_` prefix. Similary, label tokens look like raw tokens, except they begin with the 'label_' prefix. In both cases, the bitfields for these data types are calculated by the plugin system. For example:

```
32_BIT_IMMEDIATE = 
| int_32_bits                                   :: immediate_32=%int_32_bits%
| label_x86_imm_32_bits                         :: immediate_32=%label_x86_imm_32_bits%
;
```
  
`32_BIT_IMMEDIATE` has two token patterns, one which matches an `int` called `int_32_bits`, while the other matches a `label` called `label_x86_imm_32_bits`. The bitfields for both of these will be emitted by a plugin.

### Bitfield Modifiers

In all of the above examples, token patterns had a list on the right of the token pattern, delimited with `::` characters. These are lists of 'bitfield modifiers'. A bitfield modifier has the following structure:

`name=value`

Where `name` is a bitfield name, and `value` is a string of 1's and 0's which specify what binary value the bitfield will be set to. The `name` of the bitfield must match some bitfield name declared in the `.BIT_FIELDS` section of the custom ADL. 

The bitfield modifiers indicate to the generic assembler which bitfields should be set in an instruction if a token pattern is matched. If a bitfield is not referenced by a bitfield modifier, it will be ignored during instruction bitstream generation.

While most bitfield modifiers have values which are simply strings of 1's and 0's, in rare cases, the bitfield modifier values can be calculated by the plugin system. For example: 

```
32_BIT_IMMEDIATE = 
| int_32_bits                                   :: immediate_32=%int_32_bits%
| label_x86_imm_32_bits                         :: immediate_32=%label_x86_imm_32_bits%
;
```

In this snippet, the `immediate_32` bitfield value is either emitted as an `int_32_bits` calculated by a plugin, or a `label_x86_imm_32_bits` calculated by a plugin. How the plugin system calculates the values of bitfields is described in the following section.

### The Plugin System

The plugin system allows users to write Python plugins to help parse and emit bitstreams for ints and labels. To create a plugin, the user must create a `*.py` file in the `plugins` folder, and a `*.yapsy-plugin` file with the same name.

The `*.yapsy-plugin` file is just metadata, and should use the following template:

```
[Core]
Name = Builtin Types
Module = builtin_types

[Documentation]
Author = Marko Caklovic
Version = 1.0
Website = https://github.com/markoglasgow
Description = Builtin types parser and emitter for the Generic Assembler Generator
```

The `*.py` file needs to implement a class which inherits from the Yapsy  `IPlugin` interface. The implemented class must have the following properties:

It must implement a function called `get_registered_types` which takes no parameters, and returns a `Dict[str:bool]`, where each string key is the name of a data type it supports.

The name of each data type must begin with either `int_` or `label_`. `int_` indicates the data type is an `int` and fulfills the `int` interface, while `label_` indicates the data type is a `label` and fulfills the `label` interface.

To fulfill the `int` interface, the plugin must define the following functions:

`chars_<name of data type>` - takes no parameters, returns a list of allowed characters for the string representation of this int type.

`verify_<name of data type>` - takes a string parameter, which is the string representation of int data type parsed from the assembly source code. Returns a `bool` indicating whether or not the string is a valid representation of the int data type.

`emit_<name of data type>` - takes a string parameter, which is the string representation of int data type parsed from the assembly source code. Returns a bit string which is the bitwise representation of the integer. This bit string is ultimately embedded in the bitstream of the instruction.

To fulfill the `label` interface, the plugin must only define the following function:

`calc_<name of data type>` - takes 2 int parameters. The first parameter is the memory address of the instruction which is referencing the label, while the second parameter is the memory address of the label itself. The return value is a bit string representing the memory address/offset which should be embedded in the instruction bitstream.

Example implementations for all of the above methods are available in `plugins/builtin_types.py`

### Command Line Parameters

The following is a list of all command line parameters, followed by a description for each one:

  `-s FILE, --spec-file=FILE`        Spec file of architecture being assembled. REQUIRED
  `-a FILE, --asm-file=FILE`        Assembly source code file to be assembled. REQUIRED
  
  `--sigma16-labels`     Parse labels as Sigma16 labels.
  
  `--print-ast`           Print AST of parsed assembly code.
  
  `--print-bitstream`     Print debug info about generated bitstream.
  
  `--imagebase=IMAGEBASE`        Specify memory address that generated code will be loaded at.
  
  `--print-disasm`        Print disassembly of assembled machine code. Requires that ENABLE_DISASSEMBLER be set to 'True' in main.py, and for Capstone dependency to be installed. --disasm-arch option must also be set if this option is set.
  
  `--disasm-arch=DISASM_ARCH`        Specifies architecture of the disassembler. Possible options are 'x86' and 'arm'.
  
  `--check-disasm=FILE`        Checks disassembly of generated machine code against a text file. Throws error if the listings don't match. Used for testing. --disasm-arch option must also be set if this option is set.
  
  `--write-bin=FILE`        Specifies file where bytes of assembled machine code should be saved.
  
  `--write-sigma16=FILE`        Specifies file where assembled sigma16 bytecode should be saved.
  
  `--write-object=FILE`        Specifies output path of object file. Object file is generated by inserting assembled machine code into a template object file. Template object file that machine code will be inserted into must be specified via --write-template.
  
  `--template-path=FILE`        Path to template object file into which machine code will be inserted. Must be specified if --write-object is specified. By default, object templates are located in the bin_templates folder

### Object Template Files

The generic assembler ships with OSX, Linux, and Windows template object files. These are object files with code caves in them, which can be overwritten by machine code generated by the generic assembler. If specified via command line parameters, the generic assembler can automatically inject machine code into these template object files, allowing the user to execute the generated object file to test their assembled machine code.

The object file templates are located in the `bin_templates` folder of the generic assempler. Each object template has a `*.info` file in the same folder, which is a text file with two lines, for example:

```
0x00000310
0x000005c2
```

... where the first line is a decimal or hexadecimal file offset where the generated machine code should be injected, and the second line is the maximum size of the generated machine code that can be injected.

--------
