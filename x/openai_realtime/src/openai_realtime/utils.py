import base64
import numpy as np

class RealtimeUtils:
    @staticmethod
    def float_to_16bit_pcm(float32_array):
        int16_array = (np.clip(float32_array, -1, 1) * 32767).astype(np.int16)
        return int16_array.tobytes()

    @staticmethod
    def base64_to_array_buffer(base64_string):
        return base64.b64decode(base64_string)

    @staticmethod
    def array_buffer_to_base64(array_buffer):
        if isinstance(array_buffer, np.ndarray):
            if array_buffer.dtype == np.float32:
                array_buffer = RealtimeUtils.float_to_16bit_pcm(array_buffer)
            elif array_buffer.dtype == np.int16:
                array_buffer = array_buffer.tobytes()
        return base64.b64encode(array_buffer).decode('utf-8')

    @staticmethod
    def merge_int16_arrays(left, right):
        if isinstance(left, bytes):
            left = np.frombuffer(left, dtype=np.int16)
        if isinstance(right, bytes):
            right = np.frombuffer(right, dtype=np.int16)
        if not isinstance(left, np.ndarray) or not isinstance(right, np.ndarray):
            raise ValueError("Both items must be numpy arrays or bytes objects")
        return np.concatenate((left, right))

    @staticmethod
    def generate_id(prefix, length=21):
        import random
        chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        return prefix + ''.join(random.choice(chars) for _ in range(length - len(prefix)))