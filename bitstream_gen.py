from asm_grammar_spec import AsmGrammarSpec, ModifierTypes, BitfieldModifier, BitfieldDefinition
from asm_parser import ASTNode

from typing import List

from tabulate import tabulate
from bitstring import BitArray


class Bitfield:

    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.value = ""
        self.present = False

    def set_value(self, value):
        self.value = value
        self.present = True


class BitstreamGenerator:

    def __init__(self, spec: AsmGrammarSpec, ast: List[ASTNode]):
        self.spec = spec
        self.ast = ast
        return

    def get_bytes(self):

        bitstream = BitArray()
        for ast_node in self.ast:
            node_bitfields = self.get_node_bitfields(ast_node)
            node_bitarray = self.bitfields_to_bitarray(node_bitfields)
            bitstream.append(node_bitarray)

        return bitstream.tobytes()

    def print_debug_bitstream(self):

        for ast_node in self.ast:
            if len(ast_node.original_line) > 0:
                print(ast_node.original_line)

            bitfields = self.get_node_bitfields(ast_node)

            headers, values = self.get_debug_str_lines(bitfields)
            print(tabulate(values, headers=headers))

            bitarray = self.bitfields_to_bitarray(bitfields)
            bytes_padded = str(bitarray.tobytes()).replace("'\\x", "").replace("'", "").replace("\\", "").replace("b", "").replace("x", " ")
            print("Bytes (padded): ")
            print(bytes_padded)

            print("")

        return

    def get_node_bitfields(self, ast_node):

        bitfields = self.get_possible_bitfields()
        bitfields = self.set_bitfields(bitfields, ast_node)

        return bitfields

    def get_possible_bitfields(self) -> List[Bitfield]:

        bitfields = []
        for b in self.spec.bitfields:
            bitfields.append(Bitfield(b.name, b.size))

        return bitfields

    def set_bitfields(self, bitfields: List[Bitfield], ast_node: ASTNode) -> List[Bitfield]:

        for b in ast_node.bitfield_modifiers:
            if b.modifier_type == ModifierTypes.MODIFIER:
                idx = self.get_bitfield_index(b.bitfield_name)
                bitfields[idx].set_value(b.modifier_value)

        for child_node in ast_node.child_nodes:
            bitfields = self.set_bitfields(bitfields, child_node)

        return bitfields

    def get_bitfield_index(self, bitfield_name):
        if bitfield_name not in self.spec.bitfield_indexes_map:
            print("Bitstream Generation ERROR: Unknown bitfield named '%s'" % bitfield_name)
            raise ValueError

        return self.spec.bitfield_indexes_map[bitfield_name]

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

    def bitfields_to_bitarray(self, bitfields: List[Bitfield]) -> BitArray:

        retval = BitArray()
        for b in bitfields:
            if b.present:
                retval.append('0b' + b.value)

        return retval
