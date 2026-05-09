import sys

reg_table = {
    '00000': 'zero', '00001': 'ra',   '00010': 'sp',   '00011': 'gp',
    '00100': 'tp',   '00101': 't0',   '00110': 't1',   '00111': 't2',
    '01000': 's0',   '01001': 's1',   '01010': 'a0',   '01011': 'a1',
    '01100': 'a2',   '01101': 'a3',   '01110': 'a4',   '01111': 'a5',
    '10000': 'a6',   '10001': 'a7',   '10010': 's2',   '10011': 's3',
    '10100': 's4',   '10101': 's5',   '10110': 's6',   '10111': 's7',
    '11000': 's8',   '11001': 's9',   '11010': 's10',  '11011': 's11',
    '11100': 't3',   '11101': 't4',   '11110': 't5',   '11111': 't6'
}

#register
# Define constants for memory range
MEM_START = 65536   # 0x10000
MEM_END = 65660      # 0x1007C
MEM_STEP = 4

mem_data = {
    f"0x{loc:08X}": 0 for loc in range(MEM_START, MEM_END + 1, MEM_STEP)
}
#memory values
REGISTER_WIDTH = 32
STACK_POINTER_INIT = 0x17C  # 380 in decimal

reg_data = {
    reg: '0'*REGISTER_WIDTH 
    for reg in reg_table.keys()
}
reg_data['00010'] = bin(STACK_POINTER_INIT)[2:].zfill(REGISTER_WIDTH)
#register values
instructions = {
    # R-type instructions
    '0110011': {
        '0000000': {
            '000': 'add',  # Add
            '010': 'slt',  # Set less than
            '101': 'srl',  # Shift right logical
            '110': 'or',   # Bitwise OR
            '111': 'and'   # Bitwise AND
        },
        '0100000': {
            '000': 'sub'   # Subtract
        }
    },
    # I-type instructions
    '0000011': {'': {'010': 'lw'}},     # Load word
    '0010011': {'': {'000': 'addi'}},   # Add immediate
    '1100111': {'': {'000': 'jalr'}},   # Jump and link register
    # S-type instructions
    '0100011': {'': {'010': 'sw'}},     # Store word
    # B-type instructions
    '1100011': {
        '': {
            '000': 'beq',  # Branch equal
            '001': 'bne',  # Branch not equal
            '100': 'blt'   # Branch less than
        }
    },
    # J-type instructions
    '1101111': {'': 'jal'}  # Jump and link
}
#Creating a dictionary of dictionary for opcode table


def state_snapshot(pc, mem_range=None):
    """Generate state snapshot including memory context"""
    output = f"0b{pc:032b}"
    output += ' ' + ' '.join(f'0b{reg_data[reg]}' for reg in sorted(reg_data))
    output += '\n'
    
    if mem_range:
        output += "Memory:\n"
        for addr in range(mem_range[0], mem_range[1]+1, 4):
            addr_hex = f"0x{addr:08X}"
            if addr_hex in mem_data:
                output += f"{addr_hex}: 0b{mem_data[addr_hex]:032b}\n"
    
    return output

#checking instruction type

def check_R_type(opcode, funct7, funct3):
    """Validate R-type instruction fields"""
    try:
        if funct7 in instructions[opcode] and funct3 in instructions[opcode][funct7]:
            return True
    except KeyError:
        pass
    raise ValueError(
        f"Invalid R-type instruction: opcode={opcode}, funct7={funct7}, funct3={funct3}\n"
        f"Valid combinations for opcode {opcode}: {instructions[opcode]}"
    )

def check_S_type(opcode, funct3):
    """Validate S-type instruction fields"""
    try:
        if '' in instructions[opcode] and funct3 in instructions[opcode]['']:
            return True
    except KeyError:
        pass
    raise ValueError(
        f"Invalid S-type instruction: opcode={opcode}, funct3={funct3}\n"
        f"Valid funct3 values: {instructions[opcode].get('', {}).keys()}"
    )

def check_I_type(opcode, funct3):
    """Validate I-type instruction fields"""
    try:
        if '' in instructions[opcode] and funct3 in instructions[opcode]['']:
            return True
    except KeyError:
        pass
    raise ValueError(
        f"Invalid I-type instruction: opcode={opcode}, funct3={funct3}\n"
        f"Valid funct3 values: {instructions[opcode].get('', {}).keys()}"
    )

def check_B_type(opcode, funct3):
    """Validate B-type instruction fields"""
    try:
        if '' in instructions[opcode] and funct3 in instructions[opcode]['']:
            return True
    except KeyError:
        pass
    raise ValueError(
        f"Invalid B-type instruction: opcode={opcode}, funct3={funct3}\n"
        f"Valid funct3 values: {instructions[opcode].get('', {}).keys()}"
    )

def check_J_type(opcode):
    """Validate J-type instruction"""
    try:
        if '' in instructions[opcode]:
            return True
    except KeyError:
        pass
    raise ValueError(
        f"Invalid J-type instruction: opcode={opcode}\n"
        f"Valid J-type opcodes: {[k for k,v in instructions.items() if '' in v]}"
    )

instr_type_map = {
    # R-type instructions
    '0110011': 'R',  # Register-register operations
    
    # I-type instructions
    '0000011': 'I',  # Load instructions
    '0010011': 'I',  # Immediate operations
    '1100111': 'I',  # Jump and link register
    
    # S-type instructions
    '0100011': 'S',  # Store instructions
    
    # B-type instructions
    '1100011': 'B',  # Branch instructions
    
    # J-type instructions
    '1101111': 'J'   # Jump and link
}

def extend_sign(value: str, bit_width: int = 32) -> str:
    """Optimized sign extension for fixed 32-bit width."""
    if len(value) >= 32:
        return value[-32:]
    
    sign_bit = value[0]
    return (sign_bit * (32 - len(value))) + value

def compare_signed(a: str, b: str) -> bool:
    """Safe comparison with input validation."""
    if len(a) != 32 or len(b) != 32:
        raise ValueError("Inputs must be 32-bit binary strings")
    if not all(c in '01' for c in a+b):
        raise ValueError("Inputs must contain only 0s and 1s")
    
    a_int = int(a, 2)
    b_int = int(b, 2)
    
    # Handle two's complement
    if a[0] == '1':
        a_int -= 1 << 32
    if b[0] == '1':
        b_int -= 1 << 32
        
    return a_int < b_int


def convert_bin_to_int(binary_str: str) -> int:
    """Convert with thorough input validation."""
    if not isinstance(binary_str, str):
        raise TypeError("Input must be a binary string")
    if not binary_str:
        return 0
    if not all(c in '01' for c in binary_str):
        raise ValueError("Input must contain only 0s and 1s")
    
    if binary_str[0] == '0':
        return int(binary_str, 2)
    return -((1 << (len(binary_str)-1)) - int(binary_str[1:], 2))



def execute_R_instr(opcode, funct7, source_reg2, source_reg1, funct3, dest_reg):
    operation = instructions[opcode][funct7][funct3]

    if operation == 'add':
        result = int(reg_data[source_reg1], 2) + int(reg_data[source_reg2], 2)
    elif operation == 'sub':
        result = int(reg_data[source_reg1], 2) - int(reg_data[source_reg2], 2)
    elif operation == 'slt':
        result = 1 if compare_signed(reg_data[source_reg1], reg_data[source_reg2]) else 0
    elif operation == 'srl':
        shift_amt = int(reg_data[source_reg2][-5:], 2)
        result = int(reg_data[source_reg1], 2) >> shift_amt
    elif operation == 'or':
        result = int(reg_data[source_reg1], 2) | int(reg_data[source_reg2], 2)
    elif operation == 'and':
        result = int(reg_data[source_reg1], 2) & int(reg_data[source_reg2], 2)
    else:
        return

    reg_data[dest_reg] = format(result & 0xFFFFFFFF, '032b')

def execute_S_instr(opcode, immediate, source_reg1, source_reg2, funct3, program_counter):
    if instructions[opcode][''][funct3] == 'sw':
        imm_val = int(extend_sign(immediate), 2)
        memory_address = int(reg_data[source_reg1], 2) + imm_val
        memory_address_hex = f"0x{memory_address:08X}"
        mem_data[memory_address_hex] = int(reg_data[source_reg2], 2)
    return program_counter + 4

def execute_J_instr(opcode, immediate, dest_reg, program_counter):
    if instructions[opcode][''] == 'jal':
        imm_val = int(extend_sign(immediate), 2)
        if immediate[0] == '1':
            imm_val -= (1 << 32)
        reg_data[dest_reg] = format(program_counter + 4, '032b')
        return program_counter + imm_val
    return reg_data[dest_reg]

def execute_I_instr(immediate, source_reg1, funct3, dest_reg, opcode, program_counter, instruction_line):
    imm_val = int(extend_sign(immediate), 2)
    if immediate[0] == '1':
        imm_val -= (1 << 32)

    operation = instructions[opcode][''][funct3]

    if operation == 'addi':
        result = int(reg_data[source_reg1], 2) + imm_val
        reg_data[dest_reg] = format(result & 0xFFFFFFFF, '032b')
        return program_counter + 4

    elif operation == 'jalr':
        new_pc = (int(reg_data[source_reg1], 2) + imm_val) & ~1
        reg_data[dest_reg] = format(program_counter + 4, '032b')
        return new_pc

    elif operation == 'lw':
        memory_address = int(reg_data[source_reg1], 2) + imm_val
        memory_address_hex = f"0x{memory_address:08X}"
        reg_data[dest_reg] = format(mem_data[memory_address_hex], '032b')
        return program_counter + 4

def execute_B_instr(opcode, immediate, source_reg1, source_reg2, program_counter, funct3):
    immediate += '0'
    imm_val = int(extend_sign(immediate), 2)
    if immediate[0] == '1':
        imm_val -= (1 << 32)

    operation = instructions[opcode][''][funct3]

    if operation == 'beq':
        if reg_data[source_reg1] == reg_data[source_reg2]:
            return "HALT" if imm_val == 0 else program_counter + imm_val
    elif operation == 'bne':
        if reg_data[source_reg1] != reg_data[source_reg2]:
            return program_counter + imm_val
    elif operation == 'blt':
        if convert_bin_to_int(reg_data[source_reg1]) < convert_bin_to_int(reg_data[source_reg2]):
            return program_counter + imm_val

    return program_counter + 4



def state_snapshot(pc: int, include_memory: bool = False, mem_range: tuple[int, int] = None) -> str:
    # Generate register state line
    reg_state = ' '.join(f'0b{reg_data[reg]}' for reg in sorted(reg_data))
    snapshot = [f"PC: 0b{pc:032b} (0x{pc:08X})"]
    snapshot.append(f"Registers: {reg_state}")
    
    # Optionally include memory contents
    if include_memory:
        mem_start, mem_end = mem_range if mem_range else (MEM_START, MEM_END)
        snapshot.append("\nMemory Contents:")
        for addr in range(mem_start, mem_end + 1, MEM_STEP):
            addr_hex = f"0x{addr:08X}"
            snapshot.append(f"{addr_hex}: 0b{mem_data[addr_hex]:032b}")
    
    return '\n'.join(snapshot) + '\n'



def execute_program(instructions_list, output_file):
    output = ""

    instructions_list = [x.strip() for x in instructions_list]
    instructions_list = [x for x in instructions_list if x]
    instr_memory = {}

    i = 0
    while i < len(instructions_list):
        instr_memory[i * 4] = instructions_list[i]
        i += 1
    
    pc = 0
    while pc in instr_memory:
        last_pc=pc

        curr_instr = instr_memory[pc]
        opcode = curr_instr[-7:]
        if opcode not in instructions:
            raise ValueError("OPcode isn't there")
        instr_type = instr_type_map[opcode]

        if instr_type == 'R':
            fun7 = curr_instr[:7]
            rs2 = curr_instr[7:12]
            rs1 = curr_instr[12:17]
            fun3 = curr_instr[17:20]
            rd = curr_instr[20:25]

            assert check_R_type(opcode, fun7, fun3)
            assert rs1 in reg_table
            assert rs2 in reg_table
            assert rd in reg_table
            execute_R_instr(opcode, fun7, rs2, rs1, fun3, rd)
            pc += 4

        elif instr_type == 'I':
            imm = curr_instr[:12]
            rs1 = curr_instr[12:17]
            fun3 = curr_instr[17:20]
            rd = curr_instr[20:25]
            assert check_I_type(opcode, fun3)
            assert rs1 in reg_table
            pc = execute_I_instr(imm, rs1, fun3, rd, opcode, pc, curr_instr)

        elif instr_type == 'S':
            imm = curr_instr[:7]+curr_instr[20:25]
            rs2 = curr_instr[7:12]
            rs1 = curr_instr[12:17]
            fun3 = curr_instr[17:20]
            assert check_S_type(opcode, fun3)
            assert rs1 in reg_table
            assert rs2 in reg_table
            pc = execute_S_instr(opcode, imm, rs1, rs2, fun3, pc)

        elif instr_type == 'B':
            imm = curr_instr[0]+curr_instr[24]+curr_instr[1:7]+curr_instr[20:24]
            rs2 = curr_instr[7:12]
            rs1 = curr_instr[12:17]
            fun3 = curr_instr[17:20]
            assert check_B_type(opcode, fun3)
            assert rs1 in reg_table
            assert rs2 in reg_table
            old_pc = pc
            pc = execute_B_instr(opcode, imm, rs1, rs2, pc, fun3)
            if pc == "HALT":
                output += f"0b{format(old_pc, '032b')} "
                for i in reg_data.keys():
                    output += f"0b{reg_data[i]} "
                output += "\n"
                break #for halting the program
                        
        elif instr_type == 'J':
            imm = curr_instr[0] + curr_instr[12:20] + curr_instr[11] + curr_instr[1:11]+'0'
            rd = curr_instr[20:25]
            assert rd in reg_table
            assert check_J_type(opcode)
            assert rd in reg_table
            pc = execute_J_instr(opcode, imm, rd, pc)
        else:
            raise ValueError("OPcode isn't there")

        if pc=='HALT':
            output += "0b" + format(int(last_pc), "032b") + " "
        else:
            output += "0b" + format(int(pc), "032b") + " "
        reg_data['00000'] = "0" * 32
        for i in reg_data.keys():
            output += "0b" + reg_data[i] + " "
        output += "\n"

    for loc in range(65536, 65660 + 1, 4):
        loc_hex = f"0x{loc:08X}"  # Correctly format the hex address
        output += f"{loc_hex}:0b{format(mem_data[loc_hex], '032b')}\n"

    with open(output_file, "w") as f:
        f.write(output.strip())


if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, "r") as f:
        instructions_list = f.readlines()
    execute_program(instructions_list, output_file)