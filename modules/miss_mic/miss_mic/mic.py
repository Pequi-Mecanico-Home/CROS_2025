import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray
import pyaudio
import numpy as np
import audioop
import sounddevice

class MicrophonePublisher(Node):
    def __init__(self):

        super().__init__('microphone_publisher')

        self.publisher_ = self.create_publisher(Int16MultiArray, 'microphone_data', 10)
        timer_period = 0.08  # seconds

        self.timer_ = self.create_timer(timer_period, self.publish_microphone_data)

        # Declara o parâmetro 'device' com um valor padrão de -1 (indicando que não foi passado)

        self.declare_parameter('device', -1)
        self.input_device = self.get_parameter('device').get_parameter_value().integer_value

        if self.input_device == -1:
            # Se o parâmetro não foi passado, definir um valor padrão
            # input_device_specs = sounddevice.query_devices(device='USB Audio Device')
            input_device_specs = sounddevice.query_devices(device='logitech') 
            self.input_device = input_device_specs['index']
            self.get_logger().info(f"Parâmetro 'device' não passado. Usando dispositivo padrão: '{input_device_specs['name']}'")
        else:
            input_device_specs = sounddevice.query_devices(self.input_device)
            self.get_logger().info(f"Dispositivo de entrada de áudio definido como: '{input_device_specs['name']}'")

        self.audio = pyaudio.PyAudio()
        self.rate = int(self.audio.get_device_info_by_index(self.input_device)['defaultSampleRate'])
        print(f"rate: {self.rate}")
        # Get microphone stream
        self.format = pyaudio.paInt16
        self.channels = 1
        self.target_rate = 16000
        self.chunk = 1280
        self.p = pyaudio.PyAudio()
        self.cvstate = None

        self.mic_stream = self.p.open(format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk, input_device_index=self.input_device)

        self.get_logger().info(f"Recording ...")

    def publish_microphone_data(self):

        # Get microphone data from the specified device
        data = self.mic_stream.read(self.chunk, exception_on_overflow=False)
        data, self.cvstate = audioop.ratecv(data, 2, self.channels, self.rate, self.target_rate, self.cvstate)
        data = np.frombuffer(data, dtype=np.int16)
        print(self.cvstate)
        print(f"Amplitude média: {np.mean(np.abs(data))}")  
        print('-'*30)
        # self.get_logger().info(f'shape: {data.shape}')
        # Create and publish AudioData message
        audio_msg = Int16MultiArray()
        audio_msg.data = data.tolist()
        self.publisher_.publish(audio_msg)

    def list_devices(self):
        self.get_logger().info("Dispositivos de entrada (microfones):")
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:
                self.get_logger().info(f"ID: {device_info['index']}, Nome: {device_info['name']}")
                return_id = device_info['index']
        return return_id


def main(args=None):
    rclpy.init(args=args)
    microphone_publisher = MicrophonePublisher()
    try: 
        rclpy.spin(microphone_publisher)
    except KeyboardInterrupt:
        microphone_publisher.get_logger().info(f"Audio stream closed.")
        microphone_publisher.mic_stream.stop_stream()
        microphone_publisher.mic_stream.close()
        microphone_publisher.p.terminate() 
    finally:
        microphone_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
