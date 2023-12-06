Reproduction of [Enabling Clone Detection For Ethereum via Smart Contract Birthmarks](https://ieeexplore.ieee.org/document/8813297) to compute similarity of bytecode.

---

There are two ways to test the similarity (The first one require the [`evm`](https://geth.ethereum.org/docs/getting-started/installing-geth) in the operating environment):

1. Two bytecode file input
2. One Address input (in dataset): Similarity of two bytecode compiled with/without --optimize

There are two ways to trigger the test process in `test.py`:

1. `single_test(bytecode1, bytecode2)`: output the result of similar or not.
2. `batch_test(address_list)`: output the result of accuracy of this address_list.

