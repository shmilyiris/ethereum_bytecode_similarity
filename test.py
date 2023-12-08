from bytecode_similarity import similarity_scoring_via_address, similarity_scoring_via_bytecode, similarity_scoring_via_different_address
import numpy as np
import os
from tqdm import tqdm
from random import choice
import csv


class TestEClone():

    def __init__(self, dataset_dir):
        self.dataset_dir = dataset_dir
        self.bc_asm = dataset_dir + 'bytecode_without_opt/'
        self.bc_opt = dataset_dir + 'bytecode_opt/'
        self.op_asm = dataset_dir + 'opcode_without_opt/'
        self.op_opt = dataset_dir + 'opcode_opt/'
        self.source = dataset_dir + 'sol/'
        self.save_path = './address_to_score.csv'
        self.threshold = 0.84

    def single_test(self, bytecode1, bytecode2):
        score = similarity_scoring_via_bytecode(bytecode1, bytecode2)['score']
        return 'similar!' if score > self.threshold else 'not similar!'

    def batch_test(self, address_list):
        scores = np.array([])
        for address in tqdm(address_list, f"testing dataset with threshold of {self.threshold}"):
            score = similarity_scoring_via_address(address)['score']
            scores = np.append(scores, score)
            self.save_result(self.save_path, address, score)
        acc = len(scores[scores > self.threshold]) / len(scores)

        return acc

    def random_test(self, address_list, num):
        scores = np.array([])
        for i in range(num):
            addr1, addr2 = choice(address_list), choice(address_list)
            score = similarity_scoring_via_different_address(addr1, addr2)['score']
            scores = np.append(scores, score)
            print(f'{addr1} {addr2} {score}')
        acc = len(scores[scores > self.threshold]) / len(scores)

        return acc

    def save_result(self, save_path, address, similarity_score):
        with open(save_path, 'r', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([address, similarity_score])

if __name__ == '__main__':
    myTest = TestEClone('./dataset/')
    addrs = os.listdir(myTest.source)
    for i in range(len(addrs)):
        addrs[i] = addrs[i][:-4]

    # 1. two bytecode input (replace the parameters with your bytecode file position)
    # print(myTest.single_test(bytecode1, bytecode2))

    # 2. one address input
    acc = myTest.batch_test(address_list=addrs)

    # 3. random address input
    # acc = myTest.random_test(address_list=addrs, num=10)
    # print(f'accuracy is {acc}')
