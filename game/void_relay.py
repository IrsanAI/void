#!/usr/bin/env python3
"""
VOID Relay v0.1
- server: zentraler Relay (pairt Host + Join per Room-Code)
- host: outbound Tunnel vom Host-Gerät zum Relay und lokalem void_server
- join: outbound Tunnel vom Join-Gerät zum Relay und lokalem void_client
"""

import argparse
import json
import socket
import threading
import time

BUFFER = 4096
DEFAULT_ROOM_TTL = 120


def _send_json(sock, payload):
    sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))


def _recv_json_line(sock, timeout=15.0):
    sock.settimeout(timeout)
    buf = ""
    while "\n" not in buf:
        chunk = sock.recv(1024)
        if not chunk:
            raise ConnectionError("Verbindung geschlossen")
        buf += chunk.decode("utf-8", errors="ignore")
    line, _ = buf.split("\n", 1)
    return json.loads(line.strip())


def _pump(src, dst):
    try:
        while True:
            data = src.recv(BUFFER)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            dst.close()
        except Exception:
            pass
        try:
            src.close()
        except Exception:
            pass


def _bridge(a, b):
    t1 = threading.Thread(target=_pump, args=(a, b), daemon=True)
    t2 = threading.Thread(target=_pump, args=(b, a), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


class RelayServer:
    def __init__(self, host, port, room_ttl=DEFAULT_ROOM_TTL):
        self.host = host
        self.port = port
        self.room_ttl = room_ttl
        self.rooms = {}
        self.lock = threading.Lock()

    def serve_forever(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(64)
        print(f"[relay] listening on {self.host}:{self.port} (room_ttl={self.room_ttl}s)")

        while True:
            self._cleanup_expired_rooms()
            conn, addr = srv.accept()
            threading.Thread(target=self._handle_conn, args=(conn, addr), daemon=True).start()

    def _cleanup_expired_rooms(self):
        now = time.time()
        stale = []
        with self.lock:
            for room, slot in self.rooms.items():
                if now - slot["created"] > self.room_ttl:
                    stale.append((room, slot["host"]))
            for room, _ in stale:
                self.rooms.pop(room, None)

        for room, host_conn in stale:
            try:
                _send_json(host_conn, {"status": "error", "reason": "room timeout", "code": "ROOM_TIMEOUT"})
            except Exception:
                pass
            try:
                host_conn.close()
            except Exception:
                pass
            print(f"[relay] room {room} expired")

    def _handle_conn(self, conn, addr):
        try:
            hello = _recv_json_line(conn)
            role = hello.get("role")
            room = str(hello.get("room", "")).strip().upper()
            if not room:
                _send_json(conn, {"status": "error", "reason": "room required", "code": "ROOM_REQUIRED"})
                conn.close()
                return

            if role == "host":
                with self.lock:
                    if room in self.rooms:
                        _send_json(conn, {"status": "error", "reason": "room already has host", "code": "ROOM_IN_USE"})
                        conn.close()
                        return
                    self.rooms[room] = {"host": conn, "created": time.time()}
                _send_json(conn, {"status": "waiting", "room": room})
                return

            if role == "join":
                with self.lock:
                    slot = self.rooms.pop(room, None)
                if not slot:
                    _send_json(conn, {"status": "error", "reason": "room not found", "code": "ROOM_NOT_FOUND"})
                    conn.close()
                    return

                host_conn = slot["host"]
                _send_json(conn, {"status": "paired", "room": room})
                _send_json(host_conn, {"status": "paired", "room": room})
                print(f"[relay] room {room} paired: {addr}")
                _bridge(host_conn, conn)
                print(f"[relay] room {room} closed")
                return

            _send_json(conn, {"status": "error", "reason": "invalid role"})
            conn.close()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass


def run_server(args):
    RelayServer(args.listen_host, args.listen_port, args.room_ttl).serve_forever()


def _open_relay(role, relay_host, relay_port, room):
    relay = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    relay.connect((relay_host, relay_port))
    _send_json(relay, {"role": role, "room": room.upper()})
    return relay, _recv_json_line(relay)


def run_host(args):
    relay, msg = _open_relay("host", args.relay_host, args.relay_port, args.room)
    if msg.get("status") == "error":
        raise RuntimeError(f"Relay-Fehler [{msg.get('code', 'UNKNOWN')}]: {msg.get('reason')}")
    print(f"[host] waiting for join in room {args.room.upper()} @ {args.relay_host}:{args.relay_port}")

    msg = _recv_json_line(relay, timeout=None)
    if msg.get("status") != "paired":
        raise RuntimeError("Relay pairing fehlgeschlagen")
    print("[host] paired, verbinde lokal mit void_server...")

    local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local.connect((args.target_host, args.target_port))
    print(f"[host] tunnel aktiv <-> {args.target_host}:{args.target_port}")
    _bridge(relay, local)


def run_join(args):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((args.listen_host, args.listen_port))
    listener.listen(1)
    print(f"[join] local endpoint wartet auf void_client: {args.listen_host}:{args.listen_port}")

    relay = None
    deadline = time.time() + args.retry_seconds
    while True:
        relay = None
        try:
            relay, msg = _open_relay("join", args.relay_host, args.relay_port, args.room)
        except OSError as exc:
            msg = {"status": "error", "reason": str(exc), "code": "RELAY_UNREACHABLE"}

        if msg.get("status") != "error":
            break

        if relay is not None:
            try:
                relay.close()
            except Exception:
                pass

        if msg.get("code") != "ROOM_NOT_FOUND" and time.time() >= deadline:
            raise RuntimeError(f"Relay-Fehler [{msg.get('code', 'UNKNOWN')}]: {msg.get('reason')}")

        if time.time() >= deadline:
            raise RuntimeError("Relay pairing fehlgeschlagen: Room nicht gefunden (Timeout)")

        print(f"[join] warte auf Host ({msg.get('code', 'UNKNOWN')}) ...")
        time.sleep(args.retry_interval)

    if msg.get("status") == "error":
        raise RuntimeError(f"Relay-Fehler [{msg.get('code', 'UNKNOWN')}]: {msg.get('reason')}")
    if msg.get("status") != "paired":
        raise RuntimeError("Relay pairing fehlgeschlagen")

    print("[join] paired. Starte jetzt void_client auf localhost.")
    local_conn, local_addr = listener.accept()
    print(f"[join] local client connected: {local_addr}")
    _bridge(local_conn, relay)


def build_parser():
    p = argparse.ArgumentParser(description="VOID relay helper")
    sub = p.add_subparsers(dest="mode", required=True)

    ps = sub.add_parser("server", help="Relay-Server starten")
    ps.add_argument("--listen-host", default="0.0.0.0")
    ps.add_argument("--listen-port", type=int, default=8787)
    ps.add_argument("--room-ttl", type=int, default=DEFAULT_ROOM_TTL, help="Room timeout in seconds")

    ph = sub.add_parser("host", help="Host-Tunnel starten")
    ph.add_argument("--relay-host", required=True)
    ph.add_argument("--relay-port", type=int, default=8787)
    ph.add_argument("--room", required=True)
    ph.add_argument("--target-host", default="127.0.0.1")
    ph.add_argument("--target-port", type=int, default=7777)

    pj = sub.add_parser("join", help="Join-Tunnel starten")
    pj.add_argument("--relay-host", required=True)
    pj.add_argument("--relay-port", type=int, default=8787)
    pj.add_argument("--room", required=True)
    pj.add_argument("--listen-host", default="127.0.0.1")
    pj.add_argument("--listen-port", type=int, default=17777)
    pj.add_argument("--retry-seconds", type=int, default=20)
    pj.add_argument("--retry-interval", type=float, default=2.0)

    return p


def main():
    args = build_parser().parse_args()
    if args.mode == "server":
        return run_server(args)
    if args.mode == "host":
        return run_host(args)
    if args.mode == "join":
        return run_join(args)


if __name__ == "__main__":
    main()
