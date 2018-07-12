
class ParseUtils:

    valid_identifier_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"
    valid_identifier_chars_map = {}

    for c in valid_identifier_chars:
        valid_identifier_chars_map[c] = True

    @staticmethod
    def read_token(input_string, start_pos=0, break_chars=None, valid_chars=None):

        if break_chars is None:
            break_chars = [' ']

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

    @staticmethod
    def read_identifier(input_string, start_pos=0):
        return ParseUtils.read_token(input_string, start_pos, break_chars=[' '], valid_chars=ParseUtils.valid_identifier_chars_map)

    @staticmethod
    def skip_whitespace(input_string, start_pos=0):

        pos = start_pos
        while pos < len(input_string) and input_string[pos] == ' ':
            pos += 1

        return pos

    @staticmethod
    def read_next_char(input_string, start_pos=0) -> str:
        c = None
        if start_pos < len(input_string):
            c = input_string[start_pos]
        return c
