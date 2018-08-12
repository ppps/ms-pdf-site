# ms-pdf-site

*Really* basic Python script and Nginx config to generate a single-page website
from an S3 bucket containing JPGs and PDFs.

Roughly handles changes to already-existing files in the bucket, by checking
against the previously seen last-modified date.

Requires S3 credentials to be saved in `~/.aws/credentials` (the Boto library
looks here automatically, so there’s no credential-handling in the script
itself.
