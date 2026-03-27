#!/usr/bin/env bash
# my-net setup wizard bootstrap
# Usage: curl -sSL https://raw.githubusercontent.com/paulgibeault/my-net/main/install.sh | bash
# Or:    bash install.sh
set -euo pipefail

MYNET_DIR="$HOME/.mynet"
REPO_URL="https://github.com/paulgibeault/my-net.git"
REPO_BRANCH="main"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

# ── colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${CYAN}▶  $*${RESET}"; }
success() { echo -e "${GREEN}✓  $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠  $*${RESET}"; }
error()   { echo -e "${RED}✗  $*${RESET}"; }
bold()    { echo -e "${BOLD}$*${RESET}"; }

# ── banner ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}  ╔═══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}  ║          my-net  setup  wizard            ║${RESET}"
echo -e "${BOLD}${CYAN}  ║    sovereign cloud — self-hosted Bluesky  ║${RESET}"
echo -e "${BOLD}${CYAN}  ╚═══════════════════════════════════════════╝${RESET}"
echo ""

# ── Windows / WSL2 detection ─────────────────────────────────────────────────
detect_os() {
    local ostype
    ostype="$(uname -s 2>/dev/null || echo 'unknown')"

    case "$ostype" in
        Linux*)
            # Check if we're INSIDE WSL — that's fine!
            if grep -qi microsoft /proc/version 2>/dev/null; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        Darwin*)  echo "mac"     ;;
        CYGWIN*)  echo "windows" ;;
        MINGW*)   echo "windows" ;;
        MSYS*)    echo "windows" ;;
        *)
            # Last-ditch: check $OSTYPE env var (set by bash on some systems)
            case "${OSTYPE:-}" in
                cygwin*|msys*|win32) echo "windows" ;;
                *)                   echo "unknown"  ;;
            esac
            ;;
    esac
}

OS="$(detect_os)"

if [[ "$OS" == "windows" ]]; then
    echo ""
    error  "Native Windows is not supported."
    echo ""
    bold   "my-net requires WSL2 (Windows Subsystem for Linux)."
    echo   "WSL2 lets you run a real Linux environment inside Windows — it's built in,"
    echo   "free, and takes about 5 minutes to set up."
    echo ""
    bold   "── How to install WSL2 ──────────────────────────────"
    echo ""
    echo   "  1. Open PowerShell as Administrator:"
    echo   "     Right-click the Start button → 'Windows PowerShell (Admin)'"
    echo ""
    echo   "  2. Run this command:"
    echo -e "     ${YELLOW}wsl --install${RESET}"
    echo   "     (This installs WSL2 + Ubuntu automatically)"
    echo ""
    echo   "  3. Restart your computer when prompted."
    echo ""
    echo   "  4. After restart, Ubuntu will finish setting up."
    echo   "     Create a Linux username and password when asked."
    echo ""
    echo   "  5. Open the 'Ubuntu' app from your Start menu,"
    echo   "     then re-run this installer:"
    echo -e "     ${CYAN}curl -sSL https://raw.githubusercontent.com/paulgibeault/my-net/main/install.sh | bash${RESET}"
    echo ""
    bold   "─────────────────────────────────────────────────────"
    echo ""
    echo   "More info: https://learn.microsoft.com/windows/wsl/install"
    echo ""
    exit 0
fi

success "OS detected: $OS"

# ── Python version check ──────────────────────────────────────────────────────
check_python() {
    local py_cmd=""

    for cmd in python3 python3.12 python3.11 python3.10 python; do
        if command -v "$cmd" &>/dev/null; then
            local version
            version="$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)"
            local major minor
            major="${version%%.*}"
            minor="${version##*.}"
            if [[ "$major" -ge "$MIN_PYTHON_MAJOR" && "$minor" -ge "$MIN_PYTHON_MINOR" ]]; then
                echo "$cmd"
                return 0
            fi
        fi
    done

    return 1
}

info "Checking for Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+..."
if PY_CMD="$(check_python)"; then
    PY_VERSION="$("$PY_CMD" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
    success "Found Python $PY_VERSION at $(command -v "$PY_CMD")"
else
    error "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ not found."
    echo ""
    warn  "How to install Python:"
    if [[ "$OS" == "mac" ]]; then
        echo "  Option 1 (Homebrew):  brew install python3"
        echo "  Option 2 (official):  https://www.python.org/downloads/macos/"
    else
        echo "  Ubuntu/Debian:  sudo apt update && sudo apt install python3.12"
        echo "  Fedora/RHEL:    sudo dnf install python3.12"
        echo "  Official:       https://www.python.org/downloads/"
    fi
    echo ""
    exit 1
fi

# ── pip check ────────────────────────────────────────────────────────────────
info "Checking pip..."
if ! "$PY_CMD" -m pip --version &>/dev/null; then
    warn "pip not found — attempting to install..."
    if [[ "$OS" == "mac" ]]; then
        "$PY_CMD" -m ensurepip --upgrade 2>/dev/null || {
            error "Could not install pip. Try: brew install python3"
            exit 1
        }
    else
        "$PY_CMD" -m ensurepip --upgrade 2>/dev/null || \
        curl -sSL https://bootstrap.pypa.io/get-pip.py | "$PY_CMD" || {
            error "Could not install pip. Try: sudo apt install python3-pip"
            exit 1
        }
    fi
fi
success "pip available"

# ── git check ────────────────────────────────────────────────────────────────
info "Checking git..."
if ! command -v git &>/dev/null; then
    error "git is not installed."
    if [[ "$OS" == "mac" ]]; then
        echo "  Install with: brew install git  (or xcode-select --install)"
    else
        echo "  Install with: sudo apt install git"
    fi
    exit 1
fi
success "git available"

# ── clone / update repo ──────────────────────────────────────────────────────
info "Setting up my-net in $MYNET_DIR..."
mkdir -p "$MYNET_DIR"

if [[ -d "$MYNET_DIR/.git" ]]; then
    info "Repo already cloned — pulling latest..."
    git -C "$MYNET_DIR" fetch origin "$REPO_BRANCH" --quiet
    git -C "$MYNET_DIR" reset --hard "origin/$REPO_BRANCH" --quiet
    success "Updated to latest version"
else
    info "Cloning repository..."
    git clone --branch "$REPO_BRANCH" --depth 1 "$REPO_URL" "$MYNET_DIR"
    success "Repository cloned to $MYNET_DIR"
fi

# ── install Python dependencies ───────────────────────────────────────────────
info "Installing Python dependencies..."
"$PY_CMD" -m pip install --quiet --upgrade pip
"$PY_CMD" -m pip install --quiet -r "$MYNET_DIR/wizard/requirements.txt"
success "Dependencies installed"

# ── launch wizard ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}Everything is ready! Starting the wizard...${RESET}"
echo ""

cd "$MYNET_DIR" && exec "$PY_CMD" "wizard/main.py" "$@"
