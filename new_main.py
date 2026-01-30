import serial
import struct
import time
import address
from datetime import datetime

# ========== CONFIGURATION ==========
PORT = 'COM9'        # Serial port for RS485 communication
BAUDRATE = 9600      # Baud rate for Modbus RTU communication
SHOW_DEBUG = False   # True = show raw TX/RX frames
LOOP_DELAY = 1       # Delay in seconds between each reading cycle

# Multiple Battery Configuration
# Format: [(request_id, response_id, name), ...]
BATTERIES = [
    (0x81, 0x51, "Battery 1"),  # First battery pack
    (0x82, 0x52, "Battery 2"),  # Second battery pack
    (0x83, 0x53, "Battery 3"),  # Third battery pack
    # Add more as needed
]


def calculate_crc(data):
    """Calculate Modbus RTU CRC16 checksum"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)


def send_modbus_request(ser, slave_id, function_code, start_addr, count):
    """Send Modbus RTU request to BMS"""
    frame = struct.pack('>BBHH', slave_id, function_code, start_addr, count)
    crc = calculate_crc(frame)
    request = frame + crc

    if SHOW_DEBUG:
        print(f"📤 TX: {request.hex().upper()}")
    ser.write(request)
    time.sleep(0.05)


def read_modbus_response(ser, timeout=1.0):
    """Read Modbus RTU response from BMS"""
    start_time = time.time()
    response = b''

    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            response += ser.read(ser.in_waiting)
            time.sleep(0.02)  # Wait for more bytes

        # Minimum frame check
        if len(response) >= 5:
            # Modbus Function 03 response: ID(1) + Func(1) + Bytes(1) + Data(N) + CRC(2)
            if response[1] == 0x03:
                byte_count = response[2]
                expected_len = 5 + byte_count
                if len(response) >= expected_len:
                    break
            # Error response: ID(1) + Func(1) + Err(1) + CRC(2)
            elif response[1] >= 0x80:
                if len(response) >= 5:
                    break

    if response:
        if SHOW_DEBUG:
            print(f"📥 RX: {response.hex().upper()}")

        slave_id = response[0]
        function_code = response[1]

        if function_code >= 0x80:
            # print(f"❌ Error from Slave {slave_id:02X}: Code {response[2]:02X}")
            return None

        if function_code == 0x03:
            byte_count = response[2]
            data = response[3:3+byte_count]
            # Parse registers (Big Endian)
            registers = []
            for i in range(0, byte_count, 2):
                reg_value = struct.unpack('>H', data[i:i+2])[0]
                registers.append(reg_value)
            return registers

    return None


def main():
    try:
        print(f"🔌 Connecting to {PORT}...")
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUDRATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        print("✅ Connected!")
        time.sleep(1)

        cycle = 0
        while True:
            cycle += 1
            print(
                f"\n🔄 Cycle #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 120)
            print(f"{'Battery':<12} | {'Volt(V)':<7} | {'Curr(A)':<7} | {'SOC(%)':<6} | {'Status':<10} | {'Min(mV)':<7} | {'Max(mV)':<7} | {'Diff':<5} | {'Cell Temp(C)':<20}")
            print("-" * 120)

            for request_id, response_id, name in BATTERIES:
                # ========== Read Battery Temperature (0x30-0x37) ==========
                send_modbus_request(
                    ser, request_id, 0x03, address.BATT_TEMP_START_ADDRESS, address.BATT_TEMP_REGISTER_COUNT)
                temp_registers = read_modbus_response(ser)

                cell_temps = []
                if temp_registers and len(temp_registers) >= 4:
                    # Parse individual cell temperatures
                    cell_temp_1 = temp_registers[address.BATT_TEMP_OFFSET_CELL_1] - \
                        address.TEMP_OFFSET
                    cell_temp_2 = temp_registers[address.BATT_TEMP_OFFSET_CELL_2] - \
                        address.TEMP_OFFSET
                    cell_temp_3 = temp_registers[address.BATT_TEMP_OFFSET_CELL_3] - \
                        address.TEMP_OFFSET
                    cell_temp_4 = temp_registers[address.BATT_TEMP_OFFSET_CELL_4] - \
                        address.TEMP_OFFSET
                    cell_temps = [cell_temp_1, cell_temp_2, cell_temp_3, cell_temp_4]

                time.sleep(0.05)  # Small delay between requests

                # ========== Read Battery Pack Data (0x38-0x69) ==========
                # Note: Reading 50 registers (0x38 to 0x69)
                send_modbus_request(
                    ser, request_id, 0x03, address.START_ADDRESS, address.REGISTER_COUNT)
                registers = read_modbus_response(ser)

                if registers and len(registers) == address.REGISTER_COUNT:
                    # Parse Data
                    voltage = registers[address.OFFSET_VOLTAGE] / 10.0

                    raw_current = registers[address.OFFSET_CURRENT]
                    current = (raw_current - address.CURRENT_OFFSET) / 10.0

                    soc = registers[address.OFFSET_SOC] / 10.0

                    min_v = registers[address.OFFSET_MIN_CELL_V]
                    max_v = registers[address.OFFSET_MAX_CELL_V]
                    diff_v = registers[address.OFFSET_DIFF_CELL_V]

                    # Status Interpretation
                    status_val = registers[address.OFFSET_CHG_DISCHG_STATUS]
                    status_str = "Idle"
                    if status_val == 1:
                        status_str = "Charge"
                    elif status_val == 2:
                        status_str = "Dischg"

                    # Additional Info
                    cycles = registers[address.OFFSET_CYCLES]
                    rem_cap = registers[address.OFFSET_REMAINING_CAP] / 10.0

                    # Format cell temperatures
                    cell_temp_str = "/".join([f"{t}" for t in cell_temps]) if cell_temps else "--"

                    print(f"{name:<12} | {voltage:7.1f} | {current:7.1f} | {soc:6.1f} | {status_str:<10} | {min_v:<7} | {max_v:<7} | {diff_v:<5} | {cell_temp_str:<20}")

                    # Check for Faults
                    f1 = registers[address.OFFSET_FAULT_1]
                    f2 = registers[address.OFFSET_FAULT_2]
                    f3 = registers[address.OFFSET_FAULT_3]
                    f4 = registers[address.OFFSET_FAULT_4]

                    fault_list = address.get_fault_list(f1, f2, f3, f4)
                    if fault_list:
                        print(f"  ⚠️ FAULTS: {', '.join(fault_list)}")
                else:
                    print(
                        f"{name:<12} | {'--':^7} | {'--':^7} | {'--':^6} | {'Timeout':<10} | {'--':^7} | {'--':^7} | {'--':^5} | {'--':^20}")

                time.sleep(0.1)

            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        print("\n⏹️ Stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()


if __name__ == "__main__":
    main()
