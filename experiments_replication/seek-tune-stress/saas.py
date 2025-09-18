import json
import os
from locust import HttpUser, task, constant_throughput
from locust.exception import StopUser

class AudioRecognitionUser(HttpUser):
    wait_time = constant_throughput(1)
    
    # JSON payload file path
    json_file_path = "/tmp/seek-tune-stress/audio.json"
    
    # Class-level variable to store the shared payload
    _shared_payload = None
    _payload_loaded = False
    _payload_load_error = None

    @classmethod
    def load_shared_payload(cls):
        """
        Class method to load the payload once before any user starts
        """
        if cls._payload_loaded:
            return
            
        
        try:
            with open(cls.json_file_path, 'r') as file:
                cls._shared_payload = json.load(file)
            cls._payload_loaded = True
        except Exception as e:
            cls._payload_load_error = str(e)
            raise
    
    def on_start(self):
        """
        Verify payload is loaded when the user starts
        """
        if not self._payload_loaded and self._payload_load_error:
            raise StopUser(f"Failed to load JSON payload: {self._payload_load_error}")
            
        if not self._payload_loaded:
            try:
                self.load_shared_payload()
            except Exception as e:
                raise StopUser(f"Failed to load JSON payload: {str(e)}")
    
    @task
    def recognize_audio(self):
        """
        Send the POST request with the heavy JSON payload
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        self.client.post(
            "/api/audioRecognize",
            json=self._shared_payload,
            headers=headers
        )