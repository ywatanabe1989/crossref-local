<!-- ---
!-- Timestamp: 2025-08-22 19:45:15
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
# ssh ugreen-nas
git clone https://gitlab.com/crossref/labs/labs-data-file-api.git
# Edit the dois2sqlite as in this repository
cd /path/to/labs-data-file-api # cd ~/crossref_local/labs-data-file-api/
python3 -m venv .env && source .env/bin/activate && pip install -r requirements.txt
ln -s ../data/crossref.db crossref.db
python3 manage.py migrate

python main.py index-all-with-location --data-directory "../data/March 2025 Public Data File from Crossref"
# sqlite3 crossref.db "SELECT COUNT(*) FROM crossrefDataFile_dataindexwithlocation;" # 167008748
# sqlite3 crossref.db "SELECT doi FROM crossrefDataFile_dataindexwithlocation LIMIT 5;"
# 10.1001/.387
# 10.1001/.389
# 10.1001/.391
# 10.1001/.399
# 10.1001/.404
# (.env) ywatanabe@DXP480TPLUS-994:~/crossref_local/labs-data-file-api$ 
python3 manage.py runserver 0.0.0.0:3333

# Usage:
curl "http://127.0.0.1:3333/api/search/?doi=10.1001/.387"
# {"DOI": "10.1001/.387", "ISSN": ["0003-9926"], "URL": "https://doi.org/10.1001/.387", "container-title": ["Archives of Internal Medicine"], "content-domain": {"crossmark-restriction": false, "domain": []}, "created": {"date-parts": [[2006, 2, 27]], "date-time": "2006-02-27T21:28:23Z", "timestamp": 1141075703000}, "deposited": {"date-parts": [[2016, 4, 21]], "date-time": "2016-04-21T12:21:44Z", "timestamp": 1461241304000}, "indexed": {"date-parts": [[2024, 2, 29]], "date-time": "2024-02-29T21:30:11Z", "timestamp": 1709242211235}, "is-referenced-by-count": 0, "issn-type": [{"type": "print", "value": "0003-9926"}], "issue": "4", "issued": {"date-parts": [[2006, 2, 27]]}, "journal-issue": {"issue": "4", "published-print": {"date-parts": [[2006, 2, 27]]}}, "language": "en", "member": "10", "page": "387-387", "prefix": "10.1001", "published": {"date-parts": [[2006, 2, 27]]}, "published-print": {"date-parts": [[2006, 2, 27]]}, "publisher": "American Medical Association (AMA)", "reference-count": 0, "references-count": 0, "resource": {"primary": {"URL": "http://archinte.ama-assn.org/cgi/doi/10.1001/.387"}}, "score": 0.0, "short-container-title": ["Archives of Internal Medicine"], "source": "Crossref", "title": ["In This Issue of Archives of Internal Medicine"], "type": "journal-article", "volume": "166"}

curl "http://127.0.0.1:3333/api/search/?title=deep%20learning&year=1979"
# {"results": [{"doi": "10.1001/archderm.115.10.1169", "year": 1979}, {"doi": "10.1001/archderm.115.10.1171", "year": 1979}]}

curl "http://127.0.0.1:3333/api/search/?authors=smith&year=2020"
# {"results": [{"doi": "10.1001/amajethics.2020.10", "title": "How Should Clinicians Integrate Mental Health Into Epidemic Responses?"}, {"doi": "10.1001/amajethics.2020.1004", "title": "Should a Patient Who Is Pregnant and Brain Dead Receive Life Support, Despite Objection From Her Appointed Surrogate?"}, {"doi": "10.1001/amajethics.2020.1010", "title": "How Educators Can Help Prevent False Brain Death Diagnoses"}, {"doi": "10.1001/amajethics.2020.1019", "title": "Reexamining the Flawed Legal Basis of the \u201cDead Donor Rule\u201d as a Foundation for Organ Donation Policy"}, {"doi": "10.1001/amajethics.2020.102", "title": "Can International Patent Law Help Mitigate Cancer Inequity in LMICs?"}, {"doi": "10.1001/amajethics.2020.1025", "title": "AMA Code of Medical Ethics'  Opinions About End-of-Life Care and Death"}, {"doi": "10.1001/amajethics.2020.1027", "title": "Inconsistency in Brain Death Determination Should Not Be Tolerated"}, {"doi": "10.1001/amajethics.2020.1033", "title": "Guidance for Physicians Who Wish to Influence Policy Development on Determination of Death by Neurologic Criteria"}, {"doi": "10.1001/amajethics.2020.1038", "title": "What Should We Do About the Mismatch Between Legal Criteria for Death and How Brain Death Is Diagnosed?"}, {"doi": "10.1001/amajethics.2020.1047", "title": "What Does the Public Need to Know About Brain Death?"}]}
curl "http://127.0.0.1:3333/api/search/?title=Archives&year=2006&authors=smith"
# {"results": [{"doi": "10.1001/.387", "title": "In This Issue of Archives of Internal Medicine", "year": 2006}]}
```

## References
https://www.crossref.org/learning/public-data-file/
https://academictorrents.com/browse.php?search=Crossref
https://gitlab.com/crossref/labs/dois2sqlite
https://gitlab.com/crossref/labs/labs-data-file-api

## Contact
Yusuke Watanabe (ywatanabe@scitex.ai)

<!-- EOF -->