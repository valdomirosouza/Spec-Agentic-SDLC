<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Templates

Every artefact the SDD cycle produces starts as one of these. They travel in **every** adoption
layer, because a corpus that ships a workflow and not the forms that workflow fills is a corpus
that only works here.

The index is closed in both directions and `check-corpus.sh` C17 enforces it: a template added
without an entry fails, and an entry naming a file that does not exist fails. A list kept by hand
is complete only where someone looked, and this repository has now been bitten by that twice —
once in its adoption layers (#107) and once in the set it tracks upstream.

| Template                       | Filled by                                          | Produces                                     |
| ------------------------------ | -------------------------------------------------- | -------------------------------------------- |
| `spec-template.md`             | `create-new-feature.sh` (behind `/sdd-specify`)    | `specs/features/<SPEC-ID>-<slug>/spec.md`    |
| `plan-template.md`             | `setup-plan.sh` (behind `/sdd-plan`)               | the feature's `plan.md`                      |
| `research-template.md`         | `setup-plan.sh`                                    | the feature's `research.md`                  |
| `data-model-template.md`       | `setup-plan.sh`                                    | the feature's `data-model.md`                |
| `quickstart-template.md`       | `setup-plan.sh`                                    | the feature's `quickstart.md`                |
| `contracts-README-template.md` | `setup-plan.sh`                                    | the feature's `contracts/README.md`          |
| `tasks-template.md`            | `/sdd-tasks`, by the agent                         | the feature's `tasks.md`                     |
| `checklist-template.md`        | `/sdd-checklist` and `/sdd-specify`, by the agent  | `checklists/<domain>.md` beside the spec     |
| `roadmap-template.md`          | `/sdd-specify`, when a spec names an epic          | a roadmap beside the specs                   |
| `constitution-template.md`     | `/sdd-constitution`, by the agent                  | `memory/constitution.md` in an adopting repo |
| `data-contract-template.md`    | a data owner, by hand                              | an entry in `specs/data/data-contracts.md`   |
| `datasheet-template.md`        | a data owner, by hand                              | a datasheet under `docs/data/datasheets/`    |
| `model-card-template.md`       | an AI governance owner, by hand                    | a model card under `docs/ai-governance/`     |

Six of the thirteen are materialised by a script, so they are exercised on every smoke run; the
rest are filled by an agent or a person and are only as current as the last time someone read them.

## The two files called a spec template

They are different artefacts, and the names do not say so:

| | `templates/spec-template.md` | `specs/SPEC-TEMPLATE.md` |
| --- | --- | --- |
| For | one **feature**, inside a feature bundle | a **system, policy or threat-model** spec |
| Filled by | `/sdd-specify` and `create-new-feature.sh`, automatically | a person, by hand |
| Header | frontmatter the feature bundle reads | a machine-readable metadata block `/deliver` and CI read |
| Lands in | `specs/features/<SPEC-ID>-<slug>/spec.md` | `specs/<domain>/SPEC-<DOMAIN>-NNN-<slug>.md` |

If you are writing a feature, you will never touch the second one: the command opens the first for
you. If you are writing a spec that governs something standing — an API contract, a security
policy, a log-based signal — the second is the one.
