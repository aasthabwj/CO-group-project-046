import sys
import re

# creating a dictionary for the different kinds of instructions
REGISTER_CODES = {
    "zero": "00000", "ra": "00001", "sp": "00010", "gp": "00011", "tp": "00100",
    "t0": "00101", "t1": "00110", "t2": "00111", "s0": "01000", "fp": "01000",
    "s1": "01001", "a0": "01010", "a1": "01011", "a2": "01100", "a3": "01101",
    "a4": "01110", "a5": "01111", "a6": "10000", "a7": "10001", "s2": "10010",
    "s3": "10011", "s4": "10100", "s5": "10101", "s6": "10110", "s7": "10111",
    "s8": "11000", "s9": "11001", "s10": "11010", "s11": "11011", "t3": "11100",
    "t4": "11101", "t5": "11110", "t6": "11111"
}

R_TYPE_CODES = {
    "add": ("0000000", "000"), "sub": ("0100000", "000"),
    "slt": ("0000000", "010"), "sltu": ("0000000", "011"),
    "srl": ("0000000", "101"), "or": ("0000000", "110"), "and": ("0000000", "111")
}

I_TYPE_CODES = {
    "lw": ("010", "0000011"), "addi": ("000", "0010011"), 
    "sltiu": ("011", "0010011"), "jalr": ("000", "1100111")
}

S_TYPE_CODES = ["sw"]

B_TYPE_CODES = {
    "beq": "000", "bne": "001", "blt": "100", "bltu": "110", "bgeu": "111"
}

U_TYPE_CODES = {'lui': '0110111', 'auipc': '0010111'}

J_TYPE_CODES = {'jal': '1101111'}

EXT_TYPE_CODES = {"mul", "rst", "halt", "rvrs"}

ALL_CODES = [R_TYPE_CODES, I_TYPE_CODES, S_TYPE_CODES, B_TYPE_CODES, U_TYPE_CODES, J_TYPE_CODES, EXT_TYPE_CODES]

# Helper Functions
def decimal_to_binary(n, bits):
    if n < 0:
        n = 2**bits + n
    return bin(n)[2:].zfill(bits)


def is_immediate_valid(imm, bits):
    return -(2**(bits-1)) <= imm < 2**(bits-1)


def check_virtual_halt(data):
    halt_code = "00000000000000000000000001100011"
    for i, line in enumerate(data):
        if line.strip() == halt_code:
            return 1 if i == len(data) - 1 else 0
    return -1


def process_labels(data):
    labels = {}
    for i, line in enumerate(data):
        match = re.match(r"(\w+):", line)
        if match:
            label = match.group(1)
            labels[label] = i * 4
            data[i] = line[match.end():].strip()

    for i, line in enumerate(data):
        for label, address in labels.items():
            data[i] = re.sub(rf'\b{label}\b', str(address - i * 4), line)




# R type instructions
def handle_r_type(instruction):
    parts = [part.strip() for part in instruction.split(",")]
    try:
        op, rd = parts[0].split()
        funct7, funct3 = R_TYPE_CODES[op]
        rs1, rs2 = REGISTER_CODES[parts[1]], REGISTER_CODES[parts[2]]
        return f"{funct7}{rs2}{rs1}{funct3}{REGISTER_CODES[rd]}0110011\n"
    except:
        return "error"


# I type instructions
def handle_i_type(instruction):
    parts = [part.strip() for part in instruction.split(",")]
    try:
        op, rd = parts[0].split()
        if op == "lw":
            imm_str = parts[1][:parts[1].index("(")]
            imm = int(imm_str)
            if not is_immediate_valid(imm, 12):
                return "ill_imm"
            rs1 = REGISTER_CODES[parts[1][parts[1].index("(")+1:parts[1].index(")")]]
            return f"{decimal_to_binary(imm, 12)}{rs1}010{REGISTER_CODES[rd]}0000011\n"
        else:
            imm = int(parts[2])
            if not is_immediate_valid(imm, 12):
                return "ill_imm"
            rs1 = REGISTER_CODES[parts[1]]
            funct3, opcode = I_TYPE_CODES[op]
            return f"{decimal_to_binary(imm, 12)}{rs1}{funct3}{REGISTER_CODES[rd]}{opcode}\n"
    except:
        return "error"

#S type instructions
def handle_s_type(instruction):
    parts = [part.strip() for part in instruction.split(",")]
    try:
        imm_str = parts[1][:parts[1].index("(")]
        imm = int(imm_str)
        if not is_immediate_valid(imm, 12):
            return "ill_imm"
        rs2 = REGISTER_CODES[parts[0].split()[1]]
        rs1 = REGISTER_CODES[parts[1][parts[1].index("(")+1:parts[1].index(")")]]
        imm_bin = decimal_to_binary(imm, 12)
        return f"{imm_bin[:7]}{rs2}{rs1}010{imm_bin[7:12]}0100011\n"
    except:
        return "error"

# B type instructions
def handle_b_type(instruction):
    parts = [part.strip() for part in instruction.split(",")]
    try:
        op, rs1 = parts[0].split()
        rs2 = REGISTER_CODES[parts[1]]
        imm = int(parts[2])
        if not is_immediate_valid(imm, 13):
            return "ill_imm"
        imm_bin = decimal_to_binary(imm, 13)
        imm_rearranged = imm_bin[0] + imm_bin[2:8] + imm_bin[8:12] + imm_bin[1]  
        return f"{imm_rearranged}{rs2}{REGISTER_CODES[rs1]}{B_TYPE_CODES[op]}1100011\n"
    except:
        return "error"


# U type instructions
def handle_u_type(instruction):
    parts = [part.strip() for part in instruction.split(",")]
    try:
        op, rd = parts[0].split()
        imm = int(parts[1])
        if not is_immediate_valid(imm, 32):
            return "error"
        imm_bin = decimal_to_binary(imm, 32)[:20]
        return f"{imm_bin}{REGISTER_CODES[rd]}{U_TYPE_CODES[op]}\n"
    except:
        return "error"

# J type instructions
def handle_j_type(instruction):
    parts = [part.strip() for part in instruction.split(",")]
    try:
        op, rd = parts[0].split()
        imm = int(parts[1])
        if not is_immediate_valid(imm, 21):
            return "error"
        imm_bin = decimal_to_binary(imm, 21)
        imm_combined = imm_bin[0] + imm_bin[10:20] + imm_bin[9] + imm_bin[1:9]
        return f"{imm_combined}{REGISTER_CODES[rd]}{J_TYPE_CODES[op]}\n"
    except:
        return "error"

def handle_ext_type(instruction):
    parts = [part.strip() for part in instruction.split(",")]
    op = parts[0].split()[0]
    try:
        if op == "mul":
            if len(parts) < 3:
                return "error"
            return f"0000000{REGISTER_CODES[parts[2]]}{REGISTER_CODES[parts[1]]}000{REGISTER_CODES[parts[0].split()[1]]}1111111\n"
        elif op == "rst":
            return "0000000111111111111111111111111\n" if len(parts) == 1 else "error"
        elif op == "halt":
            return "00000000000000000000000001100011\n" if len(parts) == 1 else "error"
        elif op == "rvrs":
            if len(parts) < 2:
                return "error"
            return f"000000000000{REGISTER_CODES[parts[1]]}001{REGISTER_CODES[parts[0].split()[1]]}1111111\n"
        else:
            return "error"
    except:
        return "error"


# Instruction to Binary Converter
def convert_instruction_to_binary(instruction):
    for i, code_set in enumerate(ALL_CODES):
        if instruction.split()[0] in code_set:
            return [handle_r_type, handle_i_type, handle_s_type, handle_b_type, handle_u_type, handle_j_type, handle_ext_type][i](instruction)
    return "error"


# Main Execution

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python assembler.py <input_file> <output_file> [--format=plain|spaced]")
        sys.exit(1)

    input_file, output_file = sys.argv[1], sys.argv[2]
    output_format = "plain"

    if len(sys.argv) == 4 and sys.argv[3].startswith("--format="):
        output_format = sys.argv[3].split("=")[1]

    with open(input_file, "r") as f:
        data = f.read().splitlines()

    process_labels(data)

    binary_output = []
    for i, line in enumerate(data):
        if not line.strip():
            continue

        binary_code = convert_instruction_to_binary(line)
        
        if binary_code == "error":
            print(f"Syntax Error at line {i+1}")
            sys.exit(1)
        elif binary_code == "ill_imm":
            print(f"Illegal immediate value at line {i+1}")
            sys.exit(1)
        
        binary_output.append(binary_code.strip())

    halt_status = check_virtual_halt(binary_output)

    if halt_status == 1:
        with open(output_file, "w") as f:
            if output_format == "spaced":
                f.write(" ".join(binary_output))
            else:
                f.write("\n".join(binary_output))
        print("Output file written successfully.")
    elif halt_status == 0:
        print("Virtual halt is not the last instruction")
    else:
        print("Virtual halt missing")

