# Deliberately Invalid Fixtures

Files below this directory are negative test inputs. They are not alternate
authoritative configuration.

`stale-manifest/program.yaml` declares source version 3 but points to the example's
authoritative v4 plan. A validator must report the source-version mismatch.
