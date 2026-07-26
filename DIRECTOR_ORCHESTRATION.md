# Director's Orchestration Guide

**Vessel Agent System - Agent Coordination Center**
**Vessel:** F/V EILEEN (51' Commercial Fishing Vessel)
**Last Updated:** 2026-07-24
**Status:** Active Development - Phase 0

---

## Director's Overview

This document serves as the **central coordination point** for all agent work on the vessel-agent system. It provides:
- Current system status
- Active agent teams and their missions
- Quality standards for all deliverables
- Orchestration protocols for multi-agent workflows

---

## Current System Status

### Phase: 0 - Data Capture Emergency
**Timeline:** July 2026 (Days 1-30)
**Focus:** Level 0 - Raw Bits (network packets, NMEA bytes)

### Completion Status

| Component | Status | Progress | Notes |
|-----------|--------|----------|-------|
| Python Backend | ✅ Complete | 85% | Network capture, NMEA, Parquet, monitoring |
| Test Suite | ✅ Complete | 100% | 4 test modules, all passing |
| Documentation | ✅ Complete | 95% | 21 docs, 18K+ lines |
| TypeScript UI | ⏳ Planned | 0% | Phase 1 |
| Optimization | ⏳ Pending | 0% | NOT required for single vessel |

### Recent Commits

```
e9b341f Add Python performance optimization analysis
81b4868 Add comprehensive language & architecture analysis
209c66b Implement Phase 0 - Complete Python implementation
9235e5d Add play-test results from external agent evaluation
f7aefd9 Initial commit: Vessel Agent System knowledge base
```

---

## Active Agent Teams

### Team 1: Professional Mariner Guide
**Agent ID:** a6be341
**Mission:** Create comprehensive user guide for fishing vessel captains and crew
**Status:** Running
**Deliverable:** USER_GUIDE_MARINER.md
**Quality Standard:** Marine-grade, practical, zero jargon without explanation

### Team 2: Academic Researcher Guide
**Agent ID:** aba7268
**Mission:** Create technical guide for PhD researchers and marine scientists
**Status:** Running
**Deliverable:** USER_GUIDE_ACADEMIC.md
**Quality Standard:** Publication-ready, ICES-compliant, rigorous

### Team 3: Senior Engineer Guide
**Agent ID:** ad5eae0
**Mission:** Create comprehensive technical guide for systems engineers
**Status:** Running
**Deliverable:** USER_GUIDE_ENGINEER.md
**Quality Standard:** Production-quality, with code examples and diagrams

### Team 4: Agent Onboarding Guide
**Agent ID:** a6d814b
**Mission:** Create onboarding documentation for AI agent continuity
**Status:** Running
**Deliverable:** AGENT_ONBOARDING.md
**Quality Standard:** Zero-shot agent understanding, complete and structured

---

## Quality Standards

### Marine-Grade Documentation Standards

All documentation must meet these standards:

**1. Clarity**
- Technical terms explained on first use
- Acronyms defined in context
- Examples provided for all concepts
- Progressive complexity (start simple, add depth)

**2. Completeness**
- All topics covered for target audience
- No "TODO" placeholders in final docs
- Cross-references to related documents
- Practical examples included

**3. Accuracy**
- Technical details verified against implementation
- Code examples tested and working
- References to actual files/line numbers
- Real-world constraints acknowledged

**4. Accessibility**
- Zero-shot reader capable (understand without prior context)
- Multiple entry points for different knowledge levels
- Clear navigation and structure
- Visual aids (diagrams, tables, examples) where helpful

**5. Professionalism**
- Proper grammar and spelling
- Consistent terminology
- Respectful of reader's intelligence
- Acknowledges limitations and trade-offs

### Document Templates

#### Template: User Guide

```markdown
# [Title] - [Audience Level] Guide

## Introduction (2-3 pages)
- Hook/narrative appropriate for audience
- What this system does in their context
- Why it matters for their work
- Real-world examples

## Core Concepts
- 5-7 key concepts
- Each with example
- Progressive complexity

## Practical Usage
- Step-by-step procedures
- Common scenarios
- Troubleshooting

## Reference
- Quick lookup tables
- Command reference
- Configuration options

## Appendices
- Glossary
- Further reading
- Contact info
```

---

## Orchestration Protocols

### Protocol: Multi-Agent Coordination

When launching multiple agents:

**1. Pre-Launch Setup**
```python
# Define agent missions clearly
missions = {
    "team1": {
        "purpose": "Create mariner guide",
        "audience": "Professional fishermen",
        "tone": "Practical, no-nonsense",
        "deliverable": "USER_GUIDE_MARINER.md"
    },
    # ...
}

# Launch with block=false to run in parallel
for team, config in missions.items():
    agent = Task(
        description=config["purpose"],
        prompt=detailed_prompt,
        subagent_type="general-purpose",
        run_in_background=True
    )
```

**2. During Execution**
- Monitor agent progress via TaskOutput
- Provide guidance if agents go off-track
- Collect results as they complete

**3. Post-Collection**
- Review all deliverables
- Check against quality standards
- Request revisions if needed
- Integrate into repository

### Protocol: Quality Review

Before pushing to GitHub:

**1. Self-Check**
```bash
# Does it meet quality standards?
- Clarity: Yes/No
- Completeness: Yes/No
- Accuracy: Yes/No
- Accessibility: Yes/No
- Professionalism: Yes/No
```

**2. Peer Review**
- Have another agent read the document
- Check for zero-shot understanding
- Verify examples work

**3. Final Validation**
- Test all code examples
- Verify all references
- Check cross-references

### Protocol: Repository Management

**Commit Standards:**
```
Format: [Verb] [Component] - [Brief Description]

Example:
Add mariner guide for professional fishermen
Create comprehensive user guide for commercial fishing vessel
captains and crew with practical operations and real-world examples
```

**Push Sequence:**
1. Commit each major deliverable separately
2. Use descriptive commit messages
3. Push immediately after commit
4. Verify on GitHub

---

## Agent Communication Protocols

### When Assigning Tasks

**Clear Task Definition:**
- Specific deliverable
- Target audience
- Quality standard
- Timeline expectation
- Reference materials

### When Reviewing Work

**Constructive Feedback:**
- Acknowledge what's good
- Specify what needs improvement
- Provide examples
- Allow revision

### When Coordinating Teams

**Synchronization Points:**
- Kickoff meeting (document expectations)
- Mid-point check (address blockers)
- Final review (quality gate)
- Integration (combine deliverables)

---

## Current Documentation Suite

### User-Facing Documents (In Progress)

1. **USER_GUIDE_NON_TECHNICAL.md** ✅ Complete
   - Audience: Non-technical users
   - Tone: Friendly, accessible
   - Length: ~400 lines

2. **USER_GUIDE_STUDENT.md** ✅ Complete
   - Audience: Clever high school students
   - Tone: Educational, inspiring
   - Length: ~600 lines

3. **USER_GUIDE_MARINER.md** 🔄 In Progress (Agent a6be341)
   - Audience: Professional fishermen
   - Tone: Practical, maritime
   - Length: TBD

4. **USER_GUIDE_ACADEMIC.md** 🔄 In Progress (Agent aba7268)
   - Audience: PhD researchers
   - Tone: Rigorous, scientific
   - Length: TBD

5. **USER_GUIDE_ENGINEER.md** 🔄 In Progress (Agent ad5eae0)
   - Audience: Senior engineers
   - Tone: Technical, precise
   - Length: TBD

6. **AGENT_ONBOARDING.md** 🔄 In Progress (Agent a6d814b)
   - Audience: AI agents
   - Tone: Clear, structured
   - Length: TBD

### Technical Documents (Complete)

1. **README.md** - Project entry point
2. **vessel_agent_memory_schema.json** - Complete system schema
3. **vessel_agent_knowledge_base.md** - Technical knowledge
4. **ARCHITECTURE_DECISION_RECORD.md** - Design decisions
5. **PERFORMANCE_REQUIREMENTS.md** - Performance analysis
6. **PYTHON_OPTIMIZATION_ANALYSIS.md** - Optimization strategies
7. **LANGUAGE_ARCHITECTURE_ANALYSIS.md** - Multi-language analysis
8. **PLAY_TEST_RESULTS.md** - External evaluation
9. **README_IMPLEMENTATION.md** - Implementation guide

---

## Quick Reference for Directors

### Checklist: Starting a New Session

**Initial Setup (5 minutes):**
- [ ] Read this document
- [ ] Check git status for uncommitted work
- [ ] Review recent commits
- [ ] Identify current phase goals

**Documentation Review (15 minutes):**
- [ ] Read README.md (project status)
- [ ] Check ARCHITECTURE_DECISION_RECORD.md (latest decisions)
- [ ] Review PERFORMANCE_REQUIREMENTS.md (constraints)

**Agent Coordination (as needed):**
- [ ] Launch specialist agents with clear missions
- [ ] Monitor progress via TaskOutput
- [ ] Collect and review deliverables
- [ ] Integrate into repository

### Checklist: Before Pushing

**Quality Gate:**
- [ ] All code tested
- [ ] All documentation proofread
- [ ] All references verified
- [ ] Cross-references checked
- [ ] Commit messages descriptive

**Final Verification:**
- [ ] git status shows intended changes
- [ ] git log shows recent history
- [ ] No TODO placeholders in final docs
- [ ] All agents' work collected

---

## Decision Framework

### When to Launch Agents

**Launch specialist agents when:**
- Task requires deep research
- Multiple perspectives needed
- Complex multi-step workflows
- Specialized expertise required

**Handle directly when:**
- Simple file edits
- Clear documentation updates
- Routine maintenance
- Well-defined tasks

### When to Require Revision

**Require revision if:**
- Quality standards not met
- Zero-shot understanding fails
- Technical inaccuracies present
- Missing components

**Accept as-is if:**
- Minor stylistic issues
- Different but valid approach
- Audience-appropriate simplification
- Time constraints prevent perfection

---

## Common Scenarios

### Scenario: New Feature Request

**Process:**
1. Evaluate against current phase goals
2. Check ARCHITECTURE_DECISION_RECORD.md for constraints
3. If aligned: Launch agent for implementation
4. If not aligned: Document in backlog for future phase

### Scenario: Bug Report

**Process:**
1. Verify bug exists
2. Create reproduction case
3. Launch agent for fix
4. Add test for regression prevention
5. Update documentation if needed

### Scenario: Documentation Update

**Process:**
1. Identify which document needs update
2. Check for cross-references
3. Make update maintaining style
4. Verify zero-shot understanding
5. Commit and push

---

## Success Metrics

### For Documentation

**Metrics:**
- Zero-shot reader success (can understand without prior context)
- Cross-reference accuracy (all links work)
- Example validity (all code works)
- Audience appropriateness (tone matches reader)

**Targets:**
- User guides: 90%+ satisfaction in testing
- Technical docs: 95%+ accuracy
- Agent docs: 100% agent continuity

### For Development

**Metrics:**
- Code coverage: >80%
- Test pass rate: 100%
- Documentation coverage: 100% of public APIs
- Performance: Meets requirements in PERFORMANCE_REQUIREMENTS.md

---

## Emergency Procedures

### If Agent Goes Rogue

**Symptoms:**
- Agent not following guidelines
- Producing low-quality output
- Going off-mission

**Response:**
1. Kill agent if background process
2. Clarify mission with tighter constraints
3. Relaunch with clearer instructions
4. Monitor more closely

### If Repository State Confused

**Symptoms:**
- Uncommitted changes
- Merge conflicts
- Unclear current state

**Response:**
1. git status to assess
2. git stash if needed
3. git pull origin main to sync
4. git stash pop to restore work
5. Document in commit message

### If Quality Standards Unclear

**Symptoms:**
- Unclear what "good enough" means
- Conflicting quality criteria
- Template not applicable

**Response:**
1. Refer to this document's Quality Standards section
2. Use peer review (have another agent check)
3. Apply professional judgment
4. Document decision for future reference

---

## Director's Notes

### Session 2026-07-24

**Objectives:**
- Complete user-facing documentation suite
- Create agent onboarding system
- Ensure high marine-grade standards
- Establish reproducible workflows

**Agent Teams Deployed:**
- Professional Mariner Guide (a6be341)
- Academic Researcher Guide (aba7268)
- Senior Engineer Guide (ad5eae0)
- Agent Onboarding Guide (a6d814b)

**Status:**
- Non-technical and student guides: Complete
- Specialist guides: In progress
- Onboarding system: In progress

**Next Steps:**
1. Collect agent deliverables
2. Quality review all documents
3. Create master documentation index
4. Push complete documentation suite
5. Establish ongoing maintenance protocols

---

## Contact & Context

**Director:** Human-in-the-loop (Casey)
**Vessel:** F/V EILEEN
**Home Port:** Southeast Alaska
**Methodology:** BMAD (Bottom-up, Multi-level, Agile Development)
**Horizon:** 2031

**Repository:** https://github.com/SuperInstance/vessel-agent

---

*Director's Orchestration Guide v1.0.0*
*Last Updated: 2026-07-24*
*Status: Active - Documentation Phase*
*Next Update: After completion of user guide suite*
