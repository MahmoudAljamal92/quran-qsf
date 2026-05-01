QSF — OpenTimestamps (Bitcoin blockchain anchor)
================================================

Goal: turn the GitHub release commit hash into a free, Bitcoin-blockchain-anchored, court-admissible timestamp. Total cost: $0. Total time: 5 minutes active + 1 hour waiting.

Step 1 — Push to GitHub first
-----------------------------
Do the GitHub steps (see `../github/README.md`). Do not continue here until `git push -u origin main` completed.

Step 2 — Write the commit hash to release_commit.txt
----------------------------------------------------
PowerShell:

    cd C:\Users\mtj_2\OneDrive\Desktop\Quran
    git rev-parse HEAD | Out-File -Encoding ASCII _release\opentimestamps\release_commit.txt

Check the file:
    type _release\opentimestamps\release_commit.txt
It should contain a single 40-hex-character line, e.g.  a3b4c5d6e7f8...

Step 3 — Install the OpenTimestamps client
------------------------------------------
PowerShell (one-shot):

    pip install opentimestamps-client

Step 4 — Stamp the file
-----------------------
    cd C:\Users\mtj_2\OneDrive\Desktop\Quran\_release\opentimestamps
    ots stamp release_commit.txt

This creates `release_commit.txt.ots` next to it. The stamp is submitted to OpenTimestamps calendars immediately but the Bitcoin block confirmation takes ~1 hour.

Step 5 — Wait 1 hour, then upgrade
----------------------------------
    ots upgrade release_commit.txt.ots

After this succeeds, the .ots file is anchored to a specific Bitcoin block — permanent and verifiable by anyone, anywhere, forever.

Step 6 — Commit the .ots proof back into the repo
-------------------------------------------------
    cd C:\Users\mtj_2\OneDrive\Desktop\Quran
    git add _release/opentimestamps/release_commit.txt _release/opentimestamps/release_commit.txt.ots
    git commit -m "Add OpenTimestamps Bitcoin-anchored proof of release commit"
    git push

Now anyone in the future can run:
    ots verify _release/opentimestamps/release_commit.txt.ots
and receive cryptographic confirmation that this exact commit hash existed on this exact date, anchored to a specific Bitcoin block. No trusted third party required.

Optional belt-and-braces
------------------------
Also post the commit hash + GitHub URL + OSF DOI in one tweet / Mastodon post. The Internet Archive (archive.org/wayback) auto-captures popular posts within hours, giving a third independent time-witness.

Why this matters
----------------
Three independent time-witnesses (OSF DOI, arXiv ID, Bitcoin via OTS) make priority disputes structurally impossible. Anyone claiming prior art would have to prove their own timestamp is earlier than all three — extremely hard.
