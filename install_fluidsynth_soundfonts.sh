#!/bin/bash
# Download FluidSynth soundfonts from GeekFunkLabs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOUNDFONT_DIR="$SCRIPT_DIR/soundfonts"

echo "Downloading soundfonts to: $SOUNDFONT_DIR"

mkdir -p "$SOUNDFONT_DIR"

wget -qO - --show-progress https://geekfunklabs.com/squishbox_soundfonts.tar.gz | tar -xzC "$SOUNDFONT_DIR" --skip-old-files

echo "Done."
