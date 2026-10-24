# Dataset Provenance Status

## Verified from repository evidence

- The primary profile file is `data_for_project/normalized_profiles_with_profile_id.csv`.
- The repository describes the data as LinkSocial and the code references `Dataset-LinkSocial`.
- The dataset comprises public-profile fields from Twitter, Google+, and Instagram.
- A verified 2024 UIL review identifies `LinkSocial: Linking User Profiles Across Multiple Social Media Platforms` as a 2018 IEEE ICBK work by Vishal Sharma and Craig Dyreson, and describes an Instagram–Twitter–Google+ dataset.

## Not verified

The repository contains no authoritative copy of:

- the original LinkSocial dataset landing page or archival identifier;
- dataset license;
- collection dates;
- collection procedure or crawler configuration;
- original ethics/IRB statement;
- platform terms-of-use compliance statement;
- consent mechanism;
- public redistribution permission for profiles, images, or raw text.

Status: **[DATASET PROVENANCE REQUIRES VERIFICATION]**.

## Publication consequence

The manuscript may state only that the study evaluates a locally available derivative of the LinkSocial Twitter–Google+–Instagram profile corpus, with labels represented by shared entity identifiers. It must not claim legal redistribution, consent, or ethical clearance without source evidence.

Before submission, obtain and archive the original Sharma and Dyreson (2018) publication, its dataset-access instructions, and any applicable license/terms statement. If this cannot be verified, the paper should:

1. avoid releasing raw profile records, images, profile text, or pair identifiers;
2. release only code, configuration, hashes, aggregate tables, and anonymized failure categories if permitted;
3. add an explicit data-availability and ethics limitation; and
4. treat restricted reproducibility as a material threat to external reproducibility.
