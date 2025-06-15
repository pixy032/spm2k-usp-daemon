import logging
import os
import subprocess
import time

import serial

logPath = '\\ups'
logFile = logPath + '\\ups_daemon.log'
if not os.path.exists(logPath) or not os.path.isdir(logPath):
    os.mkdir(logPath, 0o777)
logging.basicConfig(filename=logFile, level=logging.INFO, format='[%(asctime)s] %(message)s')

logging.info('UPS Daemon is running...')
port = 'COM3'
ser = serial.Serial(
    port=port,  # 串口名称
    baudrate=2400,  # 波特率
    bytesize=serial.EIGHTBITS,  # 8位数据位
    stopbits=serial.STOPBITS_ONE,  # 1位停止位
    parity=serial.PARITY_NONE,  # 无奇偶校验
    timeout=2,  # 超时设置（秒）
    xonxoff=False,  # 软件流控（关闭）
    rtscts=False,  # 硬件流控（关闭）
    dsrdtr=False  # 硬件流控（关闭）
)

counter = 1
linuxCmd = ['shutdown', '-h', '+0.1']
winCmd = ['shutdown', '-s', '-t', '5']
code = 'ascii'
y = 'Y'.encode(code)
q = 'Q'.encode(code)
r = 'R'.encode(code)

while True:
    time.sleep(5)
    initOnOff = False
    try:
        ser.write(y)
        time.sleep(1)
        sm = ser.read(16)
        if not sm:
            initOnOff = True
            logging.warning('Set UPS to Smart Mode Fail')
            continue
        smStr = sm.decode(code).replace('\r', '').replace('\n', '')
        if smStr.find('SM') == -1:
            logging.warning('Set UPS to Smart Mode Fail')
            continue
        #
        ser.write(q)
        time.sleep(1)
        rep = ser.read(16)
        if not rep:
            logging.warning('UPS Response is none...')
            continue
        status = rep[0]
        logging.info(f'UPS Status: {status:08b}')
        repStr = rep.decode(code).replace('\r', '').replace('\n', '')
        if smStr.find('!') != -1 or repStr.find('!') != -1:
            logging.warning(f'UPS is Unstable times {counter}')
            counter += 1
        else:
            logging.info(f'UPS is Unstable times Recover {counter}')
            counter = 0
        #
        if counter >= 4:
            logging.warning(f'Ups : {winCmd}')
            subprocess.call(winCmd)
            break
    except Exception as e:
        logging.error(f'Ups Daemon error : {e}')
        break
    finally:
        try:
            if not initOnOff:
                ser.write(r)
                time.sleep(1)
                bye = ser.read(16)
                if not bye:
                    logging.warning('Return to Simple Mode is Fail')
                byeStr = bye.decode(code).replace('\r', '').replace('\n', '')
                logging.info(f'Return to Simple Mode {byeStr}')
        except Exception as e:
            pass
if ser.is_open:
    ser.close()
    logging.info('UPS Daemon is End Computer Shutdown')

# onLine = ''
# onBattery = ''
# 00110001 00110001 00110001 10 off b'10\r\n'
# 00110000 00001101 00110000 08 on b'08\r\n'
