#!/usr/bin/env python3
"""Local-first Mihomo inspection, overlay planning, and reversible exit probes."""
import argparse
import hashlib
import http.client
import ipaddress
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from urllib.parse import quote, urlsplit

CORE = ('anthropic.com', 'claude.ai', 'claude.com', 'clau.de',
        'claudemcpclient.com', 'claudemcpcontent.com', 'claudeusercontent.com')
SUPPORT_SUFFIX = ('sentry.io', 'statsigapi.net', 'statsig.com', 'intercom.io',
                  'intercomcdn.com', 'datadoghq.com', 'sift.com', 'siftcdn.com')
SUPPORT_EXACT = ('servd-anthropic-website.b-cdn.net', 'anthropic.com.cdn.cloudflare.net',
                 'anthropic.auth0.com', 'anthropic-com.ghost.io',
                 'browser-intake-us5-datadoghq.com', 'cdn.usefathom.com')


def yaml_module():
    try:
        import yaml
        return yaml
    except ImportError:
        raise ValueError('Install PyYAML>=6,<7 in a virtual environment first') from None


def load_config(path):
    data = yaml_module().safe_load(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Expected a YAML configuration mapping')
    return data


def private_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Never overwrite an existing file or follow an existing symlink.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        stream.write(content)


def inspect_config(config, show_names=False):
    dns = config.get('dns') or {}
    tun = config.get('tun') or {}
    groups = config.get('proxy-groups') or []
    result = {
        'mode': config.get('mode'), 'ipv6': config.get('ipv6'),
        'dns_enabled': dns.get('enable'), 'dns_ipv6': dns.get('ipv6'),
        'dns_mode': dns.get('enhanced-mode'),
        'dns_respects_rules': dns.get('respect-rules', False),
        'dns_upstream_count': len(dns.get('nameserver') or []),
        'dns_policy_count': len(dns.get('nameserver-policy') or {}),
        'direct_dns_configured': bool(dns.get('direct-nameserver')),
        'proxy_bootstrap_dns_configured': bool(dns.get('proxy-server-nameserver')),
        'tun_enabled': tun.get('enable'),
        'dns_hijack_configured': bool(tun.get('dns-hijack')),
        'group_count': len(groups), 'node_count': len(config.get('proxies') or []),
        'warnings': [],
    }
    servers = dns.get('nameserver') or []
    if any('://' not in str(s) for s in servers):
        result['warnings'].append('Plaintext default DNS upstream present')
    if not dns.get('direct-nameserver'):
        result['warnings'].append('Direct sites share default DNS; check local/intranet access')
    if not dns.get('respect-rules') and any('#' not in str(s) for s in servers):
        result['warnings'].append('Default upstreams do not explicitly use a proxy; verify actual routing')
    if show_names:
        result['groups'] = [{'name': g.get('name'), 'type': g.get('type')} for g in groups]
        result['nodes'] = [n.get('name') for n in config.get('proxies') or []]
    return result


def plan(config, node, group='Claude', support=False):
    nodes = [n.get('name') for n in config.get('proxies') or []]
    if node not in nodes:
        raise ValueError('Selected node does not exist in the input configuration')
    if any(g.get('name') == group for g in config.get('proxy-groups') or []):
        raise ValueError('Group already exists; choose a new group name or edit it manually')
    if any(c in group for c in ',#&\r\n'):
        raise ValueError('Group name contains a rule or DNS separator')
    suffix = CORE + (SUPPORT_SUFFIX if support else ())
    exact = SUPPORT_EXACT if support else ()
    rules = [f'DOMAIN-SUFFIX,{host},{group}' for host in suffix]
    rules += [f'DOMAIN,{host},{group}' for host in exact]
    policies = {f'+.{host}': f'https://1.1.1.1/dns-query#{group}' for host in suffix}
    policies.update({host: f'https://1.1.1.1/dns-query#{group}' for host in exact})
    return {
        'groups.yaml': {'prepend': [{'name': group, 'type': 'select', 'proxies': [node]}],
                        'append': [], 'delete': []},
        'rules.yaml': {'prepend': rules, 'append': [], 'delete': []},
        'dns-policy.yaml': {'dns': {'nameserver-policy': policies}},
    }


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path, timeout):
        super().__init__('localhost', timeout=timeout)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.path)


class Controller:
    def __init__(self, url=None, unix_socket=None, timeout=8):
        self.timeout, self.unix_socket = timeout, unix_socket
        self.url = urlsplit(url or 'http://127.0.0.1:9090')
        if not unix_socket:
            validate_loopback(url or 'http://127.0.0.1:9090')
        self.token = os.environ.get('MIHOMO_API_SECRET', '')

    def request(self, method, path, body=None):
        if self.unix_socket:
            conn = UnixHTTPConnection(self.unix_socket, self.timeout)
        else:
            conn = http.client.HTTPConnection(self.url.hostname, self.url.port, timeout=self.timeout)
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        try:
            conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=headers)
            response = conn.getresponse()
            raw = response.read(4 * 1024 * 1024)
            if response.status >= 400:
                raise ValueError(f'Controller returned HTTP {response.status}')
            return json.loads(raw) if raw else {}
        finally:
            conn.close()

    def group(self, name):
        return self.request('GET', '/proxies/' + quote(name, safe=''))

    def select(self, group, node):
        self.request('PUT', '/proxies/' + quote(group, safe=''), {'name': node})


def validate_loopback(url):
    u = urlsplit(url)
    if u.scheme != 'http' or u.username or u.password or u.query or u.fragment or u.path not in ('', '/'):
        raise ValueError('Use a credential-free loopback HTTP URL; API secrets go in MIHOMO_API_SECRET')
    if u.hostname != 'localhost':
        try:
            if not ipaddress.ip_address(u.hostname or '').is_loopback:
                raise ValueError('Endpoint must be loopback')
        except ValueError:
            raise ValueError('Endpoint must be loopback') from None
    return url


def trace(proxy, timeout):
    validate_loopback(proxy)
    start = time.monotonic()
    result = subprocess.run(['curl', '--silent', '--show-error', '--fail', '--max-time', str(timeout),
                             '--noproxy', '', '--proxy', proxy, 'https://claude.ai/cdn-cgi/trace'],
                            capture_output=True, text=True, timeout=timeout + 3)
    data = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if result.returncode or not data.get('ip'):
        raise ValueError('Trace request failed')
    ipaddress.ip_address(data['ip'])
    return {'ip': data['ip'], 'country': data.get('loc'),
            'request_seconds': round(time.monotonic() - start, 3)}


def risk(ip, proxy, timeout):
    # Explicit opt-in: the service receives the measured public IP.
    result = subprocess.run(['curl', '--silent', '--show-error', '--fail', '--max-time', str(timeout),
                             '--noproxy', '', '--proxy', proxy, 'https://ip.net.coffee/api/iprisk/' + quote(ip, safe='')],
                            capture_output=True, text=True, timeout=timeout + 3)
    if result.returncode:
        raise ValueError('Risk lookup failed')
    data = json.loads(result.stdout)
    keys = ('trust_score', 'is_datacenter', 'is_proxy', 'is_vpn', 'is_tor', 'is_abuser', 'abuser_score')
    return {key: data.get(key) for key in keys}


def probe(controller, group, nodes, proxy, timeout=8, lookup_risk=False, show_ips=False,
          trace_fn=trace, risk_fn=risk):
    validate_loopback(proxy)
    state = controller.group(group)
    if state.get('type') != 'Selector':
        raise ValueError('Probing requires a manual Selector group')
    original = state.get('now')
    if not original or any(n not in state.get('all', []) for n in nodes):
        raise ValueError('Unknown node or missing original selection')
    salt, results = secrets.token_bytes(32), []
    try:
        for index, node in enumerate(nodes, 1):
            controller.select(group, node)
            item = {'candidate': index, 'ok': False}
            try:
                measured = trace_fn(proxy, timeout)
                ip = measured.pop('ip')
                item.update(measured)
                item['ip_version'] = ipaddress.ip_address(ip).version
                item['exit_id'] = hashlib.sha256(salt + ip.encode()).hexdigest()[:12]
                item['ok'] = True
                if show_ips:
                    item['ip'] = ip
                if lookup_risk:
                    try:
                        item['third_party_risk'] = risk_fn(ip, proxy, timeout)
                    except (ValueError, OSError, subprocess.SubprocessError):
                        item['risk_error'] = 'lookup_failed'
            except (ValueError, OSError, subprocess.SubprocessError):
                item['error'] = 'trace_failed'
            results.append(item)
    finally:
        controller.select(group, original)
        if controller.group(group).get('now') != original:
            raise ValueError('RESTORATION FAILED: stop probing and restore the original group manually')
    return {'restored': True, 'candidates': results,
            'note': 'Candidates follow --nodes order; timings are single requests, not RTT benchmarks'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('inspect', help='Read-only, allowlisted summary')
    inspect.add_argument('--config', required=True)
    inspect.add_argument('--show-names', action='store_true', help='Local use only; names may identify a subscription')
    generate = commands.add_parser('plan', help='Generate overlays without editing live configuration')
    generate.add_argument('--config', required=True)
    generate.add_argument('--node', required=True)
    generate.add_argument('--group', default='Claude')
    generate.add_argument('--include-support', action='store_true', help='Shared services also affect other applications')
    generate.add_argument('--output', required=True, help='New local, untracked directory')
    compare = commands.add_parser('probe', help='Temporarily switch only the specified group, then restore')
    endpoint = compare.add_mutually_exclusive_group(required=True)
    endpoint.add_argument('--controller')
    endpoint.add_argument('--socket')
    compare.add_argument('--group', default='Claude')
    compare.add_argument('--nodes', nargs='+', required=True)
    compare.add_argument('--proxy', required=True)
    compare.add_argument('--timeout', type=float, default=8)
    compare.add_argument('--risk', action='store_true', help='Disclose measured exit IP to Net.Coffee')
    compare.add_argument('--show-ips', action='store_true', help='Print public exit addresses locally')
    args = parser.parse_args()
    if args.command == 'inspect':
        result = inspect_config(load_config(args.config), args.show_names)
    elif args.command == 'plan':
        directory = Path(args.output)
        if directory.exists():
            raise ValueError('Output directory already exists; use a fresh local directory')
        overlays = plan(load_config(args.config), args.node, args.group, args.include_support)
        directory.mkdir(parents=True, mode=0o700)
        for name, overlay in overlays.items():
            private_write(directory / name, yaml_module().safe_dump(overlay, allow_unicode=True, sort_keys=False))
        result = {'generated': list(overlays), 'live_config_modified': False,
                  'note': 'Merge into existing extensions; do not replace unrelated rules or DNS'}
    else:
        if not 1 <= args.timeout <= 30:
            raise ValueError('Timeout must be between 1 and 30 seconds')
        result = probe(Controller(args.controller, args.socket), args.group, args.nodes, args.proxy,
                       args.timeout, args.risk, args.show_ips)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError, http.client.HTTPException):
        # Do not print raw URLs, paths, controller bodies, credentials, or config contents.
        print('Operation failed. Check the local inputs/controller. If probing was interrupted, verify the original group selection.', file=sys.stderr)
        sys.exit(1)
