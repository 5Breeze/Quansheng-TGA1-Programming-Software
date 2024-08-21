import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import messagebox, ttk

# 调试开关
DEBUG = True

def debug_print(message):
    if DEBUG:
        print(message)

# 获取可用的串口列表
def get_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# 串口通信相关函数
def open_serial(port, baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        debug_print(f"Opened serial port {port} at baudrate {baudrate}")
        return ser
    except Exception as e:
        debug_print(f"Failed to open serial port {port}: {e}")
        return None

def send_data(ser, data):
    debug_print(f"Sending data: {data.hex().upper()}")
    ser.write(data)

def receive_data(ser, length):
    data = ser.read(length)
    debug_print(f"Received data: {data.hex().upper()}")
    return data

def process_config_data(data, index):
    # 将数据按规则解析为频率和功能控制数据
    try:
        recv_freq_hex = data[4:7][::-1].hex().upper()
        recv_freq_dec = (int(recv_freq_hex, 16) - 6445568) / 10**5 + 400
        
        send_freq_hex = data[8:11][::-1].hex().upper()
        send_freq_dec = (int(send_freq_hex, 16) - 6445568) / 10**5 + 400
        
        recv_cts = int.from_bytes(data[12:14][::-1], byteorder='big') / 10
        send_cts = int.from_bytes(data[14:16][::-1], byteorder='big') / 10
        
        control_byte = data[16]
        control_bits = f"{control_byte:08b}"[-3:]  # 取后三位
        busy_lock, encryption, frequency_hop = control_bits
        
        return {
            'index': index,
            'recv_freq': recv_freq_dec,
            'send_freq': send_freq_dec,
            'recv_cts': recv_cts,
            'send_cts': send_cts,
            'busy_lock': busy_lock,
            'encryption': encryption,
            'frequency_hop': frequency_hop
        }
    except Exception as e:
        debug_print(f"Failed to process configuration data: {e}")
        return None

def read_configuration(ser):
    config_data = []
    index = 0x00  # 起始序号

    for i in range(18):
        send_data(ser, bytes([0x52, 0x00, index, 0x0D]))  # 发送52 00 xx 0D
        response = receive_data(ser, 17)
        if response.startswith(b'\x57\x00'):
            config_data.append(process_config_data(response, index))
        else:
            debug_print(f"Unexpected response for index {index}: {response.hex().upper()}")
        index += 0x0D  # 每次序号增加13

    return config_data

# UI相关函数
def update_ui(config_data):
    for i, data in enumerate(config_data):
        label = tk.Label(frame, text=f"Channel {i+1}: {data}")
        label.pack()

def start_reading():
    port = port_combobox.get()
    if not port:
        messagebox.showerror("Error", "Please select a serial port")
        return
    
    ser = open_serial(port)
    if not ser:
        messagebox.showerror("Error", "Failed to open serial port")
        return
    
    # 开始数据交互
    send_data(ser, b'\x02\x54\x47\x53\x31\x52\x41\x4D')
    response = receive_data(ser, 1)
    
    if response != b'\x06':
        send_data(ser, b'\x02\x54\x47\x53\x31\x52\x41\x4D')
        response = receive_data(ser, 1)
        if response != b'\x06':
            messagebox.showerror("Error", "Failed to communicate with the device")
            return
    
    send_data(ser, b'\x02')
    response = receive_data(ser, 8)
    
    if response == b'\x06\x00\x00\x00\x00\x00\x00\x00':
        send_data(ser, b'\x06')
        response = receive_data(ser, 1)
        
        if response == b'\x06':
            send_data(ser, b'\x05')
            response = receive_data(ser, 7)
            
            if response:
                send_data(ser, b'\x06')
                response = receive_data(ser, 1)
                
                if response == b'\x06':
                    config_data = read_configuration(ser)
                    update_ui(config_data)
                else:
                    messagebox.showerror("Error", "Failed during final handshake")
            else:
                messagebox.showerror("Error", "Unexpected response after sending 0x05")
        else:
            messagebox.showerror("Error", "Failed after sending 0x06")
    else:
        messagebox.showerror("Error", "Failed during initial data exchange")
    
    ser.close()

# 创建UI
root = tk.Tk()
root.title("Configuration Reader")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

port_label = tk.Label(frame, text="Select Serial Port:")
port_label.pack(side=tk.LEFT)

# 串口选择下拉列表
port_combobox = ttk.Combobox(frame, values=get_serial_ports())
port_combobox.pack(side=tk.LEFT)

start_button = tk.Button(frame, text="Start Reading", command=start_reading)
start_button.pack(side=tk.LEFT)

root.mainloop()
