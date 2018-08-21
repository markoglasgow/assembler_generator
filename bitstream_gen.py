from asm_grammar_spec import AsmGrammarSpec, TokenTypes, ModifierTypes, BitfieldModifier
from asm_parser import ASTNode
from asm_int_types import AsmIntTypes

from typing import List, Dict

from tabulate import tabulate
from bitstring import BitArray


DEFAULT_IMAGEBASE = 0x1000
DEFAULT_BYTE_BITSIZE = 8


class Bitfield:

    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.value = None
        self.present = False

    def set_value(self, value):
        self.value = value
        self.present = True


class BitstreamGenerator:

    def __init__(self, spec: AsmGrammarSpec, ast: List[ASTNode], imagebase=DEFAULT_IMAGEBASE):
        self.spec = spec
        self.ast = ast
        self.imagebase = imagebase
        return

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

    def compute_node_bitfields(self, ast_node):

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

    def bytes_to_string(self, byte_array):
        s = ""
        for b in byte_array:
            s += str("{:02X} ").format(b)
        return s

    def bitfields_to_bitarray(self, bitfields: List[Bitfield]) -> BitArray:

        retval = BitArray()
        for b in bitfields:
            if b.present:
                retval.append('0b' + b.value)

        return retval

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
