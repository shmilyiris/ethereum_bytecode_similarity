import logging
import math
import sys
from metadata import MetaData
from birthmark import BirthMark
from globals import is_baseline, omega, k

log = logging.getLogger(__name__)

ARITHMETIC_OP_TYPE = "ARITHMETIC_OP_TYPE"
LOGIC_OP_TYPE = "LOGIC_OP_TYPE"
ENV_OP_TYPE = "ENV_OP_TYPE"
CHAIN_OP_TYPE = "CHAIN_OP_TYPE"
STACK_OP_TYPE = "STACK_OP_TYPE"
MEMORY_OP_TYPE = "MEMORY_OP_TYPE"
STORAGE_OP_TYPE = "STORAGE_OP_TYPE"
CALL_OP_TYPE = "CALL_OP_TYPE"

# GAS is not supported for now
OPCODE_TYPE = {
    'arithmetic': ['STOP', 'ADD', 'MUL', 'SUB', 'DIV', 'SDIV', 'MOD', 'SMOD', 'ADDMOD', 'MULMOD', 'EXP', 'SIGNEXTEND'],
    'logic': ['LT', 'GT', 'SLT', 'SGT', 'EQ', 'ISZERO', 'AND', 'OR', 'XOR', 'NOT', 'BYTE'],
    'env': ['ADDRESS', 'BALANCE', 'ORIGIN', 'CALLER', 'CALLVALUE', 'CALLDATALOAD', 'CALLDATASIZE', 'CALLDATACOPY',
            'CODESIZE', 'CODECOPY', 'GASPRICE', 'EXTCODESIZE', 'EXTCODECOPY'],
    'chain': ['BLOCKHASH', 'COINBASE', 'TIMESTAMP', 'NUMBER', 'DIFFICULTY', 'GASLIMIT'],
    'stack': ['POP', 'PUSH', 'DUP', 'SWAP'],
    'memory': ['MLOAD', 'MSTORE', 'MSTORE8'],
    'storage': ['SLOAD', 'SSTORE'],
    'call': ['CALL']
}

# Parameter set


def analyzeBlock(block):
    func_hash = ""
    path_condition_meta = 0
    arithmetic_meta = 0
    logic_meta = 0
    env_meta = 0
    chain_meta = 0
    stack_meta = 0
    memory_meta = 0
    storage_meta = 0
    call_meta = 0

    memory_def = False # True - has memory def; False - no memory def

    KallQ = [] # for update-call, use-call
    Qs = {} # queue for all storage addresses, {storage_addr, []}

    single_storage_def = {} # {storage_addr, single-def count}
    single_storage_use = {} # {storage_addr, single-use count}
    single_call = 0 # single-call count
    storage_def_use = {} # {storage_addr, def-use count}
    storage_use_update = {} # {storage_addr, use-update count}
    update_call = 0 # update-call count
    use_call = 0 # use-call count
    call_finalize = 0 # call-finalize count

    if hasattr(block, 'func_hash'):
        func_hash = block.get_function_hash()
    if hasattr(block, 'path_condition'):
        path_condition_meta = 1
    try:
        block_ins = block.get_instructions()
    except KeyError:
        log.debug("This path results in an exception, possibly an invalid jump address")
        return ["ERROR"]

    for instr in block_ins:
        instruction = instr.get_inst_str()
        instr_parts = str.split(instruction, ' ')
        instr_name = instr_parts[1]
        instr_type = getTypeOfInstruction(instr_name)

        if instr_type == "UNSUPPORTED":
            continue

        if instr_type == ARITHMETIC_OP_TYPE:
            arithmetic_meta += 1

        if instr_type == LOGIC_OP_TYPE:
            logic_meta += 1

        if instr_type == ENV_OP_TYPE:
            env_meta += 1

        if instr_type == CHAIN_OP_TYPE:
            chain_meta += 1

        if instr_type == STACK_OP_TYPE:
            stack_meta += 1

        if instr_type == MEMORY_OP_TYPE:
            if instr_name == 'MSTORE' or instr_name == 'MSTORE8':
                memory_def = True
            if instr_name == 'MLOAD' and memory_def:
                memory_meta += 1
                memory_def = False

        if instr_type == STORAGE_OP_TYPE:
            if not hasattr(instr, 'storage'):
                continue
            storage_addr = str(instr.get_storage_access()["storage"])
            if hasattr(Qs, storage_addr):
                queue = Qs[storage_addr]
            else:
                queue = []
                Qs[storage_addr] = queue

            if instr_name == 'SSTORE':
                KallQ.append('DEF')  # update KallQ

                if len(queue) > 0 and list(reversed(queue))[0] == 'DEF':  # count a single def
                    if hasattr(single_storage_def, storage_addr):
                        old_single_def = single_storage_def[storage_addr]
                        single_storage_def[storage_addr] = old_single_def + 1
                    else:
                        single_storage_def[storage_addr] = 1

                use_update_count = 0  # use-update
                call_finalize_count = 0  # call-finalize
                for e in reversed(queue):
                    if e == 'DEF':
                        break
                    if e == 'USE':
                        use_update_count += 1  # count a use-update
                    if e == 'CALL':
                        call_finalize_count += 1  # count a call-finalize
                # update global use-update
                if hasattr(storage_use_update, storage_addr):
                    old_use_update_count = storage_use_update[storage_addr]
                    storage_use_update[storage_addr] = old_use_update_count + use_update_count
                else:
                    storage_use_update[storage_addr] = use_update_count
                # update global call-finalize
                call_finalize += call_finalize_count

                queue.append('DEF')
                Qs[storage_addr] = queue  # update the queue

            if instr_name == 'SLOAD':
                KallQ.append('USE')  # update KallQ

                if len(queue) > 0 and list(reversed(queue))[0] == 'USE':  # count a single use
                    if hasattr(single_storage_use, storage_addr):
                        old_single_use = single_storage_use[storage_addr]
                        single_storage_use[storage_addr] = old_single_use + 1
                    else:
                        single_storage_use[storage_addr] = 1

                def_use_count = 0  # def-use
                for e in reversed(queue):
                    if e == 'DEF':
                        def_use_count += 1  # count a def-use
                        break
                if hasattr(storage_def_use, storage_addr):
                    old_def_use_count = storage_def_use[storage_addr]
                    storage_def_use[storage_addr] = old_def_use_count + def_use_count
                else:
                    storage_def_use[storage_addr] = def_use_count

                queue.append('USE')
                Qs[storage_addr] = queue  # update the queue

        if instr_type == CALL_OP_TYPE:
            # add CALL to all the queues
            for k, v in Qs.items():
                new_v = v.append('CALL')
                Qs[k] = new_v

            # if reversed(KallQ)[0] == 'CALL': # count a single call
            single_call += 1

            update_call_count = 0
            use_call_count = 0
            for e in reversed(KallQ):
                if e == 'DEF':
                    update_call_count += 1
                    break
            for e in reversed(KallQ):
                if e == 'USE':
                    use_call_count += 1
                    break
            update_call += update_call_count
            use_call += use_call_count

    # generate meta data
    meta_data = MetaData(arithmetic_meta, logic_meta, env_meta, chain_meta, stack_meta, memory_meta)

    # generate birthmark
    pc_cantor = 0

    def_count = len(single_storage_def)
    if len(single_storage_def.values()) == 0:
        def_max = 0
    else:
        def_max = max(single_storage_def.values())
    def_cantor = compute_cantor(def_count, def_max)

    use_count = len(single_storage_use)
    if len(single_storage_use.values()) == 0:
        use_max = 0
    else:
        use_max = max(single_storage_use.values())
    use_cantor = compute_cantor(use_count, use_max)

    call_count = single_call

    du_count = len(storage_def_use)
    if len(storage_def_use.values()) == 0:
        du_max = 0
    else:
        du_max = max(storage_def_use.values())
    du_cantor = compute_cantor(du_count, du_max)

    uu_count = len(storage_use_update)
    if len(storage_use_update.values()) == 0:
        uu_max = 0
    else:
        uu_max = max(storage_use_update.values())
    uu_cantor = compute_cantor(uu_count, uu_max)

    birth_mark = BirthMark(pc_cantor, def_cantor, use_cantor, call_count, du_cantor, uu_cantor, update_call, use_call,
                           call_finalize)

    return {"metadata": meta_data, "birthmark": birth_mark}


# cantor pairing function
def compute_cantor(k1, k2):
    return int(1 / float(2) * (k1 + k2) * (k1 + k2 + 1) + k2)


def getTypeOfInstruction(mnemonic):
    if mnemonic.startswith(OPCODE_TYPE['stack'][1]) or mnemonic.startswith(
            OPCODE_TYPE['stack'][2]) or mnemonic.startswith(OPCODE_TYPE['stack'][3]) or mnemonic == \
            OPCODE_TYPE['stack'][0]:
        return STACK_OP_TYPE
    elif mnemonic in OPCODE_TYPE['arithmetic']:
        return ARITHMETIC_OP_TYPE
    elif mnemonic in OPCODE_TYPE['logic']:
        return LOGIC_OP_TYPE
    elif mnemonic in OPCODE_TYPE['env']:
        return ENV_OP_TYPE
    elif mnemonic in OPCODE_TYPE['chain']:
        return CHAIN_OP_TYPE
    elif mnemonic in OPCODE_TYPE['memory']:
        return MEMORY_OP_TYPE
    elif mnemonic in OPCODE_TYPE['storage']:
        return STORAGE_OP_TYPE
    elif mnemonic in OPCODE_TYPE['call']:
        return CALL_OP_TYPE
    else:
        return "UNSUPPORTED"


def compute_semantic(vertices):
    # {block: {"metadata": meta_data, "birthmark": birth_mark}}
    block_semantic = {}
    for block in vertices.values():
        sem = analyzeBlock(block)
        block_semantic[block] = sem

    return block_semantic

def vector_similarity(mark1, mark2, alpha):
    top = 0
    bottom = 0
    assert (len(mark1) == len(mark2) == len(alpha)), "Incosistent vector lengths"
    for i in range(len(mark1)):
        top += (alpha[i] * abs(mark1[i] - mark2[i]))
        bottom += (alpha[i] * max(mark1[i], mark2[i]))

    if bottom == 0:
        return 0

    return top / float(bottom)


def sigmoid(x):
    return 1 / (1 + math.exp(-k * (x - 0.5)))


# 0: unsimilar. 1: similar
def block_similarity(block1, block2):
    birth_mark1 = block1["birthmark"]
    birth_mark2 = block2["birthmark"]
    sim_mark = vector_similarity(birth_mark1.get_vector(), birth_mark2.get_vector(), birth_mark1.get_alpha()) if not is_baseline \
        else vector_similarity(birth_mark1.get_baseline_vector(), birth_mark2.get_baseline_vector(), birth_mark1.get_baseline_alpha())
    meta_data1 = block1["metadata"]
    meta_data2 = block2["metadata"]
    sim_meta = vector_similarity(meta_data1.get_vector(), meta_data2.get_vector(), meta_data1.get_alpha())

    if (1 - sim_mark) + omega * sim_meta == 0:
        return 0
    sim_block = (1 - sim_mark) / float((1 - sim_mark) + omega * sim_meta)
    return sim_block


def compute_best_match(query, target):
    best = -100
    H0 = 0
    for b in target.keys():
        H0_score = block_similarity(query, target[b])
        H0 += sigmoid(H0_score)
    if len(target.keys()) == 0:
        p_H0 = 1
    else:
        p_H0 = H0 / float(len(target.keys()))

    for b in target.keys():
        score = block_similarity(query, target[b])
        p = sigmoid(score)
        if p > best:
            best = p

    if best <= 0 or p_H0 <= 0:
        return 0

    return math.log(best / float(p_H0))


def contract_similarity(contract1, contract2):
    similarity_1_1 = 0
    similarity_2_2 = 0
    similarity_1_2 = 0
    similarity_2_1 = 0

    for b1 in contract1.keys():
        similarity_1_1 += compute_best_match(contract1[b1], contract1)

    for b2 in contract2.keys():
        similarity_2_2 += compute_best_match(contract2[b2], contract2)

    for b1 in contract1.keys():
        similarity_1_2 += compute_best_match(contract1[b1], contract2)

    for b2 in contract2.keys():
        similarity_2_1 += compute_best_match(contract2[b2], contract1)

    if similarity_2_1 > similarity_1_2:
        return similarity_2_1, similarity_2_2
    else:
        return similarity_1_2, similarity_1_1
    # return max(similarity_1_2, similarity_2_1), max(similarity_1_1, similarity_2_2)
