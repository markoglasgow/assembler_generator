from asm_grammar_spec import AsmGrammarSpec, ModifierTypes, BitfieldModifier, BitfieldDefinition
from asm_parser import ASTNode
from typing import List


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

    def print_debug_bitstream(self):

        for ast_node in self.ast:
            if len(ast_node.original_line) > 0:
                print(ast_node.original_line)
            print(self.get_node_debug_bitstream(ast_node))
            print("")

        return

    def get_node_debug_bitstream(self, ast_node):

        bitfields = self.get_possible_bitfields()
        bitfields = self.set_bitfields(bitfields, ast_node)

        return self.get_debug_str_lines(bitfields)

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
            elif b.modifier_type == ModifierTypes.PLACEHOLDER:
                child_emit_value = self.find_child_emit(b.modifier_value, ast_node.child_nodes)
                if child_emit_value is None:
                    print("Bitstream Generation ERROR: Unable to find child emit '%s' for AST Node '%s'" % (b.modifier_value, ast_node.token_value))
                    raise ValueError
                idx = self.get_bitfield_index(b.bitfield_name)
                bitfields[idx].set_value(child_emit_value)

        for child_node in ast_node.child_nodes:
            bitfields = self.set_bitfields(bitfields, child_node)

        return bitfields

    def find_child_emit(self, emit_node_name, child_nodes: List[ASTNode]):
        for child_node in child_nodes:
            if child_node.token_value == emit_node_name:
                for c in child_node.child_nodes:
                    if not c.consumed:
                        for b in c.bitfield_modifiers:
                            if b.modifier_type == ModifierTypes.EMIT:
                                c.consumed = True
                                return b.modifier_value

            child_emit = self.find_child_emit(emit_node_name, child_node.child_nodes)
            if child_emit is not None:
                return child_emit

        return None

    def get_bitfield_index(self, bitfield_name):
        if bitfield_name not in self.spec.bitfield_indexes_map:
            print("Bitstream Generation ERROR: Unknown bitfield named '%s'" % bitfield_name)
            raise ValueError

        return self.spec.bitfield_indexes_map[bitfield_name]

    def get_debug_str_lines(self, bitfields: List[Bitfield]):
        headers = ""
        values = ""
        for b in bitfields:
            if b.present:
                headers += b.name + "\t"
                values += b.value + "\t"

        return headers + "\n" + values
