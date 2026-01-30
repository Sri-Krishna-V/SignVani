#!/usr/bin/env python3
"""
Avatar Setup Script

Downloads and configures the CWASA SiGML Player for sign language avatar rendering.
Supports Linux (including Raspberry Pi), macOS, and Windows.

Reference: https://vhg.cmp.uea.ac.uk/tech/jas/std/
"""

import logging
import os
import platform
import stat
import sys
import urllib.request
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# DOWNLOAD URLS
# =============================================================================

DOWNLOAD_URLS = {
    'linux': 'https://vhg.cmp.uea.ac.uk/tech/jas/std/app/SiGML-Player.AppImage',
    'darwin_arm64': 'https://vhg.cmp.uea.ac.uk/tech/jas/std/app/SiGML-Player.arm64.dmg',
    'darwin_x64': 'https://vhg.cmp.uea.ac.uk/tech/jas/std/app/SiGML-Player.x64.dmg',
    'windows': 'https://vhg.cmp.uea.ac.uk/tech/jas/std/app/SiGML-Player.exe',
}

# Installation paths
BIN_DIR = project_root / 'bin'
INSTALL_PATHS = {
    'linux': BIN_DIR / 'SiGML-Player.AppImage',
    'darwin': BIN_DIR / 'SiGML-Player.dmg',
    'windows': BIN_DIR / 'SiGML-Player.exe',
}


def get_system_info() -> tuple:
    """
    Get current system information.

    Returns:
        Tuple of (system, machine) e.g., ('linux', 'x86_64') or ('darwin', 'arm64')
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ('x86_64', 'amd64'):
        machine = 'x64'
    elif machine in ('aarch64', 'arm64'):
        machine = 'arm64'
    elif machine.startswith('arm'):
        machine = 'arm'

    return system, machine


def get_download_url() -> tuple:
    """
    Get the appropriate download URL for the current system.

    Returns:
        Tuple of (url, local_path) or (None, None) if unsupported
    """
    system, machine = get_system_info()
    logger.info(f"Detected system: {system} ({machine})")

    if system == 'linux':
        return DOWNLOAD_URLS['linux'], INSTALL_PATHS['linux']

    elif system == 'darwin':
        if machine == 'arm64':
            return DOWNLOAD_URLS['darwin_arm64'], INSTALL_PATHS['darwin']
        else:
            return DOWNLOAD_URLS['darwin_x64'], INSTALL_PATHS['darwin']

    elif system == 'windows':
        return DOWNLOAD_URLS['windows'], INSTALL_PATHS['windows']

    else:
        logger.error(f"Unsupported system: {system}")
        return None, None


def download_with_progress(url: str, dest_path: Path) -> bool:
    """
    Download a file with progress indication.

    Args:
        url: URL to download
        dest_path: Local path to save file

    Returns:
        True if download successful
    """
    # Ensure parent directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading from: {url}")
    logger.info(f"Saving to: {dest_path}")

    try:
        # Create request with user agent
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'SignVani/1.0'}
        )

        with urllib.request.urlopen(request, timeout=60) as response:
            total_size = response.getheader('Content-Length')
            if total_size:
                total_size = int(total_size)
                logger.info(f"File size: {total_size / (1024*1024):.1f} MB")

            # Download with progress
            downloaded = 0
            block_size = 8192
            last_percent = 0

            with open(dest_path, 'wb') as f:
                while True:
                    block = response.read(block_size)
                    if not block:
                        break
                    f.write(block)
                    downloaded += len(block)

                    if total_size:
                        percent = int(100 * downloaded / total_size)
                        if percent >= last_percent + 10:
                            print(f"  Progress: {percent}%", flush=True)
                            last_percent = percent

        logger.info("Download complete")
        return True

    except urllib.error.URLError as e:
        logger.error(f"Download failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return False


def make_executable(path: Path) -> bool:
    """
    Make a file executable (Linux/macOS).

    Args:
        path: Path to file

    Returns:
        True if successful
    """
    try:
        current_mode = path.stat().st_mode
        path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        logger.info(f"Set executable permissions on {path}")
        return True
    except OSError as e:
        logger.error(f"Failed to set permissions: {e}")
        return False


def verify_installation(path: Path) -> bool:
    """
    Verify the installation is valid.

    Args:
        path: Path to installed file

    Returns:
        True if installation looks valid
    """
    if not path.exists():
        return False

    # Check file size (should be at least 50MB for Electron app)
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb < 10:
        logger.warning(f"File seems too small ({size_mb:.1f} MB)")
        return False

    logger.info(f"Installation verified: {path} ({size_mb:.1f} MB)")
    return True


def setup_avatar() -> bool:
    """
    Main setup function.

    Downloads and configures the SiGML Player for the current platform.

    Returns:
        True if setup successful
    """
    print("\n" + "=" * 60)
    print("SignVani Avatar Setup")
    print("=" * 60 + "\n")

    system, machine = get_system_info()
    print(f"System: {system} ({machine})")

    # Get download URL
    url, dest_path = get_download_url()

    if url is None:
        print(f"\n✗ Unsupported platform: {system} {machine}")
        print("  CWASA SiGML Player supports: Linux, macOS, Windows")
        return False

    # Check if already installed
    if dest_path.exists() and verify_installation(dest_path):
        print(f"\n✓ SiGML Player already installed at:")
        print(f"  {dest_path}")
        print("\n  To reinstall, delete the file and run this script again.")
        return True

    # Download
    print(f"\nDownloading SiGML Player...")
    if not download_with_progress(url, dest_path):
        print(f"\n✗ Download failed")
        return False

    # Make executable on Unix systems
    if system in ('linux', 'darwin'):
        make_executable(dest_path)

    # Verify
    if not verify_installation(dest_path):
        print(f"\n✗ Installation verification failed")
        return False

    # Platform-specific instructions
    print("\n" + "=" * 60)
    print("Installation Complete!")
    print("=" * 60)

    if system == 'linux':
        print(f"""
✓ SiGML Player installed successfully

To launch manually:
  {dest_path}

To use in SignVani pipeline:
  The avatar player will be launched automatically when needed.

Note: On first run, you may need to allow the AppImage in your
      security settings. Some systems require FUSE for AppImages:
      sudo apt-get install libfuse2
""")

    elif system == 'darwin':
        print(f"""
✓ SiGML Player DMG downloaded

To install on macOS:
  1. Open {dest_path}
  2. Drag SiGML-Player to Applications
  3. Right-click the app and select 'Open' to bypass Gatekeeper
""")

    elif system == 'windows':
        print(f"""
✓ SiGML Player installer downloaded

To install on Windows:
  1. Run {dest_path}
  2. Follow the installer prompts
  3. You may need to bypass Windows SmartScreen
""")

    return True


def check_dependencies():
    """Check system dependencies for running the avatar."""
    system, _ = get_system_info()

    if system == 'linux':
        # Check for FUSE (required for AppImage)
        fuse_check = os.path.exists('/dev/fuse')
        if not fuse_check:
            print("\n⚠ Warning: FUSE may not be installed")
            print("  AppImages require FUSE to run.")
            print("  Install with: sudo apt-get install libfuse2")

        # Check for display server
        display = os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
        if not display:
            print("\n⚠ Warning: No display server detected")
            print("  The avatar player requires a graphical environment.")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Setup CWASA SiGML Player")
    parser.add_argument('--check', action='store_true',
                        help="Check if player is installed")
    parser.add_argument('--deps', action='store_true',
                        help="Check system dependencies")
    args = parser.parse_args()

    if args.check:
        _, dest_path = get_download_url()
        if dest_path and dest_path.exists():
            print(f"✓ SiGML Player installed at: {dest_path}")
            sys.exit(0)
        else:
            print("✗ SiGML Player not installed")
            sys.exit(1)

    elif args.deps:
        check_dependencies()

    else:
        success = setup_avatar()
        sys.exit(0 if success else 1)
