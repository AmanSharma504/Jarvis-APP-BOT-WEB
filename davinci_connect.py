#!/usr/bin/env python3
"""
DaVinci Resolve Python Bridge & Connection Manager
Allows external Python scripts (and Jarvis) to connect to and automate DaVinci Resolve.
"""

import os
import sys
import platform
from typing import Any, Optional, Dict


def setup_environment() -> None:
    """Configures environment variables and sys.path for DaVinci Resolve Scripting API."""
    system = platform.system()

    if system == "Darwin":  # macOS
        script_api = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
        script_lib = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
    elif system == "Windows":
        program_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        program_files = os.environ.get("PROGRAMFILES", r"C:\Program Files")
        script_api = os.path.join(program_data, "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting")
        script_lib = os.path.join(program_files, "Blackmagic Design", "DaVinci Resolve", "fusionscript.dll")
    elif system == "Linux":
        script_api = "/opt/resolve/Developer/Scripting"
        script_lib = "/opt/resolve/libs/Fusion/fusionscript.so"
    else:
        raise OSError(f"Unsupported operating system: {system}")

    os.environ.setdefault("RESOLVE_SCRIPT_API", script_api)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", script_lib)

    modules_path = os.path.join(script_api, "Modules")
    if modules_path not in sys.path and os.path.isdir(modules_path):
        sys.path.append(modules_path)


class DaVinciConnection:
    """Manages connection and interaction with a running DaVinci Resolve instance."""

    def __init__(self, auto_connect: bool = True):
        setup_environment()
        self.resolve: Optional[Any] = None
        self.fusion: Optional[Any] = None
        self.dvr_script: Optional[Any] = None
        if auto_connect:
            self.connect()

    def connect(self) -> bool:
        """Attempts to connect to the active DaVinci Resolve instance."""
        try:
            import DaVinciResolveScript as dvr_script
            self.dvr_script = dvr_script
            self.resolve = dvr_script.scriptapp("Resolve")
            if self.resolve:
                self.fusion = self.resolve.Fusion()
                return True
            return False
        except ImportError as e:
            print(f"[DaVinciConnection] Failed to import DaVinciResolveScript: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[DaVinciConnection] Connection error: {e}", file=sys.stderr)
            return False

    def is_connected(self) -> bool:
        return self.resolve is not None

    def get_project_manager(self) -> Optional[Any]:
        if not self.resolve:
            return None
        return self.resolve.GetProjectManager()

    def get_current_project(self) -> Optional[Any]:
        pm = self.get_project_manager()
        if not pm:
            return None
        return pm.GetCurrentProject()

    def get_current_timeline(self) -> Optional[Any]:
        project = self.get_current_project()
        if not project:
            return None
        return project.GetCurrentTimeline()

    def get_media_pool(self) -> Optional[Any]:
        project = self.get_current_project()
        if not project:
            return None
        return project.GetMediaPool()

    def get_info(self) -> Dict[str, Any]:
        """Gathers summary information about the current Resolve session."""
        if not self.is_connected():
            return {"connected": False}

        info: Dict[str, Any] = {
            "connected": True,
            "product_name": self.resolve.GetProductName(),
            "version": self.resolve.GetVersionString(),
        }

        project = self.get_current_project()
        if project:
            info["current_project"] = project.GetName()
            timeline = project.GetCurrentTimeline()
            info["current_timeline"] = timeline.GetName() if timeline else None
            info["timeline_count"] = project.GetTimelineCount()
        else:
            info["current_project"] = None
            info["current_timeline"] = None

        return info


def check_and_print_status() -> None:
    print("=" * 60)
    print(" DaVinci Resolve Connection Diagnostic")
    print("=" * 60)

    conn = DaVinciConnection(auto_connect=False)
    setup_environment()

    # Step 1: Check scripting API library files
    api_dir = os.environ.get("RESOLVE_SCRIPT_API", "")
    lib_file = os.environ.get("RESOLVE_SCRIPT_LIB", "")

    print(f"[*] OS Platform        : {platform.system()} ({platform.machine()})")
    print(f"[*] Python Version     : {sys.version.split()[0]}")
    print(f"[*] Scripting API Dir  : {api_dir} ({'Found' if os.path.exists(api_dir) else 'NOT FOUND'})")
    print(f"[*] Scripting Library  : {lib_file} ({'Found' if os.path.exists(lib_file) else 'NOT FOUND'})")

    # Step 2: Try import
    try:
        import DaVinciResolveScript as dvr_script
        print("[+] DaVinciResolveScript module imported successfully.")
    except Exception as e:
        print(f"[-] Failed to import DaVinciResolveScript: {e}")
        return

    # Step 3: Connect
    connected = conn.connect()
    if connected:
        info = conn.get_info()
        print("\n[SUCCESS] Connected to DaVinci Resolve!")
        print(f"  • Product Name    : {info.get('product_name')}")
        print(f"  • Version         : {info.get('version')}")
        print(f"  • Current Project : {info.get('current_project') or 'No project currently open'}")
        if info.get("current_timeline"):
            print(f"  • Active Timeline : {info.get('current_timeline')}")
            print(f"  • Total Timelines : {info.get('timeline_count', 0)}")
    else:
        print("\n[NOTICE] DaVinci Resolve is currently NOT connected.")
        print("\nTo connect, please ensure:")
        print("  1. DaVinci Resolve is running.")
        print("  2. In DaVinci Resolve, verify External Scripting is enabled:")
        print("     -> Open DaVinci Resolve > Preferences (Cmd + ,)")
        print("     -> Select System tab > General")
        print("     -> Under 'External scripting using', select 'Local' (or 'Network')")
        print("     -> Click Save")
        print("  3. Make sure a project or the Project Manager is open in Resolve.")
        print("  4. Re-run this script once DaVinci Resolve is running.")
    print("=" * 60)


if __name__ == "__main__":
    check_and_print_status()
