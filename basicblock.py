import six
import os

class BasicBlock:
    def __init__(self, start_address, end_address):
        self.start = start_address
        self.end = end_address
        self.instructions = []  # each instruction is a string.
        self.jump_target = 0

    def get_start_address(self):
        return self.start

    def get_end_address(self):
        return self.end

    def add_instruction(self, instruction):
        self.instructions.append(instruction)

    def get_instructions(self):
        return self.instructions

    def set_instruction(self, id, value):
        self.instructions[id] = value

    def get_instruction(self, id):
        return self.instructions[id]

    def set_block_type(self, type):
        self.type = type

    def get_block_type(self):
        return self.type

    def set_falls_to(self, address):
        self.falls_to = address

    def get_falls_to(self):
        return self.falls_to

    def set_jump_target(self, address):
        if isinstance(address, six.integer_types):
            self.jump_target = address
        else:
            self.jump_target = -1

    def get_jump_target(self):
        return self.jump_target

    def set_branch_expression(self, branch):
        self.branch_expression = branch

    def get_branch_expression(self):
        return self.branch_expression

    def set_function_hash(self, func_hash):
        self.func_hash = func_hash

    def get_function_hash(self):
        return self.func_hash

    def set_path_condition(self, path):
        self.path_condition = path

    def get_path_condition(self):
        return self.path_condition

    def display(self):
        six.print_("================")
        six.print_("start address: %d" % self.start)
        six.print_("end address: %d" % self.end)
        six.print_("end statement type: " + self.type)
        if hasattr(self, 'path_condition'):
            six.print_("path condition: " + str(self.path_condition))
        for instr in self.instructions:
            #six.print_(instr)
            instr.display()
            #six.print_(instr["inst_str"])
            #print instr["storage"]