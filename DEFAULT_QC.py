from projectq import MainEngine
from projectq.ops import H, CNOT, Measure, Toffoli, X, All, T, Tdag
from projectq.backends import CircuitDrawer, ResourceCounter, ClassicalSimulator
from projectq.meta import Loop, Compute, Uncompute, Control

def Permutation(eng, x):

    index = [0, 5, 10, 15, 16, 21, 26, 31, 32, 37, 42, 47, 48, 53, 58, 63,
            64, 69, 74, 79, 80, 85, 90, 95, 96,101,106,111,112,117,122,127,
            12,  1,  6, 11, 28, 17, 22, 27, 44, 33, 38, 43, 60, 49, 54, 59,
            76, 65, 70, 75, 92, 81, 86, 91,108, 97,102,107,124,113,118,123,
            8, 13,  2,  7, 24, 29, 18, 23, 40, 45, 34, 39, 56, 61, 50, 55,
            72, 77, 66, 71, 88, 93, 82, 87,104,109, 98,103,120,125,114,119,
            4,  9, 14,  3, 20, 25, 30, 19, 36, 41, 46, 35, 52, 57, 62, 51,
            68, 73, 78, 67, 84, 89, 94, 83,100,105,110, 99,116,121,126,115]

    new_x = []
    for i in range(128):
        new_x.append(x[index[i]])

    return new_x

def lighter_r_layer(eng, b):

    temp = []
    temp.append(b[2])
    temp.append(b[3])
    temp.append(b[0])
    temp.append(b[1])

    CNOT | (temp[0], temp[3])
    CNOT | (temp[3], temp[1])
    Toffoli_gate(eng, temp[2], temp[1], temp[0])
    CNOT | (temp[2], temp[3])
    CNOT | (temp[1], temp[2])
    Toffoli_gate(eng, temp[3], temp[2], temp[0])
    CNOT | (temp[0], temp[2])

    new_b = []
    new_b.append(temp[3])
    new_b.append(temp[0])
    new_b.append(temp[1])
    new_b.append(temp[2])

    return new_b

def SubCells_layer(eng, b):

    for i in range(32):
        b[4*i:4*i+4] = lighter_r_layer(eng, b[4*i:4*i+4])

def lighter_r_core(eng, b):

    temp = []
    temp.append(b[3])
    temp.append(b[2])
    temp.append(b[0])
    temp.append(b[1])

    Toffoli_gate(eng, temp[2], temp[0], temp[1])
    Toffoli_gate(eng, temp[2], temp[1], temp[0])
    Toffoli_gate(eng, temp[3], temp[1], temp[2])
    CNOT | (temp[3], temp[1])
    X | temp[3]
    Toffoli_gate(eng, temp[1], temp[0], temp[3])
    Toffoli_gate(eng, temp[3], temp[0], temp[2])
    CNOT | (temp[1], temp[0])
    Toffoli_gate(eng, temp[2], temp[0], temp[3])

    new_b = []
    new_b.append(temp[3])
    new_b.append(temp[0])
    new_b.append(temp[1])
    new_b.append(temp[2])

    return new_b

def SubCells_core(eng, b):

    for i in range(32):
        b[4*i:4*i+4] = lighter_r_core(eng, b[4*i:4*i+4])

def AddRoundkey(eng, b, k0, k1, k2, k3, round):

    if(round % 4 == 0):
        CNOT128(eng, k0, b)
    if (round % 4 == 1):
        CNOT128(eng, k1, b)
    if (round % 4 == 2):
        CNOT128(eng, k2, b)
    if (round % 4 == 3):
        CNOT128(eng, k3, b)

def DEFAULT_Layer(eng, b, k0, k1, k2, k3):

    print('DEFAULT Layer...')
    round = 0

    # Round
    for i in range(28):
        SubCells_layer(eng, b)
        b = Permutation(eng, b)
        AddConstant(eng, b, round)
        AddRoundkey(eng, b, k0, k1, k2, k3, round)
        round = round + 1

    return b, k0, k1, k2, k3

def DEFAULT_Core(eng, b, k0, k1, k2, k3):

    print('DEFAULT Core...')
    round = 0

    # Round
    for i in range(24):
        SubCells_core(eng, b)
        b = Permutation(eng, b)
        AddConstant(eng, b, round)
        AddRoundkey(eng, b, k0, k1, k2, k3, round)
        round = round + 1

    return b, k0, k1, k2, k3

def CNOT128(eng, a, b):

    for i in range(128):
        CNOT | (a[i], b[i])

def KeySchedule(eng, k0, k1, k2, k3):

    CNOT128(eng, k0, k1)
    for i in range(4):
        SubCells_layer(eng, k1)
        k1 = Permutation(eng, k1)
        X | k1[127]
    CNOT128(eng, k1, k2)

    for i in range(4):
        SubCells_layer(eng, k1)
        k1 = Permutation(eng, k1)
        X | k1[127]
    CNOT128(eng, k1, k3)

    for i in range(4):
        SubCells_layer(eng, k1)
        k1 = Permutation(eng, k1)
        X | k1[127]

    return k0, k2, k3, k1

def AddConstant(eng, x, round):

    RoundConstants = [1, 3, 7, 15, 31, 62, 61, 59, 55, 47, 30, 60, 57, 51,
             39, 14, 29, 58, 53, 43, 22, 44, 24, 48, 33, 2, 5, 11]

    if (RoundConstants[round] & 1):
        X | x[3]
    if ((RoundConstants[round] >> 1) & 1):
        X | x[7]
    if ((RoundConstants[round] >> 2) & 1):
        X | x[11]
    if ((RoundConstants[round] >> 3) & 1):
        X | x[15]
    if ((RoundConstants[round] >> 4) & 1):
        X | x[19]
    if ((RoundConstants[round] >> 5) & 1):
        X | x[23]
    X | x[127]

def Round_constant_XOR(eng, k, rc, bit):
    for i in range(bit):
        if (rc >> i & 1):
            X | k[i]

def print_state(eng, b):

    All(Measure) | b
    print('Ciphertext : 0x', end='')
    print_hex(eng, b)
    print('\n')

def print_input(eng, b, k):
    All(Measure) | b
    All(Measure) | k
    print('Plaintext : 0x', end='')
    print_hex(eng, b)
    print('\nKey : 0x', end='')
    print_hex(eng, k)
    print('\n')

def print_hex(eng, qubits):

    for i in reversed(range(32)):
        temp = 0
        temp = temp+int(qubits[4*i+3])*8
        temp = temp+int(qubits[4*i+2])*4
        temp = temp+int(qubits[4*i+1])*2
        temp = temp+int(qubits[4*i])

        temp = hex(temp)
        y = temp.replace("0x", "")
        print(y, end='')

def Toffoli_gate(eng, a, b, c):

    if (resource_check):
        Tdag | a
        Tdag | b
        H | c
        CNOT | (c, a)
        T | a
        CNOT | (b, c)
        CNOT | (b, a)
        T | c
        Tdag | a
        CNOT | (b, c)
        CNOT | (c, a)
        T | a
        Tdag | c
        CNOT | (b, a)
        H | c
    else:
        Toffoli | (a, b, c)

def Run(eng):

    k0 = eng.allocate_qureg(128)
    k1 = eng.allocate_qureg(128)
    k2 = eng.allocate_qureg(128)
    k3 = eng.allocate_qureg(128)
    b = eng.allocate_qureg(128)

    if(not resource_check):
        Round_constant_XOR(eng, k0, 0x974c0adaa33900495909bea963df0a19, 128)
        Round_constant_XOR(eng, b, 0xe1e51e2e08f8588d6fb85911b25a1829, 128)
        print_input(eng, b, k0)

    k0, k1, k2, k3 = KeySchedule(eng, k0, k1, k2, k3)
    b, k0, k1, k2, k3 = DEFAULT_Layer(eng, b, k0, k1, k2, k3)
    b, k0, k1, k2, k3 = DEFAULT_Core(eng, b, k0, k1, k2, k3)
    b, k0, k1, k2, k3 = DEFAULT_Layer(eng, b, k0, k1, k2, k3)

    if (not resource_check):
        print_state(eng, b)

global resource_check
print('Generate Ciphertext...')
Simulate = ClassicalSimulator()
eng = MainEngine(Simulate)
resource_check = 0
Run(eng)

print('Estimate cost...')
Resource = ResourceCounter()
eng = MainEngine(Resource)
resource_check = 1
Run(eng)
print(Resource)
print('\n')
eng.flush()
