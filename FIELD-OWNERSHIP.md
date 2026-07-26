# Field ownership map

Who is the **writer** for each shared field (one writer, many readers). This is the
rule that keeps a shared DB coherent: only the owning app updates a given core
field; every other app reads it. App-specific data lives in that app's own schema,
keyed to the core id.

Legend: **W** = writes, **R** = reads. Apps: MR = Make-Ready, RL = REDLINE,
BIM = Light Speed BIM, ODEN = ODEN.

## core.project  (the "job")
| Field | MR | RL | BIM | ODEN | Notes |
|---|:--:|:--:|:--:|:--:|---|
| job_number | R | **W** | R | R | REDLINE (PM/coordination) creates jobs |
| name, client | R | **W** | R | R | |
| status | R | **W** | R | R | project lifecycle owned by RL |
| geo (bbox/centroid) | R | R | R | **W** | ODEN GIS sets/refines geo |

## core.pole
| Field | MR | RL | BIM | ODEN | Notes |
|---|:--:|:--:|:--:|:--:|---|
| tag | **W** | R | R | **W** | created in MR field entry or ODEN GIS; first writer wins, then R |
| lat, lng | R | R | R | **W** | ODEN GIS is the geo authority |
| owner (utility) | **W** | R | R | R | make-ready determines pole owner |
| height_ft, pole_class | **W** | R | R | R | measured during make-ready |
| project (FK) | **W** | **W** | R | **W** | any app can associate a pole to a job |

## core.attachment  (wires/equipment on a pole)
| Field | MR | RL | BIM | ODEN | Notes |
|---|:--:|:--:|:--:|:--:|---|
| kind, owner | **W** | R | R | R | make-ready inventories attachments |
| height_ft | **W** | R | **W** | R | MR measures; BIM may refine from 3-D model |
| notes | **W** | R | R | R | |

## core.entitlement
Written only by admin/billing (later Stripe webhook). All apps **read** it to gate
features. Never written by app feature code.

## App-specific schemas (NOT shared — each app fully owns these)
| Table | Owner | Keyed to |
|---|---|---|
| makeready.pole_detail (NESC calc, SPIDA status, cables) | MR | core.pole |
| makeready.permit | MR | core.project |
| redline.work_order (contractor, due, status) | RL | core.project |
| bim.pole_structure (geometry, conduit, splice vaults) | BIM | core.pole |
| bim.network_topology | BIM | core.project |

## Conflict rules
- A field with two **W** apps (e.g. `pole.tag`, `pole.project`) uses **first-writer-creates, others-read**; edits to an existing value go through the field's primary owner (bold-first in the row) or an explicit "override" audited via `core.audit`.
- Every cross-app write appends a `core.audit` row (actor, entity, action) so provenance is traceable.
- When in doubt, add the field to an app's **own** schema instead of `core`. Only truly shared identity belongs in `core`.
