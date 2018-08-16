import os.path


class ObjectWriter:

    def __init__(self, raw_bytes):
        self.raw_bytes = raw_bytes
        return

    def write_object(self, template_file, output_file):

        if not os.path.isfile(template_file):
            print("Object Writer Error: Binary template file at %s does not exist." % template_file)
            raise ValueError

        info_file_path = template_file + ".info"
        if not os.path.isfile(info_file_path):
            print("Object Writer Error: Info file for binary template %s does not exist." % info_file_path)
            raise ValueError

        offset, size = self.read_template_info(info_file_path)

        return

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
