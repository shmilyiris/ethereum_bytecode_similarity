import multiprocessing
from bytecode_similarity import similarity_scoring_via_address, similarity_scoring_via_bytecode, similarity_scoring_via_different_address, similarity_score
import numpy as np
from tqdm import tqdm
from random import choice
import csv
import pandas as pd
from globals import threshold
from multiprocessing import Pool
import pandas as pd
import time

def write_row(save_path, row):
    with open(save_path, 'a+', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)

class TestEClone():

    def __init__(self, dataset_dir):
        self.dataset_dir = dataset_dir
        self.bc_asm = dataset_dir + 'bytecode_without_opt/'
        self.bc_opt = dataset_dir + 'bytecode_opt/'
        self.op_asm = dataset_dir + 'opcode_without_opt/'
        self.op_opt = dataset_dir + 'opcode_opt/'
        self.source = dataset_dir + 'sol/'
        self.positive_path = './test/positive.csv'
        self.negative_path = './test/negative.csv'
        self.threshold = 0.9

    def single_test(self, bytecode1, bytecode2):
        res = similarity_scoring_via_bytecode(bytecode1, bytecode2)['score']
        return res

    def batch_test(self, address_list):
        scores = np.array([])
        for address in tqdm(address_list, f"testing dataset with threshold of {self.threshold}"):
            score = similarity_scoring_via_address(address)['score']
            scores = np.append(scores, score)
            write_row(self.positive_path, [address, score])
        acc = len(scores[scores > self.threshold]) / len(scores)

        return acc

    def random_test(self, address_list, num):
        for _ in [0 for i in range(num)]:
            addr1 = addr2 = ''
            while addr1 == addr2:
                addr1, addr2 = choice(address_list), choice(address_list)

            if addr2 < addr1:
                addr1, addr2 = addr2, addr1
            score = similarity_scoring_via_different_address(addr1, addr2)['score']
            write_row(self.negative_path, [addr1, addr2, score])

    def test_by_file(self, disasm_file1, disasm_file2, fileName, label):
        # ./dataset/
        score = similarity_score(disasm_file1, disasm_file2)['score']
        write_row(fileName, [disasm_file1, disasm_file2, score, label])



if __name__ == '__main__':
    benchmark = pd.read_csv('benchmark.csv')
    rootDir = './bytecode/'
    myTest = TestEClone('./dataset/')
    T1 = time.time()

    scoreList = []
    for i in range(benchmark.shape[0]):
        addr1, addr2 = benchmark.iloc[i]['addr1'], benchmark.iloc[i]['addr2']
        bytecode1, bytecode2 = rootDir + addr1 + '.txt', rootDir + addr2 + '.txt'
        res = myTest.single_test(bytecode1, bytecode2)
        scoreList.append(res)
        print(res)
    benchmark['EClone Score'] = scoreList
    benchmark.to_csv('benchmark_EClone.csv')

    T2 = time.time()
    print(T2, T1)
    print(f'Execution Time {(T2 - T1) * 1000}ms.')

