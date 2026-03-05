"""
CWASA Avatar Player

Interfaces with the CWASA (CWA Signing Avatars) SiGML Player application
to render sign language animations from SiGML XML.

The player communicates via TCP socket on port 8052, sending SiGML data
which the avatar application renders in real-time.

Reference: https://vh.cmp.uea.ac.uk/index.php/Driving_the_SiGML_Player_App
"""

import logging
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

from config.settings import avatar_config

logger = logging.getLogger(__name__)


class CWASAPlayerError(Exception):
    """Exception raised for CWASA player errors."""
    pass


class CWASAPlayer:
    """
    Client for the CWASA SiGML Player application.

    Sends SiGML XML to the avatar player via TCP socket.
    Can optionally auto-launch the player if not running.
    """

    def __init__(self, host: str = None, port: int = None,
                 auto_launch: bool = None):
        """
        Initialize CWASA player client.

        Args:
            host: Hostname where SiGML Player is running (default from config)
            port: TCP port (default from config)
            auto_launch: Attempt to launch player if not running (default from config)
        """
        self.host = host if host is not None else avatar_config.HOST
        self.port = port if port is not None else avatar_config.PORT
        self.auto_launch = auto_launch if auto_launch is not None else avatar_config.AUTO_LAUNCH
        self._player_process: Optional[subprocess.Popen] = None

    def is_player_running(self) -> bool:
        """
        Check if the SiGML Player is running and accepting connections.

        Returns:
            True if player is running and accepting connections
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                result = sock.connect_ex((self.host, self.port))
                return result == 0
        except socket.error:
            return False

    def launch_player(self, wait_for_ready: bool = True,
                      timeout: float = None) -> bool:
        """
        Launch the SiGML Player application.

        Args:
            wait_for_ready: Wait for player to accept connections
            timeout: Maximum time to wait for player to be ready (default from config)

        Returns:
            True if player was launched successfully
        """
        if timeout is None:
            timeout = avatar_config.LAUNCH_TIMEOUT

        if self.is_player_running():
            logger.info("SiGML Player is already running")
            return True

        player_path = Path(avatar_config.PLAYER_PATH)

        if not player_path.exists():
            logger.error(f"SiGML Player not found at {player_path}")
            logger.error("Run 'python scripts/setup_avatar.py' to download it")
            return False

        # Ensure executable
        if not os.access(player_path, os.X_OK):
            os.chmod(player_path, 0o755)

        try:
            logger.info(f"Launching SiGML Player from {player_path}")

            # Launch as background process
            self._player_process = subprocess.Popen(
                [str(player_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent process
            )

            if wait_for_ready:
                return self._wait_for_player(timeout)

            return True

        except OSError as e:
            logger.error(f"Failed to launch SiGML Player: {e}")
            return False

    def _wait_for_player(self, timeout: float) -> bool:
        """
        Wait for player to be ready to accept connections.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if player is ready
        """
        start_time = time.time()
        check_interval = 0.5

        while time.time() - start_time < timeout:
            if self.is_player_running():
                logger.info("SiGML Player is ready")
                return True
            time.sleep(check_interval)

        logger.warning(f"SiGML Player not ready after {timeout}s")
        return False

    def send_sigml(self, sigml_xml: str) -> bool:
        """
        Send SiGML XML to the avatar player.

        Protocol:
        1. Connect to TCP port 8052
        2. Send SiGML as UTF-8 encoded bytes
        3. Close connection

        Args:
            sigml_xml: Complete SiGML XML string

        Returns:
            True if SiGML was sent successfully
        """
        # Auto-launch if needed
        if self.auto_launch and not self.is_player_running():
            if not self.launch_player():
                raise CWASAPlayerError("Could not launch SiGML Player")

        if not self.is_player_running():
            raise CWASAPlayerError(
                f"SiGML Player not running on {self.host}:{self.port}")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(avatar_config.CONNECTION_TIMEOUT)
                sock.connect((self.host, self.port))

                # Send SiGML as UTF-8
                sock.settimeout(avatar_config.SEND_TIMEOUT)
                data = sigml_xml.encode('utf-8')
                sock.sendall(data)

                logger.debug(f"Sent {len(data)} bytes of SiGML to player")
                return True

        except socket.timeout:
            logger.error("Timeout sending SiGML to player")
            raise CWASAPlayerError("Timeout communicating with SiGML Player")

        except socket.error as e:
            logger.error(f"Socket error sending SiGML: {e}")
            raise CWASAPlayerError(f"Failed to send SiGML: {e}")

    def send_sigml_file(self, filepath: str) -> bool:
        """
        Send SiGML from a file to the avatar player.

        Args:
            filepath: Path to .sigml file

        Returns:
            True if sent successfully
        """
        path = Path(filepath)
        if not path.exists():
            raise CWASAPlayerError(f"SiGML file not found: {filepath}")

        sigml_xml = path.read_text(encoding='utf-8')
        return self.send_sigml(sigml_xml)

    def stop_player(self):
        """Stop the SiGML Player if we launched it."""
        if self._player_process is not None:
            try:
                self._player_process.terminate()
                self._player_process.wait(timeout=5.0)
                logger.info("SiGML Player stopped")
            except subprocess.TimeoutExpired:
                self._player_process.kill()
                logger.warning("SiGML Player force-killed")
            finally:
                self._player_process = None


def play_sigml(sigml_xml: str, auto_launch: bool = True) -> bool:
    """
    Convenience function to play SiGML on the avatar.

    Args:
        sigml_xml: SiGML XML string to animate
        auto_launch: Launch player if not running

    Returns:
        True if successful
    """
    player = CWASAPlayer(auto_launch=auto_launch)
    return player.send_sigml(sigml_xml)


def test_connection() -> bool:
    """
    Test if CWASA player is available.

    Returns:
        True if player is running and accepting connections
    """
    player = CWASAPlayer(auto_launch=False)
    return player.is_player_running()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="CWASA Avatar Player Control")
    parser.add_argument('--test', action='store_true',
                        help="Test if player is running")
    parser.add_argument('--launch', action='store_true',
                        help="Launch the SiGML Player")
    parser.add_argument('--send', type=str, metavar='FILE',
                        help="Send a .sigml file to the player")
    parser.add_argument('--demo', action='store_true',
                        help="Send a demo SiGML to the player")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    player = CWASAPlayer()

    if args.test:
        if player.is_player_running():
            print("✓ SiGML Player is running")
        else:
            print("✗ SiGML Player is not running")
            if SIGML_PLAYER_PATH.exists():
                print(f"  Player available at: {SIGML_PLAYER_PATH}")
                print("  Run with --launch to start it")
            else:
                print(f"  Player not installed. Run: python scripts/setup_avatar.py")

    elif args.launch:
        if player.launch_player():
            print("✓ SiGML Player launched successfully")
        else:
            print("✗ Failed to launch SiGML Player")

    elif args.send:
        try:
            player.send_sigml_file(args.send)
            print(f"✓ Sent {args.send} to player")
        except CWASAPlayerError as e:
            print(f"✗ Error: {e}")

    elif args.demo:
        # Demo SiGML for "HELLO"
        demo_sigml = '''<?xml version="1.0" encoding="UTF-8"?>
<sigml>
    <hns_sign gloss="HELLO">
        <hamnosys_manual>hamflathand,hamextfingeru,hampalmout,hamshoulders,hammover,hamrepeat</hamnosys_manual>
    </hns_sign>
</sigml>'''
        try:
            player.send_sigml(demo_sigml)
            print("✓ Demo HELLO sign sent to player")
        except CWASAPlayerError as e:
            print(f"✗ Error: {e}")

    else:
        parser.print_help()
