from typing import Tuple

# Static class containing helper methods useful for parsing.


class ParseUtils:

    valid_identifier_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"
    valid_identifier_chars_map = {}
    for c in valid_identifier_chars:
        valid_identifier_chars_map[c] = True

    valid_number_chars = "1234567890"
    valid_number_chars_map = {}
    for c in valid_number_chars:
        valid_number_chars_map[c] = True

    # Reads a token until certain break characters are reached, or until characters read are not valid token characters.
    # Reading starts at a certain position in the given string.
    # Returns the token read, along with an updated position inside the string.
    @staticmethod
    def read_token(input_string, start_pos=0, break_chars=None, valid_chars=None) -> Tuple[str, int]:

        if break_chars is None:
            break_chars = [' ', '\t']

        token = ""

        current_pos = ParseUtils.skip_whitespace(input_string, start_pos)

        while current_pos < len(input_string):
            current_char = input_string[current_pos]
            if current_char in break_chars:
                break

            if valid_chars is not None:
                if current_char not in valid_chars:
                    break

            token += current_char

            current_pos += 1

        return token, current_pos

    # Read an alphanumeric identifier from a string at a certain position. Return the identifier and the updated position
    # in the string after the reading is done.
    @staticmethod
    def read_identifier(input_string, start_pos=0) -> Tuple[str, int]:
        return ParseUtils.read_token(input_string, start_pos, break_chars=[' ', '\t'], valid_chars=ParseUtils.valid_identifier_chars_map)

    # Read a decimal number at a certain position in a string. Return the identifier and the updated position in the string after
    # the reading is done.
    @staticmethod
    def read_number(input_string, start_pos=0) -> Tuple[str, int]:
        return ParseUtils.read_token(input_string, start_pos, break_chars=[' ', '\t'], valid_chars=ParseUtils.valid_number_chars_map)

    # Helper method to skip whitespaces at a certain point in a string, and returns updated position after the whitespaces
    @staticmethod
    def skip_whitespace(input_string, start_pos=0):

        pos = start_pos
        while pos < len(input_string) and (input_string[pos] == ' ' or input_string[pos] == '\t'):
            pos += 1

        return pos

    # Read next char in string at given position, return None if we hit eol.
    @staticmethod
    def read_next_char(input_string, start_pos=0) -> str:
        c = None
        if start_pos < len(input_string):
            c = input_string[start_pos]
        return c

    # Checks if the rest of a string is empty past a certain position.
    @staticmethod
    def is_rest_empty(input_string, start_pos=0):

        pos = ParseUtils.skip_whitespace(input_string, start_pos)
        if pos == len(input_string):
            return True

        return False
