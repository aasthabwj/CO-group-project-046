import sys

class RISCVSimulator:
    def __init__(self):
        self.registers = [0] * 32  # 32 registers initialized to 0
        self.memory = [0] * 32  # 32 x 32-bit memory initialized to 0
        self.pc = 0  # Program Counter (PC)

    def int_to_bin(self, num, bits=32):
        """Convert an integer to a fixed-length 32-bit binary string."""
        return bin(num & ((1 << bits) - 1))[2:].zfill(bits)

    def execute(self, input_file, output_file):
        """Main execution loop for the simulator."""
        try:
            with open(input_file, 'r') as f:
                program = [line.strip() for line in f.readlines() if line.strip()]

            with open(output_file, 'w') as f:
                pass  # Clear the output file before writing

            while self.pc < len(program):
                instruction = program[self.pc]

                # Error handling: Invalid instruction length
                if len(instruction) != 32 or not all(c in '01' for c in instruction):
                    print(f"Error: Invalid instruction at line {self.pc + 1}")
                    return  # Stop execution on first error

                # Halt condition: Virtual Halt instruction
                if instruction == '00000000000000000000000001100011':  
                    self.register_output(output_file)
                    break

                opcode = instruction[-7:]

                try:
                    match opcode:
                        case '0110011':  # R-type
                            self.rtype(instruction)
                        case '0000011' | '0010011' | '1100111':  # I-type
                            self.i_type(instruction)
                        case '0100011':  # S-type
                            self.stype(instruction)
                        case '1100011':  # B-type
                            self.btype(instruction)
                        case '0110111' | '0010111':  # U-type
                            self.utype(instruction)
                        case '1101111':  # J-type
                            self.j_type(instruction)
                        case _:
                            print(f"Error: Unknown opcode at line {self.pc + 1}")
                            return  # Stop execution on first error

                except Exception as e:
                    print(f"Error at line {self.pc + 1}: {str(e)}")
                    return  # Stop execution on first error

                self.register_output(output_file)
                self.pc += 1  # Move to the next instruction

            self.memory_output(output_file)

        except FileNotFoundError:
            print(f"Error: File {input_file} not found.")
        except Exception as e:
            print(f"Unexpected Error: {str(e)}")

    def register_output(self, output_file):
        """Write register contents after each instruction execution."""
        output = str(4 * self.pc)  # PC in decimal format
        for i in self.registers:
            output += " " + self.int_to_bin(i, 32)  # 32-bit binary format
        output += "\n"

        with open(output_file, "a") as file:
            file.write(output)

    def memory_output(self, output_file):
        """Write memory contents at the end of execution."""
        with open(output_file, "a") as file:
            for value in self.memory:
                file.write(self.int_to_bin(value, 32) + "\n")  # 32-bit binary format

    def rtype(self, instruction):
        """Execute R-type instructions (e.g., ADD, SUB, XOR, OR, AND)."""
        funct7 = instruction[:7]
        rs2 = int(instruction[7:12], 2)
        rs1 = int(instruction[12:17], 2)
        funct3 = instruction[17:20]
        rd = int(instruction[20:25], 2)

        match (funct7, funct3):
            case ('0000000', '000'):  # ADD
                self.registers[rd] = self.registers[rs1] + self.registers[rs2]
            case ('0100000', '000'):  # SUB
                self.registers[rd] = self.registers[rs1] - self.registers[rs2]
            case ('0000000', '100'):  # XOR
                self.registers[rd] = self.registers[rs1] ^ self.registers[rs2]
            case ('0000000', '110'):  # OR
                self.registers[rd] = self.registers[rs1] | self.registers[rs2]
            case ('0000000', '111'):  # AND
                self.registers[rd] = self.registers[rs1] & self.registers[rs2]
            case _:
                print(f"Error: Invalid R-type instruction at line {self.pc + 1}")
                exit()

    def i_type(self, instruction):
        """Execute I-type instructions (e.g., ADDI, XORI, ORI, ANDI)."""
        imm = int(instruction[:12], 2)
        rs1 = int(instruction[12:17], 2)
        funct3 = instruction[17:20]
        rd = int(instruction[20:25], 2)

        match funct3:
            case '000':  # ADDI
                self.registers[rd] = self.registers[rs1] + imm
            case '100':  # XORI
                self.registers[rd] = self.registers[rs1] ^ imm
            case '110':  # ORI
                self.registers[rd] = self.registers[rs1] | imm
            case '111':  # ANDI
                self.registers[rd] = self.registers[rs1] & imm
            case _:
                print(f"Error: Invalid I-type instruction at line {self.pc + 1}")
                exit()

    def stype(self, instruction):
        """Execute S-type instructions (stores)."""
        imm = int(instruction[:7] + instruction[20:25], 2)
        rs2 = int(instruction[7:12], 2)
        rs1 = int(instruction[12:17], 2)

        address = self.registers[rs1] + imm
        if 0 <= address < len(self.memory):
            self.memory[address] = self.registers[rs2]
        else:
            print(f"Error: Memory out of bounds at line {self.pc + 1}")
            exit()

    def btype(self, instruction):
        """Execute B-type instructions (branches)."""
        imm = int(instruction[:7] + instruction[20:25], 2)
        rs2 = int(instruction[7:12], 2)
        rs1 = int(instruction[12:17], 2)
        funct3 = instruction[17:20]

        match funct3:
            case '000':  # BEQ
                if self.registers[rs1] == self.registers[rs2]:
                    self.pc += imm - 1
            case '001':  # BNE
                if self.registers[rs1] != self.registers[rs2]:
                    self.pc += imm - 1
            case _:
                print(f"Error: Invalid B-type instruction at line {self.pc + 1}")
                exit()

    def utype(self, instruction):
        """Execute U-type instructions."""
        imm = int(instruction[:20], 2)
        rd = int(instruction[20:25], 2)

        self.registers[rd] = imm << 12

    def j_type(self, instruction):
        """Execute J-type instructions (jumps)."""
        imm = int(instruction[:20], 2)
        rd = int(instruction[20:25], 2)

        self.registers[rd] = self.pc * 4 + imm
        self.pc += imm - 1


# Entry point for running the simulator
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python simulator.py <input_file> <output_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        simulator = RISCVSimulator()
        simulator.execute(input_file, output_file)
