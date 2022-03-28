from pyaudio import PyAudio

p = PyAudio()

api_index_to_name: dict[int, str] = {}

print("-" * 20)
print("APIs:")
api_count: int = p.get_host_api_count()
for api_index in range(api_count):
    api_info: dict = p.get_host_api_info_by_index(api_index)

    api_name: str = api_info.get("name")
    if api_name is None:
        continue

    print(f"{api_index}. {api_name}")
    print(api_info)

    api_index_to_name[api_index] = api_name


print()
print("-" * 20)
print()

print("DEVICES:")
devices_count: int = p.get_device_count()
for device_index in range(devices_count):
    device_info: dict = p.get_device_info_by_index(device_index)

    device_name: str = device_info.get("name")
    device_sample_rate: float = device_info.get("defaultSampleRate", 0)
    device_host_api_index: int = device_info.get("hostApi", -1)

    device_host_api_name: str = api_index_to_name[device_host_api_index]

    print(f"Device {device_index}: {device_name}\n"
          f"  Sample Rate = {device_sample_rate}, API = {device_host_api_name}")
    print(device_info)
