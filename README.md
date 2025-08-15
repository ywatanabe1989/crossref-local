<!-- ---
!-- Timestamp: 2025-08-15 10:21:06
!-- Author: ywatanabe
!-- File: /mnt/nas_ug/crossref_local/README.md
!-- --- -->

# CrossRef 2025 Public Data

## Download Json files
https://academictorrents.com/details/e0eda0104902d61c025e27e4846b66491d4c9f98

``` bash
nohup aria2c \
	--continue=true \
	--check-integrity=true \
	--max-connection-per-server=16 \
	--split=16 \
	--save-session=aria2.session \
	--save-session-interval=30 \
	--log=aria2-resume.log "March2025PublicDataFilefromCrossref-e0eda0104902d61c025e27e4846b66491d4c9f98.torrent" &
```

#### Verification

``` bash
n_json_gz_files_provided=33402
n_json_gz_files_actual=$(find "March 2025 Public Data File from Crossref" -type f | wc -l)
if [ $n_json_gz_files_provided = $n_json_gz_files_actual ]; then
    echo "Successfully downloaded all the .json.gz files in March 2025 Public Data File from Crossref"
else
    echo "Downloaded failed or not complete for all the .json.gz files in March 2025 Public Data File from Crossref"
fi
```

## GitLab/GitHub Setup

``` bash
SSH_KEY_GITLAB="$HOME/.ssh/gitlab"
SSH_KEY_GITHUB="$HOME/.ssh/gitlab"

# Generate ssh keys
ssh-keygen -t rsa -b 2048 -f "$SSH_KEY_GITLAB"
ssh-keygen -t rsa -b 2048 -f "$SSH_KEY_GITHUB"

# Add the pub contents to GitLab through web browser
cat "$SSH_KEY_GITLAB".pub
cat "$SSH_KEY_GITHUB".pub

# Fix private key permissions
chmod 600 "$SSH_KEY_GITLAB"
chmod 644 "$SSH_KEY_GITLAB".pub
chmod 600 "$SSH_KEY_GITHUB"
chmod 644 "$SSH_KEY_GITHUB".pub
chmod 700 ~/.ssh

# Check the connection
ssh -T git@gitlab.com -i "$SSH_KEY_GITLAB"
ssh -T git@github.com -i "$SSH_KEY_GITHUB"
```

## Jsons to sqlite3 db

``` bash
git clone https://gitlab.com/crossref/labs/dois2sqlite.git
# Edit the dois2sqlite as in this repository
```

## To Database

``` bash
cd /path/to/dois2sqlite
python3.11 -m venv .env && source .env/bin/activate && pip install -e dois2sqlite/

# Create database
dois2sqlite create ./data/crossref.db

# Load all JSONL files
dois2sqlite load "./data/March 2025 Public Data File from Crossref" ./data/crossref.db --n-jobs 8 --commit-size 100000

# Create indexes
dois2sqlite index /mnt/nas_ug/crossref_local/crossref.db
```

## Run as a Service

``` bash
git clone https://gitlab.com/crossref/labs/labs-data-file-api.git
# Edit the dois2sqlite as in this repository
cd /path/to/labs-data-file-api
python3 -m venv .env && source .env/bin/activate && pip install -r requirements.txt
ln -s ../data/crossref.db crossref.db
python3 manage.py migrate
python3 manage.py runserver
python main.py index-all-with-location --data-directory "../data/March 2025 Public Data File from Crossref"
curl http://127.0.0.1:8000/api/lookup/10.1000/182
```

## References
https://www.crossref.org/learning/public-data-file/
https://academictorrents.com/browse.php?search=Crossref
https://gitlab.com/crossref/labs/dois2sqlite
https://gitlab.com/crossref/labs/labs-data-file-api

## Contact
Yusuke Watanabe (ywatanabe@scitex.ai)

<!-- EOF -->