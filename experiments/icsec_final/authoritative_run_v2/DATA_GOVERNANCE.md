# Data governance boundary (v2)

Verified in the root-cause audit: the local input is a transformed derivative of the public LinkSocial repository (Dataset-LinkSocial), whose README provides attribution and counts. A machine-readable reuse license, redistribution permission, collection methodology, platform Terms-of-Service compliance, consent/notification process, and ethics/IRB documentation were not verified.

This document does not claim consent, IRB approval, a formal license, or redistribution permission. Public hosting is not treated as permission to redistribute personal data.

Until written reuse and redistribution permission and applicable ethics review are established, the release package excludes:

- raw profiles and names;
- usernames, biographies, locations, URLs, image URLs, and images;
- raw entity IDs, raw profile IDs, pair IDs, and any linkable identifiers;
- pair-level feature, prediction, decision, or error rows that could re-identify people.

Safe reproducibility outputs may include code where permitted, configuration, environment/package metadata, SHA-256 hashes, non-identifying manifests, aggregate statistics, aggregate metrics, and aggregate error categories. Local sealed labels remain access-controlled and are never included in public artifacts.
