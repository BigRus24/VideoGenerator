#!/bin/bash

#chmod +x install.sh
#./install.sh

# Define the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sudo apt -y update && sudo apt -y upgrade

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install a package using the appropriate package manager
install_package() {
    local package=$1
    if command_exists apt; then
        sudo apt update
        sudo apt install -y "$package"
    elif command_exists dnf; then
        sudo dnf install -y "$package"
    elif command_exists yum; then
        sudo yum install -y "$package"
    else
        echo "Supported package manager (apt, dnf, yum) not found. Please install $package manually."
        exit 1
    fi
}

# Install Python if not installed
if ! command_exists python3; then
    echo "Python 3 is not installed. Installing Python 3..."
    install_package python3
    install_package python3-venv
    install_package python3-pip
fi

# Check if pip is installed
if ! command_exists pip3; then
    echo "pip3 is not installed. Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py --user
    rm get-pip.py
fi

# Check if pipenv is installed, if not, install it
if ! command_exists pipenv; then
    echo "pipenv is not installed. Installing pipenv..."
    pip3 install --user pipenv
fi

# Check if ffmpeg is installed, if not, install it
if ! command_exists ffmpeg; then
    echo "ffmpeg is not installed. Installing ffmpeg..."
    install_package ffmpeg
fi

# Check if anacron is installed, if not, install it
if ! command_exists anacron; then
    echo "anacron is not installed. Installing anacron..."
    sudo dpkg --configure -a
    install_package anacron
fi

# Export PATH to include user-level bin directory
export PATH=$PATH:~/.local/bin

# Navigate to the project directory
cd "$PROJECT_DIR"

# Ensure Pipfile exists and install dependencies
if [ ! -f "Pipfile" ]; then
    echo "Creating Pipfile from requirements.txt..."
    pipenv install -r requirements.txt
    pipenv update
    pipenv upgrade
    pipenv clean
else
    echo "Pipfile already exists. Installing dependencies..."
    pipenv install
    pipenv update
    pipenv upgrade
    pipenv clean
fi

# Make run_short_script.sh and run_video_script.sh executable
chmod +x "$PROJECT_DIR/run_short_script.sh"
chmod +x "$PROJECT_DIR/run_video_script.sh"

# Function to add or update an anacron job
add_or_update_anacron_job() {
    local period=$1
    local delay=$2
    local identifier=$3
    local command=$4

    if ! grep -q "$identifier" /etc/anacrontab; then
        echo "$period $delay $identifier $command" | sudo tee -a /etc/anacrontab > /dev/null
    else
        sudo sed -i "s|.*$identifier.*|$period $delay $identifier $command|" /etc/anacrontab
    fi
}

# Set up the anacron job for run_short_script.sh
SHORT_SCRIPT_ANACRON="1 5 run_short_script $PROJECT_DIR/run_short_script.sh >> $PROJECT_DIR/short_log_file.log 2>&1"
add_or_update_anacron_job "1" "5" "run_short_script" "$PROJECT_DIR/run_short_script.sh >> $PROJECT_DIR/short_log_file.log 2>&1"

# Set up the anacron job for run_video_script.sh
VIDEO_SCRIPT_ANACRON="1 10 run_video_script $PROJECT_DIR/run_video_script.sh >> $PROJECT_DIR/video_log_file.log 2>&1"
add_or_update_anacron_job "1" "10" "run_video_script" "$PROJECT_DIR/run_video_script.sh >> $PROJECT_DIR/video_log_file.log 2>&1"

# Restart anacron to apply changes
sudo service anacron restart

sudo apt -y update && sudo apt -y upgrade

echo "Installation and anacron job setup completed successfully."
