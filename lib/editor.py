import re


class MiniFileEditor(object):

    def __init__(self, file_path):
        self.file_path = file_path

    def append(self, line):
        if not line.endswith('\n'):
            line += '\n'
        with open(self.file_path, 'a+') as f:
            f.write(line)

    def contains(self, line_str):
        contains = False
        with open(self.file_path) as f:

            line = f.readline()
            while line:
                if line.strip() == line_str:
                    contains = True
                    break
                line = f.readline()
        return contains

    def contains_re(self, line_re):
        contains = False
        with open(self.file_path) as f:
            line = f.readline()
            while line:
                if re.match(line_re, line.strip()):
                    contains = True
                    break
                line = f.readline()
        return contains

    def add(self, line):
        if not self.contains(line):
            self.append(line)

    def replace(self, line_re, new_line):
        if not new_line.endswith('\n'):
            new_line += '\n'

        with open(self.file_path) as f:
            lines = f.readlines()

        for i in range(len(lines)):
            line = lines[i]
            if re.match(line_re, line):
                lines[i] = new_line
                break
        with open(self.file_path, 'w') as f:
            f.writelines(lines)
