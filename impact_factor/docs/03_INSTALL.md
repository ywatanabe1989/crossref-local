# Installation Guide - Impact Factor Calculator

## System Requirements

- CrossRef local database at `/mnt/nas_ug/crossref_local/data/crossref.db` (1.1TB)
- Python 3.11+ (for direct execution)
- Docker (for containerized execution)
- Apptainer/Singularity (optional, for HPC environments)

## Installation Options

### Option 1: Direct Python Execution (Simplest)

**Prerequisites:**
```bash
# Install Python dependencies
pip install numpy
```

**Run directly:**
```bash
cd /mnt/nas_ug/crossref_local/impact_factor
python calculate_if.py --journal "Nature" --year 2023
```

**Pros:** Fastest, no container overhead
**Cons:** Requires Python environment setup

---

### Option 2: Docker (Recommended for Isolated Environment)

**Build image:**
```bash
cd /mnt/nas_ug/crossref_local/impact_factor
docker build -t impact-factor-calculator .
```

**Run with convenience script:**
```bash
./run_docker.sh --journal "Nature" --year 2023
```

**Or run directly:**
```bash
docker run --rm \
  -v /mnt/nas_ug/crossref_local/data:/data:ro \
  -v $(pwd)/output:/output \
  impact-factor-calculator \
  python calculate_if.py --journal "Nature" --year 2023
```

**Pros:** Isolated environment, reproducible
**Cons:** Requires Docker daemon

---

### Option 3: Apptainer/Singularity (Best for HPC/No Root Access)

#### Installing Apptainer on UGreen NAS

**Method 1: From official releases (recommended)**
```bash
# Download latest Apptainer release
cd /tmp
wget https://github.com/apptainer/apptainer/releases/download/v1.2.5/apptainer_1.2.5_amd64.deb

# Install (requires sudo)
sudo dpkg -i apptainer_1.2.5_amd64.deb

# Verify installation
apptainer --version
```

**Method 2: Using Docker to build Apptainer image**
```bash
cd /mnt/nas_ug/crossref_local/impact_factor

# Use Docker to build Apptainer image (no apptainer installation needed)
docker run --rm --privileged \
  -v $(pwd):/work -w /work \
  quay.io/singularity/singularity:v3.11.0 \
  build impact_factor.sif impact_factor.def
```

**Method 3: Build from source**
```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev uuid-dev libgpgme-dev \
    squashfs-tools libseccomp-dev wget pkg-config git cryptsetup-bin

# Download and build
export VERSION=1.2.5
wget https://github.com/apptainer/apptainer/releases/download/v${VERSION}/apptainer-${VERSION}.tar.gz
tar -xzf apptainer-${VERSION}.tar.gz
cd apptainer-${VERSION}

./mconfig
make -C builddir
sudo make -C builddir install
```

#### Using Apptainer

**Build image:**
```bash
cd /mnt/nas_ug/crossref_local/impact_factor
./build_apptainer.sh
```

**Run with convenience script:**
```bash
./run_apptainer.sh --journal "Nature" --year 2023
```

**Or run directly:**
```bash
apptainer run \
  --bind /mnt/nas_ug/crossref_local/data:/data:ro \
  --bind $(pwd)/output:/output \
  impact_factor.sif \
  --journal "Nature" --year 2023
```

**Pros:** No root needed to run, HPC-friendly, secure
**Cons:** Requires sudo to build (or use Docker method)

---

## Quick Start After Installation

### 1. Test the Installation

**Python:**
```bash
cd /mnt/nas_ug/crossref_local/impact_factor
python test_calculator.py
```

**Docker:**
```bash
docker run --rm \
  -v /mnt/nas_ug/crossref_local/data:/data:ro \
  impact-factor-calculator \
  python test_calculator.py
```

**Apptainer:**
```bash
apptainer exec \
  --bind /mnt/nas_ug/crossref_local/data:/data:ro \
  impact_factor.sif \
  python /app/test_calculator.py
```

### 2. Run Your First Calculation

```bash
# Calculate Nature's 2023 impact factor
python calculate_if.py --journal "Nature" --year 2023

# Or with container
./run_docker.sh --journal "Nature" --year 2023
./run_apptainer.sh --journal "Nature" --year 2023
```

### 3. Create Output Directory

```bash
mkdir -p output
```

### 4. Calculate and Save Results

```bash
python calculate_if.py \
  --journal "Nature" \
  --year 2020-2024 \
  --moving-avg 3 \
  --output output/nature_if.csv
```

---

## Performance Optimization

### Add Database Indexes (Recommended)

These indexes significantly speed up queries:

```bash
sqlite3 /mnt/nas_ug/crossref_local/data/crossref.db <<'EOF'
CREATE INDEX IF NOT EXISTS idx_container_title
  ON works(json_extract(metadata, '$.container-title[0]'));
CREATE INDEX IF NOT EXISTS idx_issn
  ON works(json_extract(metadata, '$.ISSN[0]'));
CREATE INDEX IF NOT EXISTS idx_published_year
  ON works(json_extract(metadata, '$.published.date-parts[0][0]'));
CREATE INDEX IF NOT EXISTS idx_doi_lookup
  ON works(doi);
EOF
```

**Note:** Index creation will take some time (hours) due to the large database size, but queries will be much faster afterward.

---

## Troubleshooting

### "Database not found"
```bash
# Verify database exists
ls -lh /mnt/nas_ug/crossref_local/data/crossref.db

# Check permissions
stat /mnt/nas_ug/crossref_local/data/crossref.db
```

### "No articles found"
```bash
# Test database connectivity
python test_calculator.py

# Try with ISSN instead of journal name
python calculate_if.py --issn "0028-0836" --year 2023
```

### Docker permission errors
```bash
# Run with your user ID
docker run --rm --user $(id -u):$(id -g) \
  -v /mnt/nas_ug/crossref_local/data:/data:ro \
  -v $(pwd)/output:/output \
  impact-factor-calculator \
  python calculate_if.py --journal "Nature" --year 2023
```

### Apptainer build fails
```bash
# Use Docker to build instead
docker run --rm --privileged \
  -v $(pwd):/work -w /work \
  quay.io/singularity/singularity:v3.11.0 \
  build impact_factor.sif impact_factor.def
```

---

## Remote Execution from Local Machine

Since the NAS is accessible via SSH:

```bash
# Run via SSH
ssh ugreen-nas "cd /mnt/nas_ug/crossref_local/impact_factor && \
  python calculate_if.py --journal 'Nature' --year 2023"

# Run in background
ssh ugreen-nas "cd /mnt/nas_ug/crossref_local/impact_factor && \
  nohup python calculate_if.py --journal 'Nature' --year 2020-2024 \
  --output output/nature.csv > nature.log 2>&1 &"

# Check progress
ssh ugreen-nas "tail -f /mnt/nas_ug/crossref_local/impact_factor/nature.log"
```

---

## Next Steps

1. Read [USAGE.md](USAGE.md) for detailed usage examples
2. Run [test_calculator.py](test_calculator.py) to verify installation
3. Try calculating IF for your favorite journal
4. Compare with JCR data using [compare_with_jcr.py](compare_with_jcr.py)

For questions or issues, refer to the troubleshooting section above.
