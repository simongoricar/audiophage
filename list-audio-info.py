from core.audio import device_index_to_device, host_api_index_to_name, PyAudioHostAPI, PyAudioDevice

def separator():
    print()
    print("=" * 20)
    print()

print("This script will query and display available audio APIs and devices on your system.")
print("Use this script to properly configure your configuration.toml file:")
print("  - \"host_api_name\" should match the API name you wish to use (if unsure, use \"Windows WASAPI\"!);")
print("  - \"input_device_name\" should match the exact device name "
      "(the device should be available using the above API).")

separator()

# Group devices by API
devices_by_host_api: dict[PyAudioHostAPI, list[PyAudioDevice]] = {
    api: [] for api in host_api_index_to_name.values()
}
for device in device_index_to_device.values():
    devices_by_host_api[device.host_api].append(device)

devices_by_host_api = {
    k: sorted(v, key=lambda d: d.name) for k, v in devices_by_host_api.items()
}


print("---- Available audio devices, grouped by audio APIs: ----")
for host_api, devices in devices_by_host_api.items():
    print(f"  API: \"{host_api.name}\" (id: {host_api.index}, {host_api.device_count} devices)")
    for device in devices:
        print(f"    \"{device.name}\" (id: {device.index}, sample rate: {device.default_sample_rate})")
    print()

separator()

print("---- END ----")
