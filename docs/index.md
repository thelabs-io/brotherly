# Brotherly

## Overview

A trust-based remote administration tool for brothers. Chris queues shell scripts on Matt's Mac Mini via SSH, and Matt reviews and approves them through a beautiful Textual TUI. All operations are logged and Chris gets notified of results via SMS and GNOME desktop notifications.

## Architecture

The system has two sides:

**Chris's side (z2 - Arch Linux):**
- Writes scripts that perform admin operations on Matt's machine
- Queues them via SSH: `brotherly queue path/to/script.sh`
- Receives notifications (SMS + GNOME) when Matt runs them

**Matt's side (matts-mini - macOS M4):**
- Runs `brotherly` to see what's queued
- Reviews description and optionally views source code
- Approves execution with a single keypress
- Output displayed in TUI and logged for Chris to review

## Documentation

### Architecture & Design
- [Architecture Overview](architecture.md) - System design, components, data flow
- [Technical Decisions](decisions.md) - Key architectural choices

### Development
- [Development Guide](development.md) - Setup and development workflow
