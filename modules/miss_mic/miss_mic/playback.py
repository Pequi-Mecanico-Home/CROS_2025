import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray
import numpy as np
import sounddevice as sd
import pyaudio


class Playback(Node):

    def __init__(self):
        self.data = None
        super().__init__('mic_playback')

        self.subscription = self.create_subscription(
            Int16MultiArray,
            'microphone_data',
            self.detector_callback,
            10
        )

        self.output_device = 5

        # Get microphone stream
        format = pyaudio.paInt16
        channels = 1
        self.rate = 16000
        self.chunk = 1280
        self.p = pyaudio.PyAudio()
        id_2 = self.list_devices()
        try:
            self.out_stream = self.p.open(format=format, channels=channels, rate=self.rate, output=True, frames_per_buffer=self.chunk, output_device_index=self.output_device)
        except:
            self.get_logger().info(f"Device {self.output_device} not found. Using default device: {id_2}")
            self.out_stream = self.p.open(format=format, channels=channels, rate=self.rate, output=True, frames_per_buffer=self.chunk, output_device_index=id_2)

        self.get_logger().info(f"Streaming ...")

    def detector_callback(self, msg):


        data =  np.array(msg.data)
        self.out_stream.write(data.tobytes())

    def list_devices(self):
        # Listar os dispositivos de saída (alto-falantes)
        self.get_logger().info("\nDispositivos de saída (alto-falantes):")
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if device_info["maxOutputChannels"] > 0:
                 self.get_logger().info(f"ID: {device_info['index']}, Nome: {device_info['name']}")
                 return_id = device_info['index']

        return return_id

def main(args=None):

    rclpy.init(args=args)
    playback = Playback()
    try: 
        rclpy.spin(playback)
    except KeyboardInterrupt:
        playback.get_logger().info(f"Playback stop.")
        playback.out_stream.stop_stream()
        playback.out_stream.close()
        playback.p.terminate() 
    finally:
        playback.destroy_node()
        rclpy.shutdown()
    



if __name__ == '__main__':
    main()
