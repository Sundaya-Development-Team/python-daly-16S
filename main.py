import serial
import struct
import time

# ========== CONFIGURATION ==========
PORT = 'COM9'        # Serial port for RS485 communication
BAUDRATE = 9600      # Baud rate for Modbus RTU communication
SHOW_DETAIL = False  # True = show detailed cell voltages, False = overview only
LOOP_DELAY = 2       # Delay in seconds between each reading cycle

# Multiple Battery Configuration
# Format: [(request_id, response_id, name), ...]
# Note: Daly BMS uses different slave IDs for request and response
# Request ID (e.g., 0x81) -> Response ID (e.g., 0x51)
BATTERIES = [
    (0x81, 0x51, "Battery 1"),  # First battery pack
    (0x82, 0x52, "Battery 2"),  # Second battery pack
    (0x83, 0x53, "Battery 3"),  # Third battery pack (add more as needed)
]

def calculate_crc(data):
    """Calculate Modbus RTU CRC16 checksum
    
    Args:
        data: Byte array of the Modbus frame (without CRC)
    
    Returns:
        2-byte CRC in little-endian format
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)  # Pack as little-endian 16-bit

def send_modbus_request(ser, slave_id, function_code, start_addr, count):
    """Send Modbus RTU request to BMS
    
    Args:
        ser: Serial port object
        slave_id: Target slave ID (request ID)
        function_code: Modbus function code (0x03 = Read Holding Registers)
        start_addr: Starting register address
        count: Number of registers to read
    """
    # Build Modbus RTU frame: [Slave ID][Function][Start Addr H][Start Addr L][Count H][Count L][CRC]
    frame = struct.pack('>BBHH', slave_id, function_code, start_addr, count)
    crc = calculate_crc(frame)
    request = frame + crc
    
    if SHOW_DETAIL:
        print(f"📤 TX: {request.hex().upper()}")
    ser.write(request)
    time.sleep(0.1)  # Small delay for transmission

def read_modbus_response(ser, expected_slave_id=None, timeout=1.0):
    """Read Modbus RTU response from BMS
    
    Args:
        ser: Serial port object
        expected_slave_id: Expected response slave ID (not enforced)
        timeout: Response timeout in seconds
    
    Returns:
        List of register values, or None if error/timeout
    """
    start_time = time.time()
    response = b''
    
    # Read response with timeout
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            response += ser.read(ser.in_waiting)
            time.sleep(0.05)  # Wait for complete frame
        
        # Check if we have received a complete frame
        if len(response) >= 5:  # Minimum frame: slave + func + len + crc(2)
            byte_count = response[2] if len(response) > 2 else 0
            expected_len = 5 + byte_count  # slave + func + count + data + crc(2)
            
            if len(response) >= expected_len:
                break
    
    if response:
        if SHOW_DETAIL:
            print(f"📥 RX: {response.hex().upper()}")
        
        # Parse response frame
        slave_id = response[0]
        function_code = response[1]
        
        # Check for Modbus error response (function code with MSB set)
        if function_code >= 0x80:
            error_code = response[2]
            if SHOW_DETAIL:
                print(f"❌ Modbus Error: Function={function_code:02X}, Error={error_code:02X}")
            return None
        
        # Parse normal response for function 03 (Read Holding Registers)
        if function_code == 0x03:
            byte_count = response[2]
            data = response[3:3+byte_count]
            
            # Extract register values (16-bit each, big-endian format)
            registers = []
            for i in range(0, byte_count, 2):
                reg_value = struct.unpack('>H', data[i:i+2])[0]
                registers.append(reg_value)
            
            return registers
    else:
        if SHOW_DETAIL:
            print("❌ No response")
    
    return None

# ========== MAIN PROGRAM ==========
try:
    # Initialize serial connection
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
    time.sleep(0.5)
    
    # Continuous monitoring loop
    cycle = 0
    while True:
        cycle += 1
        print("\n" + "="*60)
        print(f"🔄 Cycle #{cycle} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Read data from all configured batteries
        battery_data = {}
        
        for request_id, response_id, battery_name in BATTERIES:
            # Read first 16 registers (typically cell voltages 1-16)
            # Function 0x03 = Read Holding Registers, Address 0x0000, Count 16
            send_modbus_request(ser, request_id, 0x03, 0x0000, 0x0010)
            registers = read_modbus_response(ser, expected_slave_id=response_id)
            
            if registers:
                battery_data[battery_name] = registers
                
                # Show detailed cell voltages if SHOW_DETAIL is enabled
                if SHOW_DETAIL:
                    print(f"\n📊 Cell Voltages ({battery_name}):")
                    for i, value in enumerate(registers):
                        voltage_v = value / 1000.0
                        print(f"  Cell {i+1:2d}: {value:4d} mV ({voltage_v:.3f} V)")
            
            time.sleep(0.1)  # Short delay between battery reads
        
        # Display overview summary (always shown)
        print("\n📋 OVERVIEW:")
        print("-" * 60)
        for battery_name, registers in battery_data.items():
            # Calculate battery pack statistics
            total_v = sum(registers) / 1000.0     # Total pack voltage in volts
            min_cell = min(registers)              # Minimum cell voltage in mV
            max_cell = max(registers)              # Maximum cell voltage in mV
            delta = max_cell - min_cell            # Cell imbalance (delta) in mV
            avg_v = total_v / len(registers)       # Average cell voltage
            
            # Print summary line for each battery
            print(f"🔋 {battery_name:12s} | Total: {total_v:5.2f}V | Avg: {avg_v:.3f}V | "
                  f"Min: {min_cell}mV | Max: {max_cell}mV | Δ: {delta}mV")
        
        if not battery_data:
            print("❌ No batteries detected!")
        
        print("-" * 60)
        print(f"⏳ Next read in {LOOP_DELAY}s... (Press Ctrl+C to stop)")
        
        time.sleep(LOOP_DELAY)
    
except KeyboardInterrupt:
    # Handle user interrupt (Ctrl+C)
    print("\n\n⏹️  Stopped by user")
    ser.close()
    print("✅ Connection closed")

except serial.SerialException as e:
    # Handle serial port errors
    print(f"❌ Serial Error: {e}")
except Exception as e:
    # Handle any other unexpected errors
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
