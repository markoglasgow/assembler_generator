from asm_grammar_spec import AsmGrammarSpec, TokenTypes, ModifierTypes, BitfieldModifier
from asm_parser import ASTNode
from asm_int_types import AsmIntTypes

from typing import List, Dict

from tabulate import tabulate
from bitstring import BitArray


DEFAULT_IMAGEBASE = 0x1000
DEFAULT_BYTE_BITSIZE = 8

# This module is responsible for generating the actual bitstream which is the machine code output of the assembler. The
# module works by taking the bitfield definitions from the spec, and the AST from the parser. Then for each line, it
# walks across each AST node of that line, and applies any bitfield modifiers that node might have to the possible
# bitfields of an instruction. Finally it generates the bitstream from all bitfields which had modifiers applied to them.

# Object which keeps track of the name of a bitfield, its size, the value it might be set to, and whether or not it
# is present in the final bitstream of the instruction.
class Bitfield:

    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.value = None
        self.present = False

    def set_value(self, value):
        self.value = value
        self.present = True


# Singleton class responsible for generating the bitstream from the spec and the AST.
class BitstreamGenerator:

    # spec - used to list of possible bitfields in an instruction
    # ast - list of ASTNodes, where each ASTNode corresponds to parsed line of assembly code
    # imagebase - memory address at which the generated machine code is expected to be loaded. Used for calculating
    #               label addresses/offsets correctly.
    def __init__(self, spec: AsmGrammarSpec, ast: List[ASTNode], imagebase=DEFAULT_IMAGEBASE):
        self.spec = spec
        self.ast = ast
        self.imagebase = imagebase
        return

    # Calculate the bitstream, and return an array of bytes containing the bitstream. Works in 2 passes.
    # 1st pass (1st loop) - Calculate bitstream for each instruction, and assign it a memory address. If the instruction
    #                       has an associated label, associate that label with the instruction's memory address. This lets
    #                       us later look up this address as the destination of the label
    # 2nd pass (2nd loop) - Update placeholder values for labels  in the bitstream with actual values of correct bits pointing to correct
    #                       memory addresses/offset for references to said labels. The correct bits are calculated by a plugin
    # 3rd loop            - Build final bitstream which contains updated label values.
    def get_bytes(self):

        bitstream = BitArray()
        current_address = self.imagebase
        labels_to_addresses_map = {}

        for ast_node in self.ast:
            ast_node.set_node_bitfields(self.compute_node_bitfields(ast_node))
            ast_node.set_node_address(current_address)
            for lbl in ast_node.labels:
                labels_to_addresses_map[lbl] = ast_node.address
            # TODO: What happens with addressing in non-standard word sizes?
            bit_length = self.bitfields_to_bitarray(ast_node.node_bitfields).length
            byte_length = int(bit_length / DEFAULT_BYTE_BITSIZE)
            if bit_length % DEFAULT_BYTE_BITSIZE != 0:
                byte_length += 1
            current_address += byte_length

        for ast_node in self.ast:
            self.update_label_placeholders(ast_node, labels_to_addresses_map)

        for ast_node in self.ast:
            ast_node.set_node_bitfields(self.compute_node_bitfields(ast_node))
            node_bitarray = self.bitfields_to_bitarray(ast_node.node_bitfields)
            bitstream.append(node_bitarray)

        return bitstream.tobytes()

    # Pretty prints debug info showing for each parsed instruction, what the set bitfields are for that instruction, and
    # what bytes are generated by the bytes of that instruction. Even shows the original instruction's source code.
    # Triggers an actual build of the real bitstream.
    def print_debug_bitstream(self):

        self.get_bytes()

        for ast_node in self.ast:
            if len(ast_node.original_line) > 0:
                print(ast_node.original_line)

            headers, values = self.get_debug_str_lines(ast_node.node_bitfields)
            print(tabulate(values, headers=headers))

            bitarray = self.bitfields_to_bitarray(ast_node.node_bitfields)
            bytes_padded = self.bytes_to_string(bitarray.tobytes())
            print("Bytes (padded): ")
            print(bytes_padded)

            print("")

        return

    # Compute the bitfields of an instruction, by setting bitfields according to bitfield modifiers in ast node.
    def compute_node_bitfields(self, ast_node):

        bitfields = self.get_possible_bitfields()
        bitfields = self.set_bitfields(bitfields, ast_node)

        return bitfields

    # Gets all possible bitfields for an instruction from the spec.
    def get_possible_bitfields(self) -> List[Bitfield]:

        bitfields = []
        for b in self.spec.bitfields:
            bitfields.append(Bitfield(b.name, b.size))

        return bitfields

    # Sets the bitfields of an instruction by walking across all AST nodes of that instruction, and applying any bitfield
    # modifiers which might be present at each node. Final instruction bitstream is generated from all bitfields which
    # had a value set by a modifier.
    def set_bitfields(self, bitfields: List[Bitfield], ast_node: ASTNode) -> List[Bitfield]:

        for b in ast_node.bitfield_modifiers:
            if b.modifier_type == ModifierTypes.MODIFIER:
                idx = self.get_bitfield_index(b.bitfield_name)
                bitfields[idx].set_value(b.modifier_value)
            elif b.modifier_type == ModifierTypes.INT_PLACEHOLDER:
                print("ERROR: There should be no unprocessed bitfield modifiers of type INT_PLACEHOLDER by this point")
                raise ValueError
            elif b.modifier_type == ModifierTypes.LABEL_PLACEHOLDER:
                idx = self.get_bitfield_index(b.bitfield_name)
                bitfields[idx].set_value("0" * bitfields[idx].size)
            else:
                print("ERROR: Unknown type of bitfield modifier?")
                raise ValueError

        for child_node in ast_node.child_nodes:
            bitfields = self.set_bitfields(bitfields, child_node)

        return bitfields

    # Get the index of a bitfield in the bitfields list. Looks up the bitfield by name.
    def get_bitfield_index(self, bitfield_name):
        if bitfield_name not in self.spec.bitfield_indexes_map:
            print("Bitstream Generation ERROR: Unknown bitfield named '%s'" % bitfield_name)
            raise ValueError

        return self.spec.bitfield_indexes_map[bitfield_name]

    # Builds the debug string for the bitfields of an instruction. Showing the name and value of each bitfield in the
    # instruction. Uses 'tabulate' library (https://pypi.org/project/tabulate/) to nicely display the info for debug
    # purposes.
    def get_debug_str_lines(self, bitfields: List[Bitfield]):
        headers = []
        values = []
        value_row = []
        for b in bitfields:
            if b.present:
                headers.append(b.name)
                value_row.append(b.value)
        values.append(value_row)

        return headers, values

    # Pretty print an array of bytes to a string.
    def bytes_to_string(self, byte_array):
        s = ""
        for b in byte_array:
            s += str("{:02X} ").format(b)
        return s

    # Translates internal format for bitfields to externally defined BitArray object, which can then be used to
    # emit the bitstream as an array of bytes
    def bitfields_to_bitarray(self, bitfields: List[Bitfield]) -> BitArray:

        retval = BitArray()
        for b in bitfields:
            if b.present:
                retval.append('0b' + b.value)

        return retval

    # Walks across all bitfield modifiers. If it's a label placeholder, look up the address of the label, then use
    # a plugin to emit the correct bits to express the address/offset of the label reference.
    def update_label_placeholders(self, ast_node: ASTNode, labels_to_addresses_map: Dict[str, int]):

        for idx, b in enumerate(ast_node.bitfield_modifiers):
            if b.modifier_type == ModifierTypes.LABEL_PLACEHOLDER:
                label_placeholder_value = b.modifier_value
                current_address = ast_node.address
                label_address = 0

                found_child = False
                for child_node in ast_node.child_nodes:
                    if child_node.token_type == TokenTypes.LABEL_TOKEN and child_node.token_value.startswith(label_placeholder_value + " "):
                        found_child = True
                        label_name = child_node.token_value[len(label_placeholder_value + " "):]

                        if label_name not in labels_to_addresses_map:
                            print("Bitstream Generation ERROR: Unknown label in bitfield '%s' modifier" % label_name)
                            raise ValueError

                        label_address = labels_to_addresses_map[label_name]
                        break

                if not found_child:
                    print("Bitstream Generation ERROR: We have a placeholder bitfield modifier '%s', but none of the child AST nodes are of type LABEL_TOKEN with a matching name." % label_placeholder_value)
                    raise ValueError

                label_bits = AsmIntTypes.calc_label_bits(label_placeholder_value, current_address, label_address)

                ast_node.bitfield_modifiers[idx] = BitfieldModifier(ModifierTypes.MODIFIER, b.bitfield_name, label_bits)

        for child_node in ast_node.child_nodes:
            self.update_label_placeholders(child_node, labels_to_addresses_map)

        return
