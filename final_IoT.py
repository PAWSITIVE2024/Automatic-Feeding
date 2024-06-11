import os
from gpiozero import Motor
from smbus2 import SMBus
from time import sleep
import sys
import firebase_admin
from firebase_admin import credentials, db
import urllib.request

class Final():
    def __init__(self, user_id):
        # 모터설정
        self.dc_motor = Motor(forward=20, backward=21) #pin 38,40
        # Initialize I2C
        self.bus_number = 1  
        self.bus = SMBus(bus_number)
        self.arduino_address = 0x08 #pin 3-a4, pin5-a5, gnd-gnd
        
        self.user_id = user_id
        self.cred = credentials.Certificate('library/doggy-dine-firebase-adminsdk-6tcsx-e66d564d1b.json')
        firebase_admin.initialize_app(self.cred, {'databaseURL' : "https://doggy-dine-default-rtdb.firebaseio.com/"})
        self.doggydine_ref = db.reference('/DoggyDine/UserAccount')
        self.Done = False
        self.target_weight = None

    def rotate_motor_forward(self):
        self.dc_motor.forward(speed=1) #5초간 닫힘
        sleep(5)
        self.dc_motor.stop()

    def rotate_motor_backward(self):
        self.dc_motor.backward(speed=1)#5초간 열림
        sleep(5)
        self.dc_motor.stop()

    def read_weight_from_sensor(self): #아두이노로부터 무게값 받아옴
        try:
            data = self.bus.read_i2c_block_data(arduino_address, 0, 4)
            weight = int.from_bytes(data, byteorder='little', signed=True)
            return weight / 100.0  
        except IOError:
            print("I/O error occurred")
            return None

    def clean_and_exit(self):
        self.dc_motor.close()
        sys.exit()


    def get_target(self):
        target = self.doggydine_ref.child(self.user_id + '/Detected/Target_weight')
        self.target_weight = target.get()
        self.rotate_motor_backward()

    def run(self):

        self.get_target()
        
        try:
            while True:
                actual_weight = self.read_weight_from_sensor()
                print(f"Actual weight: {actual_weight} grams")
                
                if self.target_weight is not None and actual_weight > self.target_weight:
                    self.rotate_motor_forward()
                
                sleep(1)  # 1초마다 무게 값 갱신
        except KeyboardInterrupt:
            self.clean_and_exit()
        except Exception as e:
            print(f"An error occurred: {e}")
            self.clean_and_exit()


def main():
    run = Final(user_id)
    run.run()

if __name__ == '__main__':
    main()
