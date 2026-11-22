# 02 System Models: Research Compass

Phase 2 deliverable (Sommerville Ch 5). Owner: Dipesh Rayamajhi (Architect). Date: 2026-11-22.

The context model, the search-and-add sequence, and the class model are in [FULL_SPEC.md §3](FULL_SPEC.md).
This file adds the use-case model, three more sequences (including the save and restore failure paths), the
state machines, the information flow from search to proposal, and the requirement-to-model trace.
GitHub renders the Mermaid blocks; each is followed by a plain-text summary.

## 1. Use cases

```mermaid
flowchart LR
  Student([Graduate student])
  Advisor([Advisor])
  PC[(Paperclip)]
  subgraph RC[Research Compass]
    UC1((UC1 Create project))
    UC2((UC2 Search and add papers))
    UC3((UC3 Record notes))
    UC4((UC4 Export matrix / outline))
    UC5((UC5 Check coverage))
    UC6((UC6 Compare topics))
    UC7((UC7 Draft proposal + BibTeX))
    UC8((UC8 Undo last change))
    UC9((UC9 Ask AI reader))
  end
  Student --- UC1 & UC2 & UC3 & UC4 & UC5 & UC6 & UC7 & UC8 & UC9
  UC2 --- PC
  UC6 --- PC
  UC9 --- PC
  UC4 -. files .-> Advisor
  UC7 -. files .-> Advisor
```

Summary: one human actor (the student) starts every use case. Paperclip takes part in UC2, UC6 and UC9 only, and
`--offline` replaces it for UC2 and UC6. The advisor never uses the app; they receive exported files.
MVP use cases: UC1–UC4. Increment 2: UC5, UC6. Increment 3: UC7, UC8. Could: UC9.

## 2. Information flow: from a search to a proposal

```mermaid
flowchart LR
  Q[query] -->|PaperSource.search| R[SearchResult papers]
  R -->|saved as last_search| LS[(Project.last_search)]
  LS -->|add 1 3 + dedup keys| E[(Project.entries)]
  E -->|note| N[SurveyEntry theme/method/finding/limitation/relevance]
  N --> MX[matrix.md]
  N --> OL[outline.md: themes + Gaps]
  N --> CK[check: coverage warnings]
  N --> PR[proposal.md: related work by theme, gap list]
  PL[plan: RQs, method, phases] --> PR
  E --> BIB[refs.bib]
```

Summary: a search result is stored only as `last_search` until the student picks numbers with `add`; only then
does it become a `SurveyEntry`. Everything exported is computed from entries and the student's own notes; the app
never invents a finding. The proposal is the only output that combines notes with the `plan` fields.

## 3. Sequence: compare topics (UC6)

```mermaid
sequenceDiagram
  actor S as Student
  participant C as cli
  participant St as storage
  participant Src as PaperSource
  participant T as topics
  S->>C: topics "q1" "q2" "q3"
  C->>St: load()
  C->>T: validate_queries([...])
  alt 0 or more than 8 queries
    T-->>C: ValueError
    C-->>S: error: Compare at most 8 topics (exit 1)
  end
  loop each query
    C->>Src: search(q, limit=40)
    Src-->>C: papers
  end
  C->>T: rank_topics(results, year)
  T-->>C: candidates (score, verdict, reasons, low_confidence)
  C->>T: weight_sensitivity(results, year)
  T-->>C: (agree, 5)
  C->>T: suggest_narrower(top query, its papers)
  C->>St: save(candidates)
  C-->>S: "Indicators … do not judge research value", table, robustness line, suggestions
```

Summary: all searches finish before anything is saved, so a Paperclip failure in the second query leaves the file
untouched (R11). Scoring, sensitivity and suggestions are pure functions of the search results and the year.

## 4. Sequence: saving, and what happens when it fails (R26, R27)

```mermaid
sequenceDiagram
  participant C as cli
  participant St as storage
  participant FS as disk
  C->>St: save(project, project.json)
  St->>FS: write project.json.tmp, flush, fsync
  alt write fails (disk full, permission)
    St->>FS: delete project.json.tmp
    St-->>C: StorageError "not changed"
    C-->>C: error:, exit 1
  else written
    St->>FS: copy project.json -> project.json.bak
    St->>FS: os.replace(tmp, project.json)  (atomic)
    alt rename fails
      St->>FS: delete tmp
      St-->>C: StorageError "not changed"
    end
  end
```

Summary: the old file is only ever replaced in one atomic step, after the new content is safely on disk. At every
failure point the student keeps either the old file or the new one, never half of each.

## 5. Sequence: damaged file and restore (R28, R23)

```mermaid
sequenceDiagram
  actor S as Student
  participant C as cli
  participant St as storage
  S->>C: list
  C->>St: load(project.json)
  St-->>C: StorageError "…is not valid JSON… run `restore`"
  C-->>S: error: … (exit 1)
  S->>C: restore
  C->>St: restore(project.json)
  St->>St: _read(project.json.bak) and validate
  alt backup damaged or missing
    St-->>C: StorageError
    C-->>S: error: … (file unchanged)
  else backup valid
    St->>St: save(backup project)  (damaged file becomes the new .bak)
    C-->>S: Restored previous save (N papers). Run restore again to undo.
  end
```

## 6. State machines

```mermaid
stateDiagram-v2
  [*] --> Added: add
  Added --> PartlyNoted: note (some fields)
  PartlyNoted --> Complete: theme + finding + relevance set
  Added --> Complete: note (all three)
  Complete --> PartlyNoted: note --theme "" (clears a field)
  Added --> [*]: remove
  PartlyNoted --> [*]: remove
  Complete --> [*]: remove
```

Survey entry: `is_complete()` is true only in *Complete*. `check` lists entries not in *Complete* (R13).

```mermaid
stateDiagram-v2
  [*] --> Created: init
  Created --> Surveying: add (MVP path)
  Created --> TopicsCompared: topics
  TopicsCompared --> TopicChosen: choose
  TopicChosen --> Surveying: search + add
  Surveying --> Surveying: note, add, remove
  Surveying --> ProposalReady: readiness() is empty
  ProposalReady --> Surveying: remove / new gaps
  TopicChosen --> TopicsCompared: topics again
  note right of Surveying: restore returns to the previous save from any state
```

Project: the MVP path skips topics entirely (`Created → Surveying`). *ProposalReady* is not stored; it is computed by
`readiness()` each time, so it can never be out of date.

## 7. Requirement → model trace

| Requirement | Model elements |
|---|---|
| R1, R2 | UC1; Project state *Created* |
| R3–R6 | UC2; Full Spec search-and-add sequence; `Project.last_search`, dedup keys in §2 flow |
| R7, R8 | UC3; `SurveyEntry` attributes; entry state machine |
| R9, R10 | UC4; §2 flow (matrix, outline) |
| R11 | every sequence's failure branch |
| R12 | `PaperSource` interface with `OfflineSource` (class model) |
| R13 | UC5; entry state *Complete* |
| R14–R18 | UC6; §3 sequence; `TopicCandidate` incl. `low_confidence` |
| R19–R22 | UC7; §2 flow (proposal, refs.bib); `Phase` |
| R23 | UC8; §5 sequence; note on project state machine |
| R24, R25 | UC9; `PaperclipSource` |
| R26, R27 | §4 sequence |
| R28 | §5 sequence; invariants under the class model |
| R31 | context model (key read-only from login store/env) |
| R32 | failure branch in the search-and-add sequence |

## 8. Inconsistencies found and how they were resolved
1. The v1 project state machine required *TopicChosen* before *Surveying*, but the MVP no longer includes topics. Added the `Created → Surveying` path; `search` takes an explicit query when no topic is chosen (already true in `cli.py`).
2. `restore` (R23) was in no model. Added §5 and a note on the project state machine.
3. `TopicCandidate.low_confidence` was missing from the class model after the R16 change. Added; old files load with the default `false`.
4. The first draft of the entry state machine said a field could only be cleared by hand-editing the JSON. Checking `update_note` showed that `note <id> --theme ""` clears it (only an omitted option is ignored). The diagram now shows that transition. Relevance cannot be cleared back to 0 through the CLI; no requirement asks for that.

**AI contribution:** Claude drew these models from the code after the 2026-11-22 changes. Dipesh to check each
diagram against the running app (Sprint 1 task in the charter).
