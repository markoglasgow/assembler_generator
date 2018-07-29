from asm_grammar_spec import TokenTypes, ModifierTypes
from asm_parser import ASTNode
from typing import List

print_buffer = []
bitfield_modifiers_column = 16


def pretty_print_ast(ast: List[ASTNode], indentation=0):

    global print_buffer, bitfield_modifiers_column

    print_buffer.clear()
    for ast_node in ast:
        pretty_print_ast_node(ast_node, indentation)
        print_buffer.append("")

    longest_line_len = len(max(print_buffer, key=len))
    bitfield_modifiers_column = longest_line_len + (4 - (longest_line_len % 4)) + 4
    print_buffer.clear()

    for ast_node in ast:
        pretty_print_ast_node(ast_node, indentation)
        print_buffer.append("")

    print_the_buffer()

    return


def pretty_print_ast_node(ast_node: ASTNode, indentation: int):

    if len(ast_node.original_line) > 0:
        print_buffer.append(indent_by(indentation) + ast_node.original_line)

    if ast_node.token_type == TokenTypes.WHITESPACE:
        return

    elif ast_node.token_type == TokenTypes.RAW_TOKEN or ast_node.token_type == TokenTypes.INT_TOKEN:
        row_str = indent_by(indentation) + "'" + ast_node.token_value + "'"
        row_str += padding(len(row_str))
        row_str += print_bitfield_modifiers(ast_node)
        print_buffer.append(row_str)
        return

    elif ast_node.token_type == TokenTypes.PLACEHOLDER:
        row_str = indent_by(indentation) + ast_node.token_value
        row_str += padding(len(row_str))
        row_str += print_bitfield_modifiers(ast_node)
        print_buffer.append(row_str)

        for child_node in ast_node.child_nodes:
            pretty_print_ast_node(child_node, indentation + 4)

    return


def indent_by(indentation: int):
    s = ""
    for i in range(indentation):
        s += " "
    return s


def padding(current_len: int):
    if current_len < bitfield_modifiers_column:
        indent = bitfield_modifiers_column - current_len
    else:
        indent = 4

    return indent_by(indent)


def print_bitfield_modifiers(ast_node: ASTNode):

    ret_val = ""

    for b in ast_node.bitfield_modifiers:
        ret_val += ":: "
        if b.modifier_type == ModifierTypes.MODIFIER:
            ret_val += b.bitfield_name + "=" + b.modifier_value
        elif b.modifier_type == ModifierTypes.INT_PLACEHOLDER:
            ret_val += b.bitfield_name + "=%" + b.modifier_value + "%"

        ret_val += " "

    return ret_val


def print_the_buffer():
    for s in print_buffer:
        print(s)
    return
