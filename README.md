# Audiophage <sub>*a Discord microphone bot*</sub>

![Python 3.10](https://img.shields.io/badge/python-3.10-4584b6 "Python 3.10")
![discord.py @ e515378](https://img.shields.io/badge/discord.py-e515378-99aab5 "discord.py e515378")

#### What does it do?
Audiophage is a Discord bot **capable of streaming your microphone** (or any audio input on your computer) directly to 
a voice channel of your choice and configuration. This allows you to effectively have a standalone audio stream without 
Discord installed or two audio streams running simultaneously (one Audiophage + one desktop client).

---

## 1. Installation
To run this bot either directly or to package it into a standalone archive, you'll need the following tools:
- [Python 3.10](https://www.python.org/)
- [Poetry](https://python-poetry.org/) (Python package and virtual environment manager)

With those two tools installed, clone the repository, move into it in a terminal and execute `poetry install`.
This will create a local Python environment so your main Python installation stays clean.
If Poetry is unable to find the right Python installation (can happen if your Python binaries are unusually named), 
first run `poetry env use python3.10` (this should create the `.venv` directory properly) and then run `poetry install` again.

> ##### NOTE
> This project uses the Poetry virtual environment manager, so make sure you're 
> [using the virtual Python environment properly](https://python-poetry.org/docs/basic-usage/#using-your-virtual-environment).
> This generally means either [activating it in your shell](https://python-poetry.org/docs/basic-usage/#activating-the-virtual-environment) 
> or using the `poetry run python ...` command. When `python stream.py` / `pyinstaller ...` or similar commands are written below, 
> is it assumed your Python virtual environment is active.


### 1.1. Packaging into a standalone archive
This project is configured to use [PyInstaller](https://pyinstaller.readthedocs.io/en/stable/) as the packager.
Packaging Audiophage in this way will create a relatively small folder in `dist` that can be compressed and distributed to
any computer you wish to run the bot on, but where you don't want to bother with installing Python and Poetry.

To package the bot, make sure to follow the installation steps in `1. Installation` and then execute `./package-audiophage.ps1` 
or the OS-agnostic equivalent:
```shell
pyinstaller audiophage.spec -y
```

If you encounter errors while packaging (Python 3.10-specific problem), see 
[this PyInstaller issue for a hotfix](https://github.com/pyinstaller/pyinstaller/issues/6301#issuecomment-974927257).


## 2. Configuration
Regardless of whether you're running the bot directly from source or from a package, a small amount of configurration is required.

Inside the `data` directory, copy the `configuration.TEMPLATE.toml` into `configuration.toml` and fill out at least the following values:
- **(required)** obtain your Discord bot token and set it under `discord.token`,
- *(optional)* if you need the auto-join functionality or a *"primary"* voice channel, fill out the `auto_join` table <br> 
  (if you don't, the command `/join primary` will be unavailable and no auto-join will occur when the bot starts - more about commands below),
- **(required)** fill out the `permissions` table, both the `user_ids` list and the `guild_ids` list must have at least one user and guild ID 
  (otherwise no one will be able to control the bot),
- **(required)** run the `list-audio-devices.py` script (or the `list-audio-devices.exe` binary) to get a list of available audio devices;
  pick the one you want to stream and write down its API name (`host_api_name`) and device name (`input_device_name`) inside the `audio` table.
  Make sure the device is an *input* device.

---

## 3. Running
You're ready to start streaming! **To start the bot, run**
```shell
python stream.py
```
or the `audiophage.exe` binary (if you're using a standalone package from `1.1. Packaging into a standalone archive`).

When the bot is ready to receive commands, you'll see `INFO:audiophage:Logged in as bot [BOT INFO].` in your console.

### 3.1. Slash commands
Audiophage has a small number of commands that allow you to control the stream. Here they are:

| Command                | Description                                                                                                                                  | User has to be whitelisted |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|----------------------------|
| /ping                  | Request a simple pong response from the bot - useful for verifying the bot is running properly.                                              | No                         |
| /join [me/primary]     | Request the bot to join a voice channel and start streaming your microphone (the audio device you configured in step 2).                     | Yes                        |
| /volume [float: 0 - 2] | Change the volume of the audio stream. 0 means muted output, 1 is the original volume and 2 is twice the volume. Can be anywhere in between. | Yes                        |
| /leave                 | Request the bot to stop streaming and leave the current voice channel.                                                                       | Yes                        |
