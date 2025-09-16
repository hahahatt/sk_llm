"""
로그 생성 모듈
시나리오에 따라 각 시스템별로 실제적인 로그를 생성
"""

import random
import datetime
from typing import Dict, Any, List
import ipaddress
import uuid

class LogGenerator:
    def __init__(self):
        """로그 생성기 초기화"""
        self.init_data_pools()
    
    def init_data_pools(self):
        """로그 생성에 사용할 데이터 풀 초기화"""
        
        # IP 주소 풀
        self.internal_ips = [
            "192.168.1.100", "192.168.1.150", "192.168.1.200",
            "10.0.0.50", "10.0.0.100", "10.0.0.200",
            "172.16.0.25", "172.16.0.50", "172.16.0.100"
        ]
        
        self.external_ips = [
            "203.250.133.88", "8.8.8.8", "1.1.1.1",
            "185.220.100.240", "94.130.135.25", "45.33.32.156"
        ]
        
        self.malicious_ips = [
            "185.220.101.42", "194.147.142.25", "45.134.26.45",
            "91.200.81.15", "159.89.214.31", "167.99.74.55"
        ]
        
        # 도메인 풀
        self.normal_domains = [
            "google.com", "microsoft.com", "amazon.com", "facebook.com",
            "github.com", "stackoverflow.com", "linkedin.com"
        ]
        
        self.malicious_domains = [
            "evil-c2.com", "malicious-site.com", "phishing-bank.com",
            "fake-update.net", "suspicious-download.org"
        ]
        
        # 사용자 계정 풀
        self.user_accounts = [
            "admin", "user1", "user2", "service", "backup",
            "john.doe", "jane.smith", "bob.wilson", "alice.johnson"
        ]
        
        # 파일 경로 풀
        self.file_paths = [
            "/var/log/access.log", "/home/user/documents/",
            "/opt/application/config/", "/tmp/",
            "C:\\Users\\admin\\Documents\\", "C:\\Windows\\System32\\",
            "C:\\Program Files\\Application\\"
        ]
        
        # 프로세스 풀
        self.processes = [
            "chrome.exe", "firefox.exe", "notepad.exe", "cmd.exe",
            "powershell.exe", "svchost.exe", "explorer.exe",
            "malware.exe", "backdoor.exe", "keylogger.exe"
        ]
    
    def generate_log_content(self, log_type: Dict[str, str], count: int, scenario: Dict[str, Any]) -> str:
        """
        로그 컨텐츠 생성
        
        Args:
            log_type (Dict[str, str]): 로그 타입 정보
            count (int): 생성할 로그 개수
            scenario (Dict[str, Any]): 시나리오 정보
            
        Returns:
            str: 생성된 로그 컨텐츠
        """
        
        logs = []
        base_time = datetime.datetime.now() - datetime.timedelta(hours=2)
        timeline_phases = len(scenario['timeline'])
        
        for i in range(count):
            # 현재 로그가 속하는 공격 단계 계산
            phase = int((i / count) * timeline_phases)
            
            # 시간 계산 (순차적으로 증가)
            timestamp = base_time + datetime.timedelta(seconds=i * 2)
            
            # 로그 타입별 생성 함수 호출
            log_entry = self._generate_single_log(
                log_type['type'], timestamp, phase, scenario, i, count
            )
            
            logs.append(log_entry)
        
        return '\n'.join(logs)
    
    def _generate_single_log(self, log_type: str, timestamp: datetime.datetime, 
                           phase: int, scenario: Dict[str, Any], index: int, total: int) -> str:
        """
        단일 로그 엔트리 생성
        
        Args:
            log_type (str): 로그 타입
            timestamp (datetime.datetime): 로그 시간
            phase (int): 공격 단계
            scenario (Dict[str, Any]): 시나리오 정보
            index (int): 현재 로그 인덱스
            total (int): 전체 로그 개수
            
        Returns:
            str: 단일 로그 엔트리
        """
        
        # 로그 생성 함수 매핑
        generators = {
            'firewall': self._generate_firewall_log,
            'webserver': self._generate_webserver_log,
            'waf': self._generate_waf_log,
            'auth': self._generate_auth_log,
            'database': self._generate_database_log,
            'proxy': self._generate_proxy_log,
            'email': self._generate_email_log,
            'endpoint': self._generate_endpoint_log,
            'dns': self._generate_dns_log,
            'network': self._generate_network_log,
            'fileserver': self._generate_fileserver_log,
            'usb': self._generate_usb_log,
            'dlp': self._generate_dlp_log,
            'router': self._generate_router_log,
            'loadbalancer': self._generate_loadbalancer_log,
            'cdn': self._generate_cdn_log,
            'backup': self._generate_backup_log
        }
        
        generator = generators.get(log_type, self._generate_generic_log)
        return generator(timestamp, phase, scenario, index, total)
    
    def _generate_firewall_log(self, timestamp: datetime.datetime, phase: int, 
                              scenario: Dict[str, Any], index: int, total: int) -> str:
        """방화벽 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # 공격 단계에 따른 로그 패턴 변경
        if phase < 2:  # 초기 정찰
            src_ip = random.choice(self.external_ips)
            dst_ip = random.choice(self.internal_ips)
            action = "ALLOW" if random.random() < 0.8 else "DENY"
            port = random.choice([80, 443, 22, 21, 25])
        elif phase < 4:  # 공격 시도
            src_ip = random.choice(self.malicious_ips)
            dst_ip = random.choice(self.internal_ips)
            action = "DENY" if random.random() < 0.6 else "ALLOW"
            port = random.choice([80, 443, 8080, 3389, 445])
        else:  # 공격 성공 후
            src_ip = random.choice(self.malicious_ips)
            dst_ip = random.choice(self.internal_ips)
            action = "ALLOW" if random.random() < 0.7 else "DENY"
            port = random.choice([443, 80, 53, 443])
        
        return f"{time_str} [FIREWALL] SRC={src_ip} DST={dst_ip} PROTO=TCP SPORT={random.randint(1024, 65535)} DPORT={port} ACTION={action} LEN={random.randint(40, 1500)}"
    
    def _generate_webserver_log(self, timestamp: datetime.datetime, phase: int,
                               scenario: Dict[str, Any], index: int, total: int) -> str:
        """웹서버 로그 생성"""
        
        time_str = timestamp.strftime('%d/%b/%Y:%H:%M:%S +0000')
        
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']
        normal_paths = ['/', '/index.html', '/about.html', '/contact.html', '/products']
        attack_paths = ['/admin/', '/login.php', '/admin/login.php', '/wp-admin/', '/phpmyadmin/']
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'curl/7.64.1',
            'sqlmap/1.4.7',
            'Nikto/2.1.6'
        ]
        
        if phase < 2:  # 정상 트래픽
            method = random.choice(['GET', 'POST'])
            path = random.choice(normal_paths)
            status = random.choice([200, 304, 404])
            user_agent = user_agents[0]
            src_ip = random.choice(self.external_ips)
        elif phase < 4:  # 공격 시도
            method = random.choice(['GET', 'POST'])
            path = random.choice(attack_paths)
            if "' OR 1=1" in path or "UNION SELECT" in path:
                path += "?id=1' OR 1=1--"
            status = random.choice([401, 403, 500, 200])
            user_agent = random.choice(user_agents[1:])
            src_ip = random.choice(self.malicious_ips)
        else:  # 공격 성공
            method = random.choice(['GET', 'POST'])
            path = random.choice(attack_paths)
            status = 200
            user_agent = user_agents[0]
            src_ip = random.choice(self.malicious_ips)
        
        size = random.randint(200, 50000)
        
        return f'{src_ip} - - [{time_str}] "{method} {path} HTTP/1.1" {status} {size} "-" "{user_agent}"'
    
    def _generate_waf_log(self, timestamp: datetime.datetime, phase: int,
                         scenario: Dict[str, Any], index: int, total: int) -> str:
        """WAF 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        attack_types = ['SQL_INJECTION', 'XSS', 'LFI', 'RFI', 'CSRF', 'COMMAND_INJECTION']
        severity_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        if phase < 1:  # 정상 요청
            return f"{time_str} [WAF] INFO: Request processed - SRC: {random.choice(self.external_ips)} - Clean request"
        elif phase < 4:  # 공격 탐지
            attack = random.choice(attack_types)
            severity = random.choice(severity_levels[1:])
            payload = self._generate_attack_payload(attack)
            src_ip = random.choice(self.malicious_ips)
            
            return f'{time_str} [WAF] ALERT {severity}: {attack} detected from {src_ip} - Payload: "{payload}"'
        else:  # 우회된 공격
            if random.random() < 0.3:  # 30% 확률로 탐지
                attack = random.choice(attack_types)
                severity = 'CRITICAL'
                src_ip = random.choice(self.malicious_ips)
                return f'{time_str} [WAF] ALERT {severity}: {attack} bypass attempt from {src_ip}'
            else:
                return f"{time_str} [WAF] INFO: Request processed - SRC: {random.choice(self.malicious_ips)} - Bypassed detection"
    
    def _generate_attack_payload(self, attack_type: str) -> str:
        """공격 페이로드 생성"""
        
        payloads = {
            'SQL_INJECTION': [
                "' OR 1=1--", "' UNION SELECT null,null--", "'; DROP TABLE users--",
                "1' AND (SELECT COUNT(*) FROM information_schema.tables)>0--"
            ],
            'XSS': [
                "<script>alert('XSS')</script>", "<img src=x onerror=alert(1)>",
                "javascript:alert(document.cookie)"
            ],
            'LFI': [
                "../../../etc/passwd", "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"
            ],
            'COMMAND_INJECTION': [
                "; cat /etc/passwd", "| whoami", "&& dir C:\\"
            ]
        }
        
        return random.choice(payloads.get(attack_type, ["malicious_payload"]))
    
    def _generate_auth_log(self, timestamp: datetime.datetime, phase: int,
                          scenario: Dict[str, Any], index: int, total: int) -> str:
        """인증 시스템 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        events = ['LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 'PASSWORD_CHANGE', 'ACCOUNT_LOCKED']
        
        if phase < 2:  # 정상 인증
            user = random.choice(self.user_accounts[:5])  # 정상 사용자
            event = random.choice(['LOGIN_SUCCESS', 'LOGOUT'])
            src_ip = random.choice(self.internal_ips)
        elif phase < 4:  # 공격 시도
            user = 'admin' if random.random() < 0.7 else random.choice(self.user_accounts)
            event = 'LOGIN_FAILED' if random.random() < 0.8 else 'ACCOUNT_LOCKED'
            src_ip = random.choice(self.malicious_ips)
        else:  # 공격 성공
            user = 'admin'
            event = 'LOGIN_SUCCESS' if random.random() < 0.6 else 'PASSWORD_CHANGE'
            src_ip = random.choice(self.malicious_ips)
        
        session_id = str(uuid.uuid4())[:8]
        
        return f"{time_str} [AUTH] User: {user} Event: {event} Source: {src_ip} Session: {session_id}"
    
    def _generate_database_log(self, timestamp: datetime.datetime, phase: int,
                              scenario: Dict[str, Any], index: int, total: int) -> str:
        """데이터베이스 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        operations = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        tables = ['users', 'products', 'orders', 'customers', 'logs', 'config']
        
        if phase < 3:  # 정상 DB 접근
            operation = random.choice(['SELECT', 'INSERT', 'UPDATE'])
            table = random.choice(tables[:4])
            user = random.choice(['webapp', 'service', 'admin'])
            rows = random.randint(1, 100)
        elif phase < 5:  # 공격 시도
            operation = 'SELECT'
            table = random.choice(['users', 'customers', 'admin_config'])
            user = 'admin'
            rows = random.randint(100, 10000)
        else:  # 데이터 유출
            operation = 'SELECT'
            table = random.choice(['customers', 'credit_cards', 'personal_info'])
            user = 'admin'
            rows = random.randint(1000, 50000)
        
        duration = random.uniform(0.1, 5.0)
        
        return f"{time_str} [DB] User: {user} Operation: {operation} Table: {table} Rows: {rows} Duration: {duration:.2f}s"
    
    def _generate_proxy_log(self, timestamp: datetime.datetime, phase: int,
                           scenario: Dict[str, Any], index: int, total: int) -> str:
        """프록시 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        if phase < 2:  # 정상 트래픽
            domain = random.choice(self.normal_domains)
            method = 'GET'
            status = 200
        elif phase < 4:  # 의심스러운 통신
            domain = random.choice(self.malicious_domains)
            method = random.choice(['GET', 'POST'])
            status = random.choice([200, 403, 404])
        else:  # 데이터 유출
            domain = 'external-server.com'
            method = 'POST'
            status = 200
        
        src_ip = random.choice(self.internal_ips)
        size = random.randint(1024, 1048576)
        
        return f"{time_str} [PROXY] {method} https://{domain}/ - Client: {src_ip} Status: {status} Size: {size}"
    
    def _generate_email_log(self, timestamp: datetime.datetime, phase: int,
                           scenario: Dict[str, Any], index: int, total: int) -> str:
        """이메일 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        internal_emails = ['user@company.com', 'admin@company.com', 'support@company.com']
        external_emails = ['contact@partner.com', 'info@supplier.com']
        malicious_emails = ['attacker@evil.com', 'phishing@fake-bank.com']
        
        subjects = ['Meeting Schedule', 'Project Update', 'Important Document', 'Urgent Action Required']
        malicious_subjects = ['Account Verification Required', 'Security Alert', 'Invoice #12345']
        
        if phase == 0:  # 초기 피싱
            from_addr = random.choice(malicious_emails)
            to_addr = random.choice(internal_emails)
            subject = random.choice(malicious_subjects)
            attachment = 'invoice.doc' if random.random() < 0.5 else None
        elif phase < 3:  # 정상 이메일
            from_addr = random.choice(internal_emails + external_emails)
            to_addr = random.choice(internal_emails)
            subject = random.choice(subjects)
            attachment = None
        else:  # 데이터 유출
            from_addr = random.choice(internal_emails)
            to_addr = 'external@gmail.com'
            subject = 'Confidential Data'
            attachment = 'customer_data.zip'
        
        size = random.randint(1024, 10485760)
        attachment_str = f" ATTACHMENT: {attachment}" if attachment else ""
        
        return f"{time_str} [EMAIL] FROM: {from_addr} TO: {to_addr} SUBJECT: \"{subject}\" SIZE: {size}{attachment_str}"
    
    def _generate_endpoint_log(self, timestamp: datetime.datetime, phase: int,
                              scenario: Dict[str, Any], index: int, total: int) -> str:
        """엔드포인트 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        normal_processes = ['chrome.exe', 'notepad.exe', 'outlook.exe', 'excel.exe']
        malicious_processes = ['malware.exe', 'backdoor.exe', 'keylogger.exe', 'ransomware.exe']
        
        events = ['PROCESS_START', 'PROCESS_STOP', 'FILE_WRITE', 'REGISTRY_MODIFY', 'NETWORK_CONNECT']
        
        if phase < 1:  # 정상 활동
            process = random.choice(normal_processes)
            event = random.choice(events[:2])
            path = 'C:\\Program Files\\Application\\'
        elif phase < 3:  # 멀웨어 실행
            process = random.choice(malicious_processes)
            event = random.choice(events)
            path = 'C:\\Users\\user\\AppData\\Temp\\'
        else:  # 지속적인 악성 활동
            process = random.choice(malicious_processes)
            event = random.choice(events[2:])  # 파일/레지스트리 변경
            path = 'C:\\Windows\\System32\\'
        
        user = random.choice(self.user_accounts[:3])
        
        return f"{time_str} [ENDPOINT] Process: {process} Event: {event} User: {user} Path: {path}"
    
    def _generate_dns_log(self, timestamp: datetime.datetime, phase: int,
                         scenario: Dict[str, Any], index: int, total: int) -> str:
        """DNS 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        query_types = ['A', 'AAAA', 'MX', 'TXT', 'CNAME']
        
        if phase < 2:  # 정상 DNS 질의
            domain = random.choice(self.normal_domains)
            query_type = random.choice(['A', 'AAAA'])
        elif phase < 4:  # 악성 도메인 질의
            domain = random.choice(self.malicious_domains)
            query_type = 'A'
        else:  # C&C 통신
            domain = f"c2-{random.randint(1000, 9999)}.evil.com"
            query_type = random.choice(['A', 'TXT'])
        
        client_ip = random.choice(self.internal_ips)
        response_ip = random.choice(self.external_ips)
        
        return f"{time_str} [DNS] Query: {domain} Type: {query_type} Client: {client_ip} Response: {response_ip}"
    
    def _generate_network_log(self, timestamp: datetime.datetime, phase: int,
                             scenario: Dict[str, Any], index: int, total: int) -> str:
        """네트워크 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        protocols = ['TCP', 'UDP', 'ICMP']
        ports = [80, 443, 22, 3389, 445, 135, 1433, 3306]
        
        if phase < 2:  # 정상 트래픽
            src_ip = random.choice(self.internal_ips)
            dst_ip = random.choice(self.internal_ips)
            protocol = 'TCP'
            port = random.choice([80, 443, 22])
        elif phase < 4:  # 네트워크 스캔
            src_ip = random.choice(self.internal_ips)
            dst_ip = random.choice(self.internal_ips)
            protocol = 'TCP'
            port = random.choice(ports)
        else:  # 횡적 이동
            src_ip = random.choice(self.internal_ips)
            dst_ip = random.choice(self.internal_ips)
            protocol = 'TCP'
            port = random.choice([445, 135, 3389])  # SMB, RPC, RDP
        
        bytes_sent = random.randint(64, 65536)
        
        return f"{time_str} [NETWORK] SRC: {src_ip}:{random.randint(1024, 65535)} DST: {dst_ip}:{port} PROTO: {protocol} BYTES: {bytes_sent}"
    
    def _generate_fileserver_log(self, timestamp: datetime.datetime, phase: int,
                                scenario: Dict[str, Any], index: int, total: int) -> str:
        """파일서버 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        operations = ['READ', 'write', 'delete', 'copy', 'move']
        file_types = ['document.pdf', 'report.xlsx', 'customer_data.csv', 'config.txt', 'backup.zip']
        
        if phase < 2:  # 정상 파일 접근
            operation = random.choice(['read', 'write'])
            file_name = random.choice(file_types[:3])
            user = random.choice(self.user_accounts[:3])
        elif phase < 4:  # 의심스러운 접근
            operation = 'read'
            file_name = 'customer_data.csv'
            user = 'admin'
        else:  # 대량 파일 복사
            operation = random.choice(['copy', 'read'])
            file_name = random.choice(['customer_data.csv', 'financial_reports.xlsx'])
            user = 'admin'
        
        file_size = random.randint(1024, 104857600)
        
        return f"{time_str} [FILESERVER] User: {user} Operation: {operation} File: /data/{file_name} Size: {file_size}"
    
    def _generate_usb_log(self, timestamp: datetime.datetime, phase: int,
                         scenario: Dict[str, Any], index: int, total: int) -> str:
        """USB 모니터링 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        events = ['USB_CONNECT', 'USB_DISCONNECT', 'FILE_COPY_TO_USB', 'FILE_COPY_FROM_USB']
        device_ids = ['USB_DEVICE_001', 'USB_DEVICE_002', 'USB_DEVICE_003']
        
        if phase < 3:  # 정상 USB 사용
            event = random.choice(['USB_CONNECT', 'USB_DISCONNECT'])
            device = random.choice(device_ids)
            user = random.choice(self.user_accounts[:3])
            file_info = ""
        else:  # 데이터 유출
            event = 'FILE_COPY_TO_USB'
            device = 'USB_DEVICE_001'
            user = 'admin'
            file_info = f" FILE: customer_data.csv SIZE: {random.randint(1048576, 104857600)}"
        
        return f"{time_str} [USB] Device: {device} Event: {event} User: {user}{file_info}"
    
    def _generate_dlp_log(self, timestamp: datetime.datetime, phase: int,
                         scenario: Dict[str, Any], index: int, total: int) -> str:
        """DLP 시스템 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        actions = ['ALLOW', 'BLOCK', 'WARN', 'QUARANTINE']
        channels = ['EMAIL', 'USB', 'WEB', 'PRINT', 'CLOUD_UPLOAD']
        policies = ['PII_PROTECTION', 'CREDIT_CARD_DATA', 'CONFIDENTIAL_DOCS', 'FINANCIAL_DATA']
        
        if phase < 3:  # 정상 활동
            action = 'ALLOW'
            channel = random.choice(channels[:3])
            policy = random.choice(policies)
            user = random.choice(self.user_accounts[:3])
        else:  # 정책 위반 탐지
            action = random.choice(['BLOCK', 'WARN'])
            channel = random.choice(['EMAIL', 'USB'])
            policy = 'PII_PROTECTION'
            user = 'admin'
        
        confidence = random.randint(70, 99)
        
        return f"{time_str} [DLP] Action: {action} Channel: {channel} Policy: {policy} User: {user} Confidence: {confidence}%"
    
    def _generate_router_log(self, timestamp: datetime.datetime, phase: int,
                            scenario: Dict[str, Any], index: int, total: int) -> str:
        """라우터 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        interfaces = ['eth0', 'eth1', 'wan0', 'lan0']
        events = ['LINK_UP', 'LINK_DOWN', 'ROUTING_UPDATE', 'BANDWIDTH_EXCEEDED', 'PACKET_DROP']
        
        if phase < 2:  # 정상 라우터 동작
            interface = random.choice(interfaces)
            event = random.choice(['LINK_UP', 'ROUTING_UPDATE'])
            bandwidth = random.randint(10, 100)
        elif phase < 4:  # 트래픽 증가
            interface = 'wan0'
            event = 'BANDWIDTH_EXCEEDED'
            bandwidth = random.randint(800, 1000)
        else:  # DDoS 공격 중
            interface = 'wan0'
            event = random.choice(['BANDWIDTH_EXCEEDED', 'PACKET_DROP'])
            bandwidth = random.randint(900, 1000)
        
        return f"{time_str} [ROUTER] Interface: {interface} Event: {event} Bandwidth: {bandwidth}Mbps"
    
    def _generate_loadbalancer_log(self, timestamp: datetime.datetime, phase: int,
                                  scenario: Dict[str, Any], index: int, total: int) -> str:
        """로드밸런서 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        servers = ['web01', 'web02', 'web03', 'web04']
        status_types = ['HEALTHY', 'UNHEALTHY', 'OVERLOADED', 'TIMEOUT']
        
        if phase < 2:  # 정상 상태
            server = random.choice(servers)
            status = 'HEALTHY'
            connections = random.randint(50, 200)
            response_time = random.randint(50, 300)
        elif phase < 4:  # 부하 증가
            server = random.choice(servers)
            status = random.choice(['HEALTHY', 'OVERLOADED'])
            connections = random.randint(500, 2000)
            response_time = random.randint(300, 1000)
        else:  # 서버 과부하
            server = random.choice(servers)
            status = random.choice(['OVERLOADED', 'TIMEOUT', 'UNHEALTHY'])
            connections = random.randint(2000, 10000)
            response_time = random.randint(1000, 5000)
        
        return f"{time_str} [LB] Server: {server} Status: {status} Connections: {connections} Response_Time: {response_time}ms"
    
    def _generate_cdn_log(self, timestamp: datetime.datetime, phase: int,
                         scenario: Dict[str, Any], index: int, total: int) -> str:
        """CDN 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        edges = ['edge01.cdn.com', 'edge02.cdn.com', 'edge03.cdn.com']
        resources = ['/css/style.css', '/js/app.js', '/images/logo.png', '/api/data', '/index.html']
        
        if phase < 2:  # 정상 CDN 동작
            edge = random.choice(edges)
            resource = random.choice(resources)
            status = 200
            cache = random.choice(['HIT', 'MISS'])
        elif phase < 4:  # 트래픽 증가
            edge = random.choice(edges)
            resource = random.choice(resources)
            status = 200 if random.random() < 0.8 else 503
            cache = 'HIT' if random.random() < 0.6 else 'MISS'
        else:  # 서비스 장애
            edge = random.choice(edges)
            resource = random.choice(resources)
            status = 503 if random.random() < 0.7 else 200
            cache = 'MISS'
        
        size = random.randint(1024, 1048576)
        
        return f"{time_str} [CDN] Edge: {edge} Resource: {resource} Status: {status} Cache: {cache} Size: {size}"
    
    def _generate_backup_log(self, timestamp: datetime.datetime, phase: int,
                            scenario: Dict[str, Any], index: int, total: int) -> str:
        """백업 시스템 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        operations = ['BACKUP_START', 'BACKUP_COMPLETE', 'BACKUP_FAILED', 'RESTORE_START', 'BACKUP_DELETE']
        backup_types = ['FULL', 'INCREMENTAL', 'DIFFERENTIAL']
        
        if phase < 3:  # 정상 백업
            operation = random.choice(['BACKUP_START', 'BACKUP_COMPLETE'])
            backup_type = random.choice(backup_types)
            size = random.randint(1073741824, 107374182400)  # 1GB - 100GB
            status = 'SUCCESS'
        else:  # 백업 시스템 공격
            operation = random.choice(['BACKUP_DELETE', 'BACKUP_FAILED'])
            backup_type = 'FULL'
            size = random.randint(1073741824, 107374182400)
            status = 'FAILED' if operation == 'BACKUP_FAILED' else 'DELETED'
        
        return f"{time_str} [BACKUP] Operation: {operation} Type: {backup_type} Size: {size} Status: {status}"
    
    def _generate_generic_log(self, timestamp: datetime.datetime, phase: int,
                             scenario: Dict[str, Any], index: int, total: int) -> str:
        """일반 로그 생성"""
        
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return f"{time_str} [SYSTEM] Generic log entry {index + 1} - Phase: {phase} - {scenario.get('attack_type', 'unknown')}"