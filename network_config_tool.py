import paramiko
import time
import yaml
import jinja2
import logging
import argparse
import netmiko
import difflib
import ipaddress
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from scapy.all import ARP, Ether, srp

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NetworkDevice:
    def __init__(self, hostname: str, username: str, password: str, device_type: str):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.device_type = device_type
        self.connection = None

    def connect(self) -> None:
        """Establish a connection to the device using Netmiko."""
        try:
            self.connection = netmiko.ConnectHandler(
                device_type=f'cisco_{self.device_type}',
                ip=self.hostname,
                username=self.username,
                password=self.password
            )
            logger.info(f"Connected to {self.hostname}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.hostname}. Error: {str(e)}")
            raise

    def send_command(self, command: str) -> str:
        """Send a command to the device and return the output."""
        if not self.connection:
            raise Exception("Not connected to the device")
        return self.connection.send_command(command)

    def send_config_set(self, config: List[str]) -> str:
        """Send a list of configuration commands to the device."""
        if not self.connection:
            raise Exception("Not connected to the device")
        return self.connection.send_config_set(config)

    def get_config(self) -> str:
        """Get the current running configuration of the device."""
        return self.send_command("show running-config")

    def close(self) -> None:
        """Close the connection to the device."""
        if self.connection:
            self.connection.disconnect()
            logger.info(f"Closed connection to {self.hostname}")

def load_devices(filename: str) -> List[Dict[str, Any]]:
    """Load device information from a YAML file."""
    with open(filename, 'r') as file:
        return yaml.safe_load(file)

def load_template(filename: str) -> jinja2.Template:
    """Load a Jinja2 template from a file."""
    with open(filename, 'r') as file:
        return jinja2.Template(file.read())

def render_config(template: jinja2.Template, device: Dict[str, Any]) -> List[str]:
    """Render the configuration template for a specific device."""
    config_str = template.render(device)
    return config_str.split('\n')

def backup_config(device: NetworkDevice, backup_dir: str) -> None:
    """Backup the current configuration of a device."""
    config = device.get_config()
    filename = f"{backup_dir}/{device.hostname}_backup.cfg"
    with open(filename, 'w') as file:
        file.write(config)
    logger.info(f"Backup of {device.hostname} saved to {filename}")

def configure_device(device_info: Dict[str, Any], template: jinja2.Template, backup_dir: str) -> None:
    """Configure a single device using the provided template."""
    device = NetworkDevice(device_info['hostname'], device_info['username'], 
                           device_info['password'], device_info['device_type'])
    try:
        device.connect()
        backup_config(device, backup_dir)
        new_config = render_config(template, device_info)
        current_config = device.get_config().splitlines()
        diff = list(difflib.unified_diff(current_config, new_config, fromfile="Current Config", tofile="New Config", lineterm=""))
        if diff:
            logger.info(f"Configuration changes for {device.hostname}:")
            for line in diff:
                logger.info(line)
            device.send_config_set(new_config)
            logger.info(f"Configuration of {device.hostname} completed successfully")
        else:
            logger.info(f"No configuration changes needed for {device.hostname}")
    except Exception as e:
        logger.error(f"Failed to configure {device.hostname}. Error: {str(e)}")
    finally:
        device.close()

def configure_devices_parallel(devices: List[Dict[str, Any]], template: jinja2.Template, backup_dir: str, max_workers: int = 5) -> None:
    """Configure multiple devices in parallel using ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(configure_device, device, template, backup_dir) for device in devices]
        for future in as_completed(futures):
            future.result()

def discover_devices(network: str) -> List[str]:
    """Discover active devices in the given network using ARP."""
    ip_network = ipaddress.ip_network(network)
    arp = ARP(pdst=str(ip_network))
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp
    result = srp(packet, timeout=3, verbose=0)[0]
    return [received.psrc for sent, received in result]

def main():
    parser = argparse.ArgumentParser(description="Automated Network Configuration Tool")
    parser.add_argument("--devices", help="Path to YAML file containing device information", required=True)
    parser.add_argument("--template", help="Path to Jinja2 template file", required=True)
    parser.add_argument("--backup-dir", help="Directory to store configuration backups", default="./backups")
    parser.add_argument("--discover", help="Discover devices in the given network (e.g., 192.168.1.0/24)", default=None)
    args = parser.parse_args()

    if args.discover:
        discovered_devices = discover_devices(args.discover)
        logger.info(f"Discovered devices: {discovered_devices}")
    
    devices = load_devices(args.devices)
    template = load_template(args.template)
    configure_devices_parallel(devices, template, args.backup_dir)

if __name__ == "__main__":
    main()