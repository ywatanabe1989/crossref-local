# Installing Apptainer on UGreen NAS

**IMPORTANT:** The `singularity` package in apt repositories is a GAME, not the container system!
You need **Apptainer** (the new name for Singularity container system).

## Quick Installation (Recommended)

### Method 1: Install from Official .deb Package

```bash
# Download Apptainer
cd /tmp
wget https://github.com/apptainer/apptainer/releases/download/v1.3.0/apptainer_1.3.0_amd64.deb

# Install
sudo dpkg -i apptainer_1.3.0_amd64.deb

# Fix any dependency issues
sudo apt-get install -f

# Verify installation
apptainer --version
# Should show: apptainer version 1.3.0
```

### Method 2: Use Pre-built Binary

```bash
# Download binary
cd /usr/local/bin
sudo wget https://github.com/apptainer/apptainer/releases/download/v1.3.0/apptainer_1.3.0_amd64.deb
sudo chmod +x apptainer

# Verify
apptainer --version
```

### Method 3: Build Apptainer Image Using Docker (No Apptainer Installation Needed!)

If you can't install Apptainer, use Docker to build the image:

```bash
cd /mnt/nas_ug/crossref_local/impact_factor

# Use Docker to build Apptainer/Singularity image
docker run --rm --privileged \
  -v $(pwd):/work \
  -w /work \
  quay.io/singularity/singularity:v3.11.0 \
  build impact_factor.sif impact_factor.def

# Now you can run with Singularity (if available) or convert to Docker
# Run with singularity (if available)
singularity run --bind /mnt/nas_ug/crossref_local/data:/data:ro \
  impact_factor.sif --journal "Nature" --year 2023
```

## What You Accidentally Installed

If you ran `sudo apt install singularity`, you installed **Singularity the game**, not the container platform.

To remove it:
```bash
sudo apt remove singularity singularity-music python3-pygame
sudo apt autoremove
```

## Why This Confusion Exists

- **Singularity (container)** was renamed to **Apptainer** in 2021
- **Singularity (game)** is a different project that happens to have the same name
- Debian/Ubuntu repos have the game, not the container system
- You must install Apptainer from official releases

## After Installation

Test your installation:
```bash
cd /mnt/nas_ug/crossref_local/impact_factor

# Build image
./build_apptainer.sh

# Run calculation
./run_apptainer.sh --journal "Nature" --year 2023
```

## Alternative: Just Use Docker

If Apptainer installation is problematic, Docker works perfectly fine:

```bash
cd /mnt/nas_ug/crossref_local/impact_factor

# Build Docker image
docker build -t impact-factor-calculator .

# Run
./run_docker.sh --journal "Nature" --year 2023
```

## Alternative: Direct Python Execution

Simplest approach - no containers:

```bash
cd /mnt/nas_ug/crossref_local/impact_factor

# Install dependencies
pip install numpy

# Run directly
python calculate_if.py --journal "Nature" --year 2023
```

This requires only Python and numpy, no containers needed!
