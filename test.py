import multiprocessing
from bytecode_similarity import similarity_scoring_via_address, similarity_scoring_via_bytecode, similarity_scoring_via_different_address, similarity_score
import numpy as np
from tqdm import tqdm
from random import choice
import csv
import pandas as pd
from globals import threshold
from multiprocessing import Pool

is_baseline = True

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
        self.threshold = threshold

    def single_test(self, bytecode1, bytecode2):
        score = similarity_scoring_via_bytecode(bytecode1, bytecode2)['score']
        return 'similar!' if score > self.threshold else 'not similar!'

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
    myTest = TestEClone('./dataset/')
    num_of_cores = multiprocessing.cpu_count()
    target_num = 3156
    p = Pool(num_of_cores)
    fileName = './test/test_Baseline.csv' if is_baseline else './test/test_EClone.csv'
    test_cases = pd.read_csv('./test/test_cases.csv')

    for i in range(test_cases.shape[0]):
        file1, file2 = test_cases.iloc[i]['file1'], test_cases.iloc[i]['file2']
        p.apply_async(myTest.test_by_file, args=(file1, file2, fileName, test_cases.iloc[i]['label']))

    p.close()
    p.join()

