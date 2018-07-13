from asm_grammar_spec import TokenTypes
from asm_parser import ASTNode
from typing import List


def pretty_print_ast(ast: List[ASTNode], indentation=0):

    for ast_node in ast:
        pretty_print_ast_node(ast_node, indentation)
        print("")

    return


def pretty_print_ast_node(ast_node: ASTNode, indentation: int):

    if ast_node.token_type == TokenTypes.WHITESPACE:
        return

    elif ast_node.token_type == TokenTypes.RAW_TOKEN:
        print(indent_by(indentation) + "'" + ast_node.token_value + "'")
        return

    elif ast_node.token_type == TokenTypes.PLACEHOLDER:
        print(indent_by(indentation) + ast_node.token_value)
        for child_node in ast_node.child_nodes:
            pretty_print_ast_node(child_node, indentation + 4)

    return


def indent_by(indentation):
    s = ""
    for i in range(indentation):
        s += " "
    return s
