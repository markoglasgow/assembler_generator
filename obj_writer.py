import os.path

# Helper module for outputting the bitstream in various formats, or to embed it inside an object template. The object
# templates are located in bin_templates. Each template has a code cave of NOPs into which machine code can be injected.
# There is a .info file which must be present next to each template object file. The first line of the .info file
# contains the offset into which machine code should be injected. The second line contains the size of the code cave.
# Machine code blobs larger than the size should not be injected.


class ObjectWriter:

    def __init__(self, raw_bytes):
        self.raw_bytes = raw_bytes
        return

    # Write the raw binary blob to a file.
    def write_bin(self, output_file):
        with open(output_file, "wb+") as out_file:
            out_file.write(self.raw_bytes)

        return

    # Write the machine code as textual Sigma16 data, which can be loaded and executed in a Sigma16 simulator.
    def write_sigma16_data(self, output_file):

        if len(self.raw_bytes) % 2 != 0:
            print("Sigma16 writer error: Sigma16 has 16 bit words, so the buffer length should be divisible by 2. Instead it has a length of %s" % (len(self.raw_bytes)))

        text_buffer = ""
        current_offset = 0

        while current_offset < len(self.raw_bytes):
            first_byte = str("{:02x}").format(self.raw_bytes[current_offset])
            second_byte = str("{:02x}").format(self.raw_bytes[current_offset + 1])

            line = "    data $" + first_byte + second_byte + "\n"
            text_buffer += line
            current_offset += 2

        with open(output_file, "w+") as out_file:
            out_file.write(text_buffer)

        return

    # Write machine code into a template object file which gives the user an executable binary they can run to test their
    # assembled code. Template files are located in bin_templates folder, and have a .info file next to them.
    def write_object(self, template_file, output_file):

        if not os.path.isfile(template_file):
            print("Object Writer Error: Binary template file at %s does not exist." % template_file)
            raise ValueError

        info_file_path = template_file + ".info"
        if not os.path.isfile(info_file_path):
            print("Object Writer Error: Info file for binary template %s does not exist." % info_file_path)
            raise ValueError

        offset, size = self.read_template_info(info_file_path)

        if len(self.raw_bytes) > size:
            print("Object Writer Error: Size of assembled code (%s) is larger than available space in binary template" % (len(self.raw_bytes)))
            raise ValueError

        with open(template_file, "rb") as bin_file:
            binary_buffer = bin_file.read()

        binary_buffer = self.overwrite_bytes(binary_buffer, self.raw_bytes, offset)

        with open(output_file, "wb+") as out_file:
            out_file.write(binary_buffer)

        return

    # Reads .info file of an object template file. First line will specify offset of code cave where assembled machine
    # code should be injected, second line will specify size of code cave. Size of machine code should not exceed size
    # of code cave.
    def read_template_info(self, info_file_path):
        with open(info_file_path, "r") as info_file:
            lines = info_file.readlines()

        if len(lines) != 2:
            print("Object Writer Error: Info file %s should only have two lines. First line should be offset where binary blob will be inserted. Second line should be maximum size of binary blob." % info_file_path)
            raise ValueError

        lines = [l.strip() for l in lines]

        try:
            if lines[0].startswith("0x"):
                offset = int(lines[0], 16)
            else:
                offset = int(lines[0], 10)
        except ValueError:
            print("Object Writer Error: Unable to parse offset int %s in info file %s" % (lines[0], info_file_path))
            raise ValueError

        try:
            if lines[1].startswith("0x"):
                size = int(lines[1], 16)
            else:
                size = int(lines[1], 10)
        except ValueError:
            print("Object Writer Error: Unable to parse size int %s in info file %s" % (lines[1], info_file_path))
            raise ValueError

        return offset, size

    # Overwrite bytes in a buffer at a certain offset with new_bytes.
    def overwrite_bytes(self, original_buffer, new_bytes, offset):

        bin_size = len(new_bytes)
        current_offset = 0

        new_buffer = bytearray()

        while current_offset < len(original_buffer):
            if offset <= current_offset < offset + bin_size:
                new_buffer.append(new_bytes[current_offset - offset])
            else:
                new_buffer.append(original_buffer[current_offset])
            current_offset += 1

        return new_buffer
