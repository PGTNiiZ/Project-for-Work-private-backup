# LinkSocial Dataset Provenance and Release Audit

## VERIFIED

- The authoritative public repository is `https://github.com/vishalshar/Dataset-LinkSocial`.
- Its README states that it contains the dataset used in *LINKSOCIAL: Linking User Profiles Across Multiple Social Media Platforms* by Vishal Sharma and Curtis E. Dyreson, IEEE ICBK 2018, pp. 260–267; IEEE record: `8588801`.
- The repository contains the same three raw-profile directory names used by this project: `1.profile.data`, `2.profile.data`, and `3.profile.data`.
- Public README statistics report 10,958 Instagram, 13,961 Twitter, and 11,892 Google+ profiles. The local derivative contains 10,957, 13,960, and 11,890 respectively, consistent with filtering/removal of a small number of rows.
- The public README lists profile fields: username, bio, full name, external URL, bi-grams, and profile-picture URLs for Instagram/Twitter.
- The local pipeline label is a shared entity folder/identifier across platform profiles; the raw repository folder layout is consistent with this label construction.

## LIKELY BUT UNVERIFIED

- The local corpus is a transformed derivative of the public Dataset-LinkSocial repository. File/folder naming and counts support this, but no full file-level checksum comparison was performed.
- The original publication likely describes collection and linkage methodology. This audit has verified the paper identity and public repository, but not extracted a definitive collection-period, consent, or methodology statement from the IEEE full text.

## NOT FOUND

- A `LICENSE` file in the public Dataset-LinkSocial repository.
- An SPDX/GitHub repository license: the GitHub API returns `license: null`.
- Explicit redistribution permission.
- Explicit reuse conditions beyond “If you use our dataset please cite it.”
- Collection period, crawler implementation, platform Terms-of-Service compliance statement, ethics/IRB statement, consent statement, or data-subject notification mechanism.

## PUBLICATION RISK

Moderate to high. Dataset source and citation are now verified, but legal/ethical-use conditions are not. Public hosting is not equivalent to a reuse or redistribution license.

Safe manuscript wording:

“Experiments use a locally transformed derivative of the public LinkSocial profile corpus, originally released with Sharma and Dyreson’s IEEE ICBK publication. Because the source repository does not state a machine-readable reuse license or formal ethics documentation, this study does not redistribute raw records and limits reproducibility materials to code, configuration, cryptographic hashes, aggregate results, and non-identifying error categories.”

## DATA RELEASE RISK

Do not release raw usernames, full names, biographies, locations, external URLs, profile-image URLs/images, `user_folder`, pair identifiers, or raw decision files. Publish only code where permitted, derived schemas, run configuration, source hashes, aggregate metrics, and anonymized failure-category counts. Confirm ICSEC’s artifact/data policy and obtain written permission from the dataset maintainers before releasing any data-derived artifact beyond aggregates.
