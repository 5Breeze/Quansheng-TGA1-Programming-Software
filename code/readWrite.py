import serial
import math
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

# CTCSS标准码
CTCSS_CODES = [
    67.0, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8,
    97.4, 100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8,
    136.5, 141.3, 146.2, 151.4, 156.7, 162.2, 167.9, 173.8, 179.9, 186.2,
    192.8, 203.5, 210.7, 218.1, 225.7, 233.6, 241.8, 250.3, 3000
]
nummmm=0;
# 处理配置信息
def process_config_data(data):
    global nummmm;
    nummmm = nummmm +1;
    recv_freq_hex = data[4:7][::-1].hex().upper()
    recv_freq_dec = (int(recv_freq_hex, 16) - 6445568) / 10**5 + 400
    
    send_freq_hex = data[8:11][::-1].hex().upper()
    send_freq_dec = (int(send_freq_hex, 16) - 6445568) / 10**5 + 400
    
    recv_cts_temp_2 = int.from_bytes(data[12:13], byteorder='big')
    recv_cts_temp_1 = int.from_bytes(data[13:14], byteorder='big')
    recv_cts = (recv_cts_temp_2 % 16 + math.floor(recv_cts_temp_2/16) * 10 + (recv_cts_temp_1 % 16) * 100 +  math.floor(recv_cts_temp_1/16) * 1000)/10
    
    send_cts_temp_2 = int.from_bytes(data[14:15], byteorder='big')
    send_cts_temp_1 = int.from_bytes(data[15:16], byteorder='big')
    send_cts = (send_cts_temp_2 % 16 + math.floor(send_cts_temp_2/16) * 10 + (send_cts_temp_1 % 16) * 100 +  math.floor(send_cts_temp_1/16) * 1000)/10
    
    
    control_byte = data[16]
    if control_byte == 0xEA:
        busy_lock, encryption, frequency_hop =1,0,0
    elif control_byte == 0x6A:
        busy_lock, encryption, frequency_hop =1,0,1
    elif control_byte == 0x4B:
        busy_lock, encryption, frequency_hop =0,1,1
    elif control_byte == 0xEB:
        busy_lock, encryption, frequency_hop =0,0,0
    elif control_byte == 0x6B:
        busy_lock, encryption, frequency_hop =0,0,1
    else:
        busy_lock, encryption, frequency_hop =0,1,0
    
    return {
        'recv_freq': recv_freq_dec,
        'send_freq': send_freq_dec,
        'recv_cts': recv_cts,
        'send_cts': send_cts,
        'busy_lock': busy_lock,
        'encryption': encryption,
        'frequency_hop': frequency_hop
    }

# 生成配置数据
def generate_configuration(user_input):
    config_data = []
    array = [0xEB, 0x6B, 0xCB, 0x4B, 0xEA, 0x6A]
    for i, channel in enumerate(user_input):
        recv_freq = int((channel['recv_freq'] - 400) * 10**5 + 6445568)
        recv_freq_hex = recv_freq.to_bytes(3, byteorder='big')[::-1]

        send_freq = int((channel['send_freq'] - 400) * 10**5 + 6445568)
        send_freq_hex = send_freq.to_bytes(3, byteorder='big')[::-1]

        recv_cts_integer = int(channel['recv_ctcss'] * 10)
        if recv_cts_integer>3000:
            recv_ctcss_hex=bytes([0xFF, 0xFF])
        else:
            # 计算接收 CTS 值的字节序列
            recv_cts_temp_1 = recv_cts_integer // 100
            recv_cts_temp_2 = recv_cts_integer % 100
            recv_ctcss_hex_1 = recv_cts_temp_1%10+math.floor(recv_cts_temp_1/10)*16
            recv_ctcss_hex_2 = recv_cts_temp_2%10+math.floor(recv_cts_temp_2/10)*16
            recv_ctcss_hex = bytes([recv_ctcss_hex_2,recv_ctcss_hex_1])

        send_cts_integer = int(channel['send_ctcss'] * 10)
        if send_cts_integer>1000:
            send_ctcss_hex=bytes([0xFF, 0xFF])
        else:
            # 计算接收 CTS 值的字节序列
            send_cts_temp_1 = send_cts_integer // 100
            send_cts_temp_2 = send_cts_integer % 100
            send_ctcss_hex_1 = send_cts_temp_1%10+math.floor(send_cts_temp_1/10)*16
            send_ctcss_hex_2 = send_cts_temp_2%10+math.floor(send_cts_temp_2/10)*16
            send_ctcss_hex = bytes([send_ctcss_hex_2,send_ctcss_hex_1])

        # 假设 channel 是一个字典，包含 'busy_lock'、'encryption' 和 'frequency_hop'
        busy_lock = int(channel['busy_lock'])
        encryption = int(channel['encryption'])
        frequency_hop = int(channel['frequency_hop'])
        
        # 将它们组合成一个三位的整数
        control_byte = (busy_lock << 2) | (encryption << 1) | frequency_hop

        # control_byte = ((int(channel['busy_lock']) << 2) |(int(channel['encryption']) < 1) |int(channel['frequency_hop']))
        config_data.append(
            b'\x57\x00' + bytes([i*13]) + b'\x0D' + recv_freq_hex + b'\x02' +
            send_freq_hex + b'\x02' + recv_ctcss_hex + send_ctcss_hex + bytes([array[control_byte]]))
    
    return config_data

# 写入配置
def write_configuration(ser, config_data):
    for i, config in enumerate(config_data):
        send_data(ser, config)
        response = receive_data(ser, 1)
        if response != b'\x06':
            debug_print(f"Failed to write configuration for index {i}: {response.hex().upper()}")
            messagebox.showerror("Error", f"Failed to write configuration for index {i}")
            return False
    return True

# 读取配置
def read_configuration(ser):
    global config_data_global
    config_data = []
    index = 0x00  # 起始序号

    for i in range(18):
        send_data(ser, bytes([0x52, 0x00, index, 0x0D]))  # 发送52 00 xx 0D
        response = receive_data(ser, 17)
        config_data_global.append(response)
        if response.startswith(b'\x57\x00'):
            config_data.append(process_config_data(response))
        else:
            debug_print(f"Unexpected response for index {index}: {response.hex().upper()}")
            return None
        
        index += 13  # 每次序号增加13

    return config_data

# UI相关函数
def update_ui(config_data):


    for i, data in enumerate(config_data):
        recv_freq_vars[i].set(f"{data['recv_freq']:.3f}")
        send_freq_vars[i].set(f"{data['send_freq']:.3f}")
        recv_ctcss_vars[i].set(f"{data['recv_cts']:.1f}")
        send_ctcss_vars[i].set(f"{data['send_cts']:.1f}")
        busy_vars[i].set(data['busy_lock'])
        encryption_vars[i].set(data['encryption'])
        freq_hop_vars[i].set(data['frequency_hop'])
        if i == 15:
            break
config_data_global=[]
def start_reading():
    global config_data_global
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
                    
                    if config_data:
                        update_ui(config_data)
                    else:
                        messagebox.showerror("Error", "Failed to read configuration data")
                else:
                    messagebox.showerror("Error", "Failed during final handshake")
            else:
                messagebox.showerror("Error", "Unexpected response after sending 0x05")
        else:
            messagebox.showerror("Error", "Failed after sending 0x06")
    else:
        messagebox.showerror("Error", "Failed during initial data exchange")
    
    ser.close()

def start_writing():
    global config_data_global
    port = port_combobox.get()
    if not port:
        messagebox.showerror("Error", "Please select a serial port")
        return
    
    ser = open_serial(port)
    if not ser:
        messagebox.showerror("Error", "Failed to open serial port")
        return

    # 生成用户配置数据
    user_input = []
    for i in range(16):
        user_input.append({
            'recv_freq': float(recv_freq_vars[i].get()),
            'send_freq': float(send_freq_vars[i].get()),
            'recv_ctcss': float(recv_ctcss_vars[i].get()),
            'send_ctcss': float(send_ctcss_vars[i].get()),
            'busy_lock': busy_vars[i].get(),
            'encryption': encryption_vars[i].get(),
            'frequency_hop': freq_hop_vars[i].get()
        })
    
    generated_config = generate_configuration(user_input)

    # 用读取到的最后两条数据替换生成配置中的占位符
    generated_config.append(config_data_global[-2])
    generated_config.append(config_data_global[-1])

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
                    # 写入配置
                    if write_configuration(ser, generated_config):
                         messagebox.showinfo("Success", "Configuration written successfully")
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
root.title("Configuration Reader and Writer")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

port_label = tk.Label(frame, text="Select Serial Port:")
port_label.grid(row=0, column=0, columnspan=2)

# 串口选择下拉列表
port_combobox = ttk.Combobox(frame, values=get_serial_ports())
port_combobox.grid(row=0, column=2, columnspan=2)

read_button = tk.Button(frame, text="Read Configuration", command=start_reading)
read_button.grid(row=0, column=4)

write_button = tk.Button(frame, text="Write Configuration", command=start_writing)
write_button.grid(row=0, column=5)

# 列标签
labels = ["Channel", "Recv Frequency (MHz)", "Recv CTCSS", "Send Frequency (MHz)", "Send CTCSS", "Busy Lock", "Encryption", "Freq Hop"]
for col, text in enumerate(labels):
    tk.Label(frame, text=text).grid(row=1, column=col)

# 输入框和下拉菜单变量
recv_freq_vars = []
send_freq_vars = []
recv_ctcss_vars = []
send_ctcss_vars = []
busy_vars = []
encryption_vars = []
freq_hop_vars = []

# 为16个信道生成输入框
for i in range(16):
    tk.Label(frame, text=f"Channel {i+1}").grid(row=i+2, column=0)

    recv_freq_var = tk.StringVar(value="400.000")
    recv_freq_vars.append(recv_freq_var)
    tk.Entry(frame, textvariable=recv_freq_var).grid(row=i+2, column=1)

    recv_ctcss_var = tk.StringVar(value=str(CTCSS_CODES[0]))
    recv_ctcss_vars.append(recv_ctcss_var)
    recv_ctcss_menu = ttk.Combobox(frame, values=CTCSS_CODES, textvariable=recv_ctcss_var)
    recv_ctcss_menu.grid(row=i+2, column=2)

    send_freq_var = tk.StringVar(value="400.000")
    send_freq_vars.append(send_freq_var)
    tk.Entry(frame, textvariable=send_freq_var).grid(row=i+2, column=3)

    send_ctcss_var = tk.StringVar(value=str(CTCSS_CODES[0]))
    send_ctcss_vars.append(send_ctcss_var)
    send_ctcss_menu = ttk.Combobox(frame, values=CTCSS_CODES, textvariable=send_ctcss_var)
    send_ctcss_menu.grid(row=i+2, column=4)

    busy_var = tk.StringVar(value="0")
    busy_vars.append(busy_var)
    tk.Checkbutton(frame, text="Busy Lock", variable=busy_var, onvalue="1", offvalue="0").grid(row=i+2, column=5)

    encryption_var = tk.StringVar(value="0")
    encryption_vars.append(encryption_var)
    tk.Checkbutton(frame, text="Encryption", variable=encryption_var, onvalue="1", offvalue="0").grid(row=i+2, column=6)

    freq_hop_var = tk.StringVar(value="0")
    freq_hop_vars.append(freq_hop_var)
    tk.Checkbutton(frame, text="Freq Hop", variable=freq_hop_var, onvalue="1", offvalue="0").grid(row=i+2, column=7)

root.mainloop()
