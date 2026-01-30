# Daly BMS Modbus Register Addresses
# Based on Protocol 8 6 16

# Data format: 9600 8-bit data, 1 stop bit, no checksum
# High bit first, low bit last (Big Endian)

# ========== BATTERY TEMPERATURE SECTION ==========
# Battery Temperature Registers (Separate read from main pack data)
# Address: 0x30 - 0x37 (8 registers for cell temperature 1-4)
# Data offset: 40 (actual temperature = register value - 40)
BATT_TEMP_START_ADDRESS = 0x30
BATT_TEMP_REGISTER_COUNT = 8  # 0x30 to 0x37

# Offsets from BATT_TEMP_START_ADDRESS (0x30)
BATT_TEMP_OFFSET_CELL_1 = 0x00  # 0x30: Cell Temperature 1
BATT_TEMP_OFFSET_CELL_2 = 0x01  # 0x31: Cell Temperature 2
BATT_TEMP_OFFSET_CELL_3 = 0x02  # 0x32: Cell Temperature 3
BATT_TEMP_OFFSET_CELL_4 = 0x03  # 0x33: Cell Temperature 4
# 0x34 - 0x37: Reserved or additional cells

# ========== BATTERY PACK DATA SECTION ==========
# Start Address for Battery Pack Data
START_ADDRESS = 0x38
# Previous Count: 21 (0x38 - 0x4C)
# New End Address: 0x69 (Fault Status 4)
# Total Registers: 0x69 - 0x38 + 1 = 50 registers
REGISTER_COUNT = 50

# Register Offests from START_ADDRESS (0x38)
OFFSET_VOLTAGE = 0x00  # 0x38: Total Battery Voltage (0.1V)
OFFSET_CURRENT = 0x01  # 0x39: Current (Offset 30000, 0.1A)
OFFSET_SOC = 0x02  # 0x3A: SOC (0.1%)
OFFSET_LIFE = 0x03  # 0x3B: Life (Heartbeat?)
OFFSET_BATT_QTY = 0x04  # 0x3C: Battery quantity
OFFSET_TEMP_QTY = 0x05  # 0x3D: Temp sensor quantity
OFFSET_MAX_CELL_V = 0x06  # 0x3E: Max cell voltage (mV)
OFFSET_MAX_CELL_NO = 0x07  # 0x3F: Max cell voltage serial number
OFFSET_MIN_CELL_V = 0x08  # 0x40: Min cell voltage (mV)
OFFSET_MIN_CELL_NO = 0x09  # 0x41: Min cell voltage serial number
OFFSET_DIFF_CELL_V = 0x0A  # 0x42: Max-Min cell voltage diff (mV)
OFFSET_MAX_TEMP = 0x0B  # 0x43: Max cell temp (Offset 40)
OFFSET_MAX_TEMP_NO = 0x0C  # 0x44: Max cell temp serial number
OFFSET_MIN_TEMP = 0x0D  # 0x45: Min cell temp (Offset 40)
OFFSET_MIN_TEMP_NO = 0x0E  # 0x46: Min cell temp serial number
OFFSET_DIFF_TEMP = 0x0F  # 0x47: Max-Min temp diff
OFFSET_CHG_DISCHG_STATUS = 0x10  # 0x48: 0=Stationary, 1=Charge, 2=Discharge
OFFSET_CHARGER_STATUS = 0x11  # 0x49: 0=No charger, 1=Charger detected
OFFSET_LOAD_STATUS = 0x12  # 0x4A: 0=No load, 1=Load detected
OFFSET_REMAINING_CAP = 0x13  # 0x4B: Remaining capacity (0.1AH)
OFFSET_CYCLES = 0x14  # 0x4C: Cycle times

# New Registers (0x4D - 0x69)
# 0x4D: Equilibrium state (0:Off, 1:Passive, 2:Active)
OFFSET_EQUIL_STATE = 0x15
OFFSET_BALANCED_CUR = 0x16  # 0x4E: Balanced current (0.1A)
OFFSET_EQUIL_POS_H = 0x17  # 0x4F: Equilibrium position High
# 0x50: Equilibrium position Low # Note: 0x4F-0x51 in docs? Assuming standard 16-bit registers.
OFFSET_EQUIL_POS_L = 0x18
OFFSET_EQUIL_POS_2 = 0x19  # 0x51: ...
OFFSET_CHG_MOS_STATUS = 0x1A  # 0x52: Charging MOS status (0:off, 1:on)
OFFSET_DIS_MOS_STATUS = 0x1B  # 0x53: Discharge MOS status (0:off, 1:on)
OFFSET_PRE_MOS_STATUS = 0x1C  # 0x54: Precharge MOS status
OFFSET_HEAT_MOS_STATUS = 0x1D  # 0x55: Heating MOS status
OFFSET_FAN_MOS_STATUS = 0x1E  # 0x56: Fan MOS status
OFFSET_AVG_VOLTAGE = 0x1F  # 0x57: Average voltage (1mV)
OFFSET_POWER = 0x20  # 0x58: Power (W)
OFFSET_ENERGY = 0x21  # 0x59: Energy (1Wh)
OFFSET_MOS_TEMP = 0x22  # 0x5A: MOS temperature (Offset 40)
OFFSET_AMBIENT_TEMP = 0x23  # 0x5B: Ambient temperature (Offset 40)
OFFSET_HEAT_TEMP = 0x24  # 0x5C: Heating temperature (Offset 40)
OFFSET_HEAT_CURRENT = 0x25  # 0x5D: Heating current (1A?)
OFFSET_REM_MILEAGE = 0x26  # 0x5E: Remaining mileage
OFFSET_CUR_LIMIT_STATE = 0x27  # 0x5F: Current limiting state
OFFSET_CUR_LIMIT = 0x28  # 0x60: Current limit (0.1A, Offset 30000)
OFFSET_RTC_1 = 0x29  # 0x61
OFFSET_RTC_2 = 0x2A  # 0x62
OFFSET_RTC_3 = 0x2B  # 0x63
OFFSET_REM_CHG_TIME = 0x2C  # 0x64: Remaining charging time (min)
# 0x65 Reserved?

OFFSET_FAULT_1 = 0x2E  # 0x66: Fault Status 1
OFFSET_FAULT_2 = 0x2F  # 0x67: Fault Status 2
OFFSET_FAULT_3 = 0x30  # 0x68: Fault Status 3
OFFSET_FAULT_4 = 0x31  # 0x69: Fault Status 4

# Constants for Calculation
CURRENT_OFFSET = 30000
TEMP_OFFSET = 40

# ========== FAULT STATUS SECTION ==========


def get_fault_list(f1, f2, f3, f4):
    """Parse fault registers and return list of active fault strings."""
    faults = []

    # --- Fault Status 1 (0x66) ---
    # Byte 0 (High Byte of register in Big Endian?) -> Actually Modbus register is 16-bit.
    # Docs say "Byte 0" and "Byte 1". Usually in Modbus 16-bit int:
    # High Byte = Bits 8-15, Low Byte = Bits 0-7.
    # BUT checks usually "Bit 0" of "Byte 0".
    # Let's assume the doc "Byte 0" corresponds to Low Byte (0-7) or High Byte?
    # Standard Daly often: High Byte (First received) = Byte 0? Or Low Byte?
    # Let's interpret simplisticly: 16-bit Value.
    # Doc: "Byte 0: Bit 0...".
    # If reg value is 0xAABB, Byte 0 usually means AA (High) or BB (Low)?
    # In Modbus 0x66, value 0x1234 -> High Byte 0x12, Low Byte 0x34.
    # If doc says "Byte 0... Bit 0", it might mean "First Byte, First Bit".
    # Let's support both 16-bit mapping directly if "Level 1 alarm...".
    # For now, I'll map assuming "Byte 0" is the LSB (Low Byte) and "Byte 1" is MSB (High Byte) OR vice versa.
    # Let's simply break 16-bit val into LSB and MSB.
    # val = (MSB << 8) | LSB.

    # Fault 1
    # Byte 0 (bits 0-7): Cell V High 1/2, Low 1/2...
    # Byte 1 (bits 0-7): Charge Temp High, etc.

    # Let's create dictionaries/lists for bits.
    # We will assume: Reg Value = (Byte 1 << 8) | Byte 0   OR   (Byte 0 << 8) | Byte 1.
    # Typically in Chinese BMS docs:
    # "Byte 0" is often the first byte transmitted (MSB in Big Endian Modbus).
    # "Bit 0" is the LSB of that byte.

    f1_msb = (f1 >> 8) & 0xFF  # Byte 0?
    f1_lsb = f1 & 0xFF         # Byte 1?

    # MAPPING based on typical Daly order (Subject to verification)
    # Usually: Alarm 1 (Warning), Alarm 2 (Protection).
    # Let's list checks.

    # Fault 1 - Voltage (Byte 0?) & Temp (Byte 1?)
    # Let's treat as bitmasks on the full 16-bit word if possible, or per byte.
    # Doc Order:
    # Byte 0:
    # 0: Cell V High L1
    # 1: Cell V High L2
    # 2: Cell V Low L1
    # 3: Cell V Low L2
    # 4: Pack V High L1
    # 5: Pack V High L2
    # 6: Pack V Low L1
    # 7: Pack V Low L2

    # If f1_msb matches this 'Byte 0', then:
    if f1_msb & 0x01:
        faults.append("Cell V High L1")
    if f1_msb & 0x02:
        faults.append("Cell V High L2")
    if f1_msb & 0x04:
        faults.append("Cell V Low L1")
    if f1_msb & 0x08:
        faults.append("Cell V Low L2")
    if f1_msb & 0x10:
        faults.append("Pack V High L1")
    if f1_msb & 0x20:
        faults.append("Pack V High L2")
    if f1_msb & 0x40:
        faults.append("Pack V Low L1")
    if f1_msb & 0x80:
        faults.append("Pack V Low L2")

    # Byte 1 - Temps
    if f1_lsb & 0x01:
        faults.append("Chg Temp High L1")
    if f1_lsb & 0x02:
        faults.append("Chg Temp High L2")
    if f1_lsb & 0x04:
        faults.append("Chg Temp Low L1")
    if f1_lsb & 0x08:
        faults.append("Chg Temp Low L2")
    if f1_lsb & 0x10:
        faults.append("Dischg Temp High L1")
    if f1_lsb & 0x20:
        faults.append("Dischg Temp High L2")
    if f1_lsb & 0x40:
        faults.append("Dischg Temp Low L1")
    if f1_lsb & 0x80:
        faults.append("Dischg Temp Low L2")

    # Fault 2 - Current / SOC / Diff
    f2_msb = (f2 >> 8) & 0xFF
    f2_lsb = f2 & 0xFF

    if f2_msb & 0x01:
        faults.append("Chg Overcur L1")
    if f2_msb & 0x02:
        faults.append("Chg Overcur L2")
    if f2_msb & 0x04:
        faults.append("Dischg Overcur L1")
    if f2_msb & 0x08:
        faults.append("Dischg Overcur L2")
    if f2_msb & 0x10:
        faults.append("SOC High L1")
    if f2_msb & 0x20:
        faults.append("SOC High L2")
    if f2_msb & 0x40:
        faults.append("SOC Low L1")
    if f2_msb & 0x80:
        faults.append("SOC Low L2")

    if f2_lsb & 0x01:
        faults.append("Diff V High L1")
    if f2_lsb & 0x02:
        faults.append("Diff V High L2")
    if f2_lsb & 0x04:
        faults.append("Diff Temp High L1")
    if f2_lsb & 0x08:
        faults.append("Diff Temp High L2")
    if f2_lsb & 0x10:
        faults.append("MOS Temp High L1")
    if f2_lsb & 0x20:
        faults.append("MOS Temp High L2")
    if f2_lsb & 0x40:
        faults.append("Amb Temp High L1")
    if f2_lsb & 0x80:
        faults.append("Amb Temp High L2")

    # Fault 3 - MOS / Hardware
    f3_msb = (f3 >> 8) & 0xFF
    f3_lsb = f3 & 0xFF

    if f3_msb & 0x01:
        faults.append("Chg MOS Temp Warn")
    if f3_msb & 0x02:
        faults.append("Dischg MOS Temp Warn")
    if f3_msb & 0x04:
        faults.append("Chg MOS Sensor Fail")
    if f3_msb & 0x08:
        faults.append("Dischg MOS Sensor Fail")
    if f3_msb & 0x10:
        faults.append("Chg MOS Adhesion")
    if f3_msb & 0x20:
        faults.append("Dischg MOS Adhesion")
    if f3_msb & 0x40:
        faults.append("Chg MOS Open Circ")
    if f3_msb & 0x80:
        faults.append("Dischg MOS Open Circ")

    if f3_lsb & 0x01:
        faults.append("AFE Fail")
    if f3_lsb & 0x02:
        faults.append("Volt Sensor Disconn")
    if f3_lsb & 0x04:
        faults.append("Temp Sensor Fail")
    if f3_lsb & 0x08:
        faults.append("EEPROM Fail")
    if f3_lsb & 0x10:
        faults.append("RTC Fail")
    if f3_lsb & 0x20:
        faults.append("Precharge Fail")
    if f3_lsb & 0x40:
        faults.append("Veh Comm Fail")
    if f3_lsb & 0x80:
        faults.append("Int Net Fail")

    # Fault 4 - Other
    f4_msb = (f4 >> 8) & 0xFF

    if f4_msb & 0x01:
        faults.append("Curr Mod Fail")
    if f4_msb & 0x02:
        faults.append("Press Mod Fail")
    if f4_msb & 0x04:
        faults.append("Short Circ")
    if f4_msb & 0x08:
        faults.append("Low V Chg Prohibit")
    if f4_msb & 0x10:
        faults.append("GPS/Switch MOS")
    if f4_msb & 0x20:
        faults.append("Chg Cab Offline")

    return faults
