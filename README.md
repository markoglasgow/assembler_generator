# A Generic Assembler Generator

The generic assembler generator, or generic assembler for short, is an assembler capable of producing machine code for any custom architecture specified by the user.

The generic assembler takes two inputs:
  - An architecture specification written in a custom ADL
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

--------

## Documentation

--------
