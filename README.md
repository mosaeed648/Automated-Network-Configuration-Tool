# Automated Network Configuration Tool

## Description

The Automated Network Configuration Tool is a powerful Python-based utility designed to streamline the process of configuring multiple network devices simultaneously. It leverages SSH connections to apply standardized configurations across various network devices such as routers and switches, significantly reducing the time and potential for human error in network management tasks.

## Features

- Multi-device configuration using YAML-based device information
- Jinja2 templating for flexible configuration generation
- Parallel execution for efficient configuration of multiple devices
- Configuration backup before applying changes
- Configuration diff to show proposed changes
- Device discovery using ARP
- Dockerized for easy deployment and consistency across environments

## Prerequisites

- Python 3.7+
- Docker (for containerized deployment)

## Installation

1. Clone the repository:
   ```
   https://github.com/mosaeed648/Automated-Network-Configuration-Tool.git
   cd Automated-Network-Configuration-Tool
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running Locally

1. Prepare your `devices.yaml` file with the list of devices to configure.
2. Create your `config_template.j2` file with the Jinja2 template for your configurations.
3. Run the tool:
   ```
   python network_config_tool.py --devices devices.yaml --template config_template.j2 --backup-dir ./backups
   ```

### Running with Docker

1. Build the Docker image:
   ```
   docker build -t network-config-tool .
   ```

2. Run the Docker container:
   ```
   docker run -it --network host -v $(pwd)/backups:/app/backups network-config-tool --devices devices.yaml --template config_template.j2 --backup-dir /app/backups
   ```

3. For device discovery (requires additional privileges):
   ```
   docker run -it --network host --cap-add=NET_RAW --cap-add=NET_ADMIN -v $(pwd)/backups:/app/backups network-config-tool --devices devices.yaml --template config_template.j2 --backup-dir /app/backups --discover 192.168.1.0/24
   ```

## Main Functions

### `class NetworkDevice`
Represents a network device and handles connections, command execution, and configuration management.

- `connect()`: Establishes a connection to the device using Netmiko.
- `send_command(command)`: Sends a single command to the device and returns the output.
- `send_config_set(config)`: Sends a list of configuration commands to the device.
- `get_config()`: Retrieves the current running configuration of the device.
- `close()`: Closes the connection to the device.

### `load_devices(filename)`
Loads device information from a YAML file.

### `load_template(filename)`
Loads a Jinja2 template from a file.

### `render_config(template, device)`
Renders the configuration template for a specific device.

### `backup_config(device, backup_dir)`
Creates a backup of the current device configuration.

### `configure_device(device_info, template, backup_dir)`
Configures a single device using the provided template, including backup and diff operations.

### `configure_devices_parallel(devices, template, backup_dir, max_workers)`
Configures multiple devices in parallel using ThreadPoolExecutor.

### `discover_devices(network)`
Discovers active devices in the given network using ARP.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Netmiko](https://github.com/ktbyers/netmiko) for handling network device connections
- [Jinja2](https://jinja.palletsprojects.com/) for templating
- [Scapy](https://scapy.net/) for network discovery capabilities
