import os.path
import subprocess
import tokenize
import zlib, base64
from tokenize import NUMBER, NAME, NEWLINE
from collections import namedtuple
from z3 import *

from analysis import *
from basicblock import BasicBlock
from instruction import Instruction

log = logging.getLogger(__name__)


def logging_info(content):
    print("LOG_INFO:symExecEclone: " + content)


UNSIGNED_BOUND_NUMBER = 2 ** 256 - 1
CONSTANT_ONES_159 = BitVecVal((1 << 160) - 1, 256)

Assertion = namedtuple('Assertion', ['pc', 'model'])


def construct_static_edges(jump_type, vertices, edges):
    key_list = sorted(jump_type.keys())
    length = len(key_list)
    for i, key in enumerate(key_list):
        if jump_type[key] != "terminal" and jump_type[key] != "unconditional" and i + 1 < length:
            target = key_list[i + 1]
            edges[key].append(target)
            vertices[key].set_falls_to(target)
    return vertices, edges


def start_add_0x(file):
    add_0x_contents = []
    with open(file, 'r') as f:
        contents = f.readlines()
        if len(contents) > 1 and contents[1].startswith('0x'):
            return
        for content in contents:
            add_0x_contents.append('0x' + content)

    with open(file, 'w') as f:
        for content in add_0x_contents:
            f.write(content)


def build_cfg_and_analyze(disasm_file):
    start_add_0x(disasm_file)
    with open(disasm_file, 'r') as f:
        f.readline()  # Remove first line
        tokens = tokenize.generate_tokens(f.readline)
        end_ins_dict, instructions, jump_type = collect_vertices(tokens)
        vertices, edges = construct_bb(end_ins_dict, instructions, jump_type)
        vertices, edges = construct_static_edges(jump_type, vertices, edges)
        out = compute_semantic(vertices)
    return out


def collect_vertices(tokens):
    end_ins_dict, instructions, jump_type = {}, {}, {}

    current_ins_address = 0
    last_ins_address = 0
    is_new_line = True
    current_block = 0
    current_line_content = ""
    wait_for_push = False
    is_new_block = False

    for tok_type, tok_string, (srow, scol), _, line_number in tokens:
        if wait_for_push is True:
            push_val = ""
            for ptok_type, ptok_string, _, _, _ in tokens:
                if ptok_type == NEWLINE:
                    is_new_line = True
                    current_line_content += push_val + ' '
                    instructions[current_ins_address] = current_line_content
                    log.debug(current_line_content)
                    current_line_content = ""
                    wait_for_push = False
                    break
                try:
                    int(ptok_string, 16)
                    push_val += ptok_string
                except ValueError:
                    pass

            continue
        elif is_new_line is True and tok_type == NUMBER:  # looking for a line number
            last_ins_address = current_ins_address
            # print(tok_string, current_ins_address)
            try:
                current_ins_address = int(tok_string, 16)
            except ValueError:
                log.critical("ERROR when parsing row %d col %d", srow, scol)
                quit()
            is_new_line = False
            if is_new_block:
                current_block = current_ins_address
                is_new_block = False
            continue
        elif tok_type == NEWLINE:
            is_new_line = True
            log.debug(current_line_content)
            instructions[current_ins_address] = current_line_content
            current_line_content = ""
            continue
        elif tok_type == NAME:
            if tok_string == "JUMPDEST":
                if last_ins_address not in end_ins_dict:
                    end_ins_dict[current_block] = last_ins_address
                current_block = current_ins_address
                is_new_block = False
            elif tok_string == "STOP" or tok_string == "RETURN" or tok_string == "SUICIDE" or tok_string == "REVERT" or tok_string == "ASSERTFAIL":
                jump_type[current_block] = "terminal"
                end_ins_dict[current_block] = current_ins_address
            elif tok_string == "JUMP":
                jump_type[current_block] = "unconditional"
                end_ins_dict[current_block] = current_ins_address
                is_new_block = True
            elif tok_string == "JUMPI":
                jump_type[current_block] = "conditional"
                end_ins_dict[current_block] = current_ins_address
                is_new_block = True
            elif tok_string.startswith('PUSH', 0):
                wait_for_push = True
            is_new_line = False
        if tok_string != "=" and tok_string != ">":
            current_line_content += tok_string + " "

    if current_block not in end_ins_dict:
        log.debug("current block: %d", current_block)
        log.debug("last line: %d", current_ins_address)
        end_ins_dict[current_block] = current_ins_address

    if current_block not in jump_type:
        jump_type[current_block] = "terminal"

    for key in end_ins_dict:
        if key not in jump_type:
            jump_type[key] = "falls_to"
    return end_ins_dict, instructions, jump_type


def construct_bb(end_ins_dict, instructions, jump_type):
    vertices, edges = {}, {}
    sorted_addresses = sorted(instructions.keys())
    size = len(sorted_addresses)
    for key in end_ins_dict:
        end_address = end_ins_dict[key]
        block = BasicBlock(key, end_address)
        if key not in instructions:
            continue
        inst = Instruction(instructions[key])
        # inst = {"inst_str": "", "storage": []}
        # inst["inst_str"] = instructions[key]
        # block.add_instruction(instructions[key])
        block.add_instruction(inst)
        i = sorted_addresses.index(key) + 1
        while i < size and sorted_addresses[i] <= end_address:
            inst_sorted = Instruction(instructions[sorted_addresses[i]])
            # inst_sorted = {"inst_str": "", "storage": []}
            # inst_sorted["inst_str"] = instructions[sorted_addresses[i]]
            block.add_instruction(inst_sorted)
            # block.add_instruction(instructions[sorted_addresses[i]])
            i += 1
        block.set_block_type(jump_type[key])
        vertices[key] = block
        edges[key] = []
    return vertices, edges


def generate_semantics(bytecode='', address=None, optimized=None):

    disasm_file = 'tmp.disasm.evm'
    ret = subprocess.run(['evm', 'disasm', bytecode, '>', disasm_file], shell=True, stderr=open(os.devnull, 'w'), stdout=open(os.devnull, 'w'))
    # ret = os.system(f'evm disasm {bytecode} > {disasm_file}')
    if ret.returncode != 0:
        # cmd failed
        if address and os.path.exists(f'./dataset/opcode_without_opt/{address}.txt') and os.path.exists(f'./dataset/opcode_opt/{address}.txt'):
            disasm_file = f'./dataset/opcode_without_opt/{address}.txt' if optimized == 1 else f'./dataset/opcode_opt/{address}.txt'

    return build_cfg_and_analyze(disasm_file)


def similarity_scoring_via_bytecode(bytecode1, bytecode2):
    contract_semantic_1 = generate_semantics(bytecode1)
    contract_semantic_2 = generate_semantics(bytecode2)
    relative_score, self_score = contract_similarity(contract_semantic_1, contract_semantic_2)
    similarity_score = relative_score / float(self_score)
    # print(f"\nSimilarity Score: {relative_score}/{self_score}={similarity_score}")
    return {"score": similarity_score, "nquery": len(contract_semantic_1.keys()),
            "ntarget": len(contract_semantic_2.keys())}

def similarity_scoring_via_address(address):
    contract_semantic_1 = generate_semantics(f'./dataset/bytecode_without_opt/{address}.txt', address, 1)
    contract_semantic_2 = generate_semantics(f'./dataset/bytecode_opt/{address}.txt', address, 0)
    relative_score, self_score = contract_similarity(contract_semantic_1, contract_semantic_2)
    similarity_score = relative_score / float(self_score)
    # print(f"\nSimilarity Score: {relative_score}/{self_score}={similarity_score}")
    return {"score": similarity_score, "nquery": len(contract_semantic_1.keys()),
            "ntarget": len(contract_semantic_2.keys())}

def similarity_scoring_via_different_address(address1, address2):
    contract_semantic_1 = generate_semantics('', address1, 1)
    contract_semantic_2 = generate_semantics('', address2, 1)
    relative_score, self_score = contract_similarity(contract_semantic_1, contract_semantic_2)
    similarity_score = relative_score / float(self_score)
    # print(f"\nSimilarity Score: {relative_score}/{self_score}={similarity_score}")
    return {"score": similarity_score, "nquery": len(contract_semantic_1.keys()),
            "ntarget": len(contract_semantic_2.keys())}