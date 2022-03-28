from core.audio import device_index_to_device, host_api_index_to_name

print("APIs:")
for api_index, api_name in host_api_index_to_name.items():
    print(f"  {api_index}. {api_name}")

print()
print("-" * 20)
print()

print("DEVICES:")
for device_index, device in device_index_to_device.items():
    print(f"  {device_index}. \"{device.name}\" "
          f"(API = {device.host_api.name}, Sample Rate = {device.default_sample_rate})")
