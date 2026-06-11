# Output Schema

`hkust_gz_faculty_profiles.json` is a list of person-Thrust rows. A faculty member can appear more than once when selected Thrusts overlap.

Core fields:

- `id`: profile person ID from the public API.
- `code`: public HKUST(GZ) profile code when present.
- `en_name`, `zh_name`, `first_name`, `last_name`.
- `email`, `phone`, `location`.
- `degree`, `school`, `end_date`, `major`.
- `website`, `permalink`, `profile_url`, `photo_url`.
- `selected_hub`, `selected_hub_key`, `selected_thrust`, `selected_thrust_code`.
- `official_role`: `ACTING_HEAD`, `CURRENT_FACULTY_ADVISOR`, or `PAGE_RESULT`.
- `jobs`: public jobs from the profile record.
- `matched_jobs`: subset of `jobs` matching the selected Thrust.
- `identifiers`: normalized identifiers keyed by label, for example `GoogleScholarID`, `ORCID`, `ScopusID`.
- `source`: source endpoint names used for the row.

When `--include-details` is set:

- `details` contains the public response from `/api/itdcms-rpc/profile/primary/{id}`.
- Details can include projects, resumes, publications, overview-like content, research interests, and other public profile sections. Keep this as raw source data unless a downstream workflow defines a stricter schema.

CSV export flattens only review-friendly fields and keeps `identifiers`, `matched_jobs`, and `source` as JSON strings.
