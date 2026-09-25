# Security and Privacy

## Scope

Medical AI is pre-release research/education software. Security, privacy, clinical-safety validation, and regulatory assessment are separate gates.

## Do not report sensitive data publicly

This repository is private, but repository content is still not an approved PHI store. Do not place real patient identifiers, clinical records, Medicare numbers, credentials, secrets, access tokens, or private keys in issues, pull requests, commits, Actions logs, screenshots, or test fixtures.

Use synthetic or de-identified examples for testing.

## Reporting a vulnerability

Do not open an issue containing exploit details, credentials, or health information. Contact the repository owner privately and include only the minimum information required to reproduce the problem safely.

## Safety-critical defects

Treat defects as release-blocking when they can cause the application to:

- display a medical claim its own policy forbids;
- misrepresent evidence provenance or citation support;
- bypass high-consequence verification;
- treat retracted/superseded evidence as current;
- expose patient-identifying data to a connector that is not PHI-approved;
- tell users a safety/privacy control worked when it did not.

A fix is not established until the relevant regression and integration evidence exists for the exact revision/artifact under review.
