#!/usr/bin/env python3
"""
Update manifest.json version to match Git tag version.
This script is used by the release workflow to ensure version consistency.
"""

import json
import sys
import os
from pathlib import Path

def update_manifest_version(manifest_path: str, new_version: str) -> bool:
    """
    Update the version field in manifest.json.
    
    Args:
        manifest_path: Path to the manifest.json file
        new_version: New version string to set
        
    Returns:
        True if version was updated, False if already matches
    """
    try:
        # Read current manifest
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Check current version
        current_version = manifest.get('version', 'unknown')
        print(f"📋 Current version: {current_version}")
        print(f"🏷️  New version: {new_version}")
        
        # Update if different
        if current_version != new_version:
            manifest['version'] = new_version
            
            # Write back with proper formatting
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
                f.write('\n')  # Add trailing newline
            
            print(f"✅ Version updated from {current_version} to {new_version}")
            return True
        else:
            print(f"ℹ️  Version already matches ({new_version})")
            return False
            
    except FileNotFoundError:
        print(f"❌ Error: Manifest file not found at {manifest_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in manifest file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error updating manifest: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    # Get version from environment or argument
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        version = os.environ.get('VERSION', '').strip()
    
    if not version:
        print("❌ Error: No version provided")
        print("Usage: python update-manifest-version.py <version>")
        print("   or: VERSION=<version> python update-manifest-version.py")
        sys.exit(1)
    
    # Remove 'v' prefix if present
    if version.startswith('v'):
        version = version[1:]
    
    # Path to manifest
    manifest_path = Path(__file__).parent.parent / 'custom_components' / 'petkit_ble' / 'manifest.json'
    
    # Update version
    updated = update_manifest_version(str(manifest_path), version)
    
    # Exit with appropriate code
    sys.exit(0 if updated or not updated else 1)

if __name__ == "__main__":
    main()