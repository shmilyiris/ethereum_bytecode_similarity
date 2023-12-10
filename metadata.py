class MetaData:
    def __init__(self, arithmeticOP, logicOP, envOP, chainOP, stackOP, memoryProp):
        self.arithmetic = arithmeticOP
        self.logic = logicOP
        self.env = envOP
        self.chain = chainOP
        self.stack = stackOP
        self.memory = memoryProp
        self.alpha = [1 for _ in range(6)]

    def get_arithmetic_value(self):
        return self.arithmetic

    def get_logic_value(self):
        return self.logic

    def get_env_value(self):
        return self.env

    def get_chain_value(self):
        return self.chain

    def get_stack_value(self):
        return self.stack

    def get_memory_value(self):
        return self.memory

    def get_vector(self):
        return [self.arithmetic, self.logic, self.env, self.chain, self.stack, self.memory]

    def get_alpha(self):
        return self.alpha