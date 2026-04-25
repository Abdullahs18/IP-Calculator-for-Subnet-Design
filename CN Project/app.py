from flask import Flask, request, jsonify, render_template
import ipaddress

app = Flask(__name__)

def get_ip_class(ip_int):
    first_octet = (ip_int >> 24) & 255
    if first_octet < 128:
        return 'A', '1.0.0.0 – 126.255.255.255'
    elif first_octet < 192:
        return 'B', '128.0.0.0 – 191.255.255.255'
    elif first_octet < 224:
        return 'C', '192.0.0.0 – 223.255.255.255'
    elif first_octet < 240:
        return 'D', '224.0.0.0 – 239.255.255.255 (Multicast)'
    else:
        return 'E', '240.0.0.0 – 255.255.255.255 (Reserved)'

def ip_to_binary(ip_str):
    parts = ip_str.split('.')
    return '.'.join(format(int(p), '08b') for p in parts)

def mask_to_binary(mask_str):
    parts = mask_str.split('.')
    return '.'.join(format(int(p), '08b') for p in parts)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        ip_input = data.get('ip', '').strip()
        mask_input = data.get('mask', '').strip()

        if not ip_input or not mask_input:
            return jsonify({'error': 'IP address and mask/prefix are required'}), 400

        # Handle CIDR or dotted mask
        if '/' in ip_input:
            cidr_str = ip_input
        elif mask_input.startswith('/'):
            cidr_str = ip_input + mask_input
        elif '.' in mask_input:
            # Convert dotted mask to prefix
            mask_obj = ipaddress.IPv4Network(f'0.0.0.0/{mask_input}', strict=False)
            cidr_str = f"{ip_input}/{mask_obj.prefixlen}"
        else:
            cidr_str = f"{ip_input}/{mask_input}"

        network = ipaddress.IPv4Network(cidr_str, strict=False)
        ip_obj = ipaddress.IPv4Address(ip_input.split('/')[0])

        usable = max(0, network.num_addresses - 2)
        if usable > 0:
            first_host = str(network.network_address + 1)
            last_host = str(network.broadcast_address - 1)
        else:
            first_host = str(network.network_address)
            last_host = str(network.broadcast_address)

        ip_int = int(ip_obj)
        ip_class, class_range = get_ip_class(ip_int)
        is_private = ip_obj.is_private

        wildcard = ipaddress.IPv4Address(int(network.hostmask))

        result = {
            'ip': str(ip_obj),
            'cidr': network.prefixlen,
            'network_address': str(network.network_address),
            'broadcast_address': str(network.broadcast_address),
            'subnet_mask': str(network.netmask),
            'wildcard_mask': str(wildcard),
            'first_host': first_host,
            'last_host': last_host,
            'total_hosts': network.num_addresses,
            'usable_hosts': usable,
            'ip_class': ip_class,
            'class_range': class_range,
            'is_private': is_private,
            'ip_binary': ip_to_binary(str(ip_obj)),
            'mask_binary': mask_to_binary(str(network.netmask)),
            'network_binary': ip_to_binary(str(network.network_address)),
            'wildcard_binary': ip_to_binary(str(wildcard)),
        }
        return jsonify(result)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400


@app.route('/vlsm', methods=['POST'])
def vlsm():
    try:
        data = request.get_json()
        base_network = data.get('network', '').strip()
        host_counts = data.get('hosts', [])

        if not base_network:
            return jsonify({'error': 'Base network is required'}), 400
        if not host_counts:
            return jsonify({'error': 'At least one subnet host count is required'}), 400

        host_counts = [int(h) for h in host_counts if str(h).strip()]
        if any(h < 1 for h in host_counts):
            return jsonify({'error': 'Host counts must be positive integers'}), 400

        base = ipaddress.IPv4Network(base_network, strict=False)

        # Sort largest first for efficient allocation
        subnets_needed = sorted(enumerate(host_counts), key=lambda x: x[1], reverse=True)

        # Calculate required prefix for each
        def required_prefix(hosts):
            prefix = 32
            while (2 ** (32 - prefix)) < hosts + 2:
                prefix -= 1
            return prefix

        allocated = []
        current_ip = int(base.network_address)
        base_end = int(base.broadcast_address)

        for original_idx, hosts in subnets_needed:
            prefix = required_prefix(hosts)
            block_size = 2 ** (32 - prefix)

            # Align to block boundary
            if current_ip % block_size != 0:
                current_ip = ((current_ip // block_size) + 1) * block_size

            net = ipaddress.IPv4Network(f'{ipaddress.IPv4Address(current_ip)}/{prefix}', strict=False)

            if int(net.broadcast_address) > base_end:
                return jsonify({'error': f'Address space exhausted at subnet #{original_idx + 1} needing {hosts} hosts'}), 400

            usable_hosts = max(0, net.num_addresses - 2)
            first_host = str(net.network_address + 1) if usable_hosts > 0 else str(net.network_address)
            last_host = str(net.broadcast_address - 1) if usable_hosts > 0 else str(net.broadcast_address)

            allocated.append({
                'index': original_idx + 1,
                'hosts_needed': hosts,
                'network': str(net.network_address),
                'cidr': prefix,
                'subnet_mask': str(net.netmask),
                'first_host': first_host,
                'last_host': last_host,
                'broadcast': str(net.broadcast_address),
                'usable_hosts': usable_hosts,
            })
            current_ip = int(net.broadcast_address) + 1

        # Sort back to original order
        allocated.sort(key=lambda x: x['index'])
        return jsonify({'subnets': allocated, 'base_network': base_network})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 400


@app.route('/compare', methods=['POST'])
def compare():
    try:
        data = request.get_json()
        ip1 = data.get('ip1', '').strip()
        ip2 = data.get('ip2', '').strip()
        mask = data.get('mask', '').strip()

        if not ip1 or not ip2 or not mask:
            return jsonify({'error': 'Both IP addresses and a subnet mask are required'}), 400

        ip1_obj = ipaddress.IPv4Address(ip1)
        ip2_obj = ipaddress.IPv4Address(ip2)

        if mask.startswith('/'):
            prefix = int(mask[1:])
        elif '.' in mask:
            net_temp = ipaddress.IPv4Network(f'0.0.0.0/{mask}', strict=False)
            prefix = net_temp.prefixlen
        else:
            prefix = int(mask)

        net1 = ipaddress.IPv4Network(f'{ip1}/{prefix}', strict=False)
        net2 = ipaddress.IPv4Network(f'{ip2}/{prefix}', strict=False)

        same = net1.network_address == net2.network_address

        return jsonify({
            'ip1': ip1,
            'ip2': ip2,
            'network1': f'{net1.network_address}/{prefix}',
            'network2': f'{net2.network_address}/{prefix}',
            'same_subnet': same,
            'subnet_mask': str(net1.netmask),
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 400


@app.route('/supernet', methods=['POST'])
def supernet():
    try:
        data = request.get_json()
        networks_input = data.get('networks', [])

        if len(networks_input) < 2:
            return jsonify({'error': 'At least 2 networks are required'}), 400

        networks = []
        for n in networks_input:
            n = n.strip()
            if n:
                networks.append(ipaddress.IPv4Network(n, strict=False))

        collapsed = list(ipaddress.collapse_addresses(networks))

        result = []
        for net in collapsed:
            usable_hosts = max(0, net.num_addresses - 2)
            first_host = str(net.network_address + 1) if usable_hosts > 0 else str(net.network_address)
            last_host = str(net.broadcast_address - 1) if usable_hosts > 0 else str(net.broadcast_address)

            result.append({
                'supernet': str(net),
                'network_address': str(net.network_address),
                'broadcast': str(net.broadcast_address),
                'subnet_mask': str(net.netmask),
                'prefix': net.prefixlen,
                'total_addresses': net.num_addresses,
                'first_host': first_host,
                'last_host': last_host,
            })

        return jsonify({'supernets': result, 'input_count': len(networks)})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 400


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
