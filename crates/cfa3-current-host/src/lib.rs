//! CFA3 Current Host native core: explicit ownership, real-edge delta planning,
//! versioned evidence boundary. No authority duplication and no physical PASS issuer.
//!
//! This crate does not test or certify vendor drivers, commercial software, or
//! community plugin implementation quality. It validates CFA3-owned contracts only.

use std::collections::{BTreeMap, BTreeSet, VecDeque};

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum Owner {
    Cfa3Component,
    Cfa3Connector,
    Cfa3PluginHost,
    VendorDriver,
    CommercialSoftware,
    CommunityPlugin,
}
impl Owner {
    fn cfa3_owned(self) -> bool {
        matches!(self, Self::Cfa3Component | Self::Cfa3Connector | Self::Cfa3PluginHost)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Mode { None, Scoped, Full }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Level { Foundation, Layer, Global }

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum TestCase { Positive, Negative, Rollback, StandaloneGui, ParentGui, Handoff }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Trigger {
    Cfa3Code,
    Cfa3Interface,
    GlobalSecurityPolicy,
    EvidenceContract,
    WorkloadModeContract,
    FoundationAbi,
}
impl Trigger {
    fn requires_full(self) -> bool {
        matches!(self, Self::GlobalSecurityPolicy | Self::EvidenceContract
                 | Self::WorkloadModeContract | Self::FoundationAbi)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Component {
    pub id: String,
    pub layer: String,
    pub revision: String,
    pub owner: Owner,
    pub gui: bool,
    /// None means no actual parent; never invent a parent merely to pass GUI CI.
    pub parent_id: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Handoff {
    pub id: String,
    pub producer: String,
    pub consumer: String,
    pub artifact_type: String,
    pub source_revision: String,
    pub processing_owner: String,
    pub acceptance_ref: String,
    pub rollback_ref: String,
}

#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Obligation {
    pub level: Level,
    pub component_id: String,
    pub case: TestCase,
    pub handoff_id: Option<String>,
}

impl Ord for Level {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        (*self as usize).cmp(&(*other as usize))
    }
}
impl PartialOrd for Level {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Plan {
    pub mode: Mode,
    pub affected: Vec<String>,
    pub obligations: Vec<Obligation>,
    pub reason: &'static str,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Error {
    EmptyIdentity,
    DuplicateComponent,
    DuplicateHandoff,
    UnknownComponent,
    StaleSourceRevision,
    ExternalRecipientOutOfScope,
    MissingRealGuiParent,
}

#[derive(Default)]
pub struct Graph {
    components: BTreeMap<String, Component>,
    handoffs: BTreeMap<String, Handoff>,
}

fn all_present(fields: &[&str]) -> bool {
    fields.iter().all(|field| !field.trim().is_empty())
}
impl Graph {
    pub fn new() -> Self { Self::default() }

    pub fn register_component(&mut self, c: Component) -> Result<(), Error> {
        if !all_present(&[&c.id, &c.layer, &c.revision])
           || c.parent_id.as_deref() == Some(c.id.as_str())
        {
            return Err(Error::EmptyIdentity);
        }
        if self.components.contains_key(&c.id) {
            return Err(Error::DuplicateComponent);
        }
        self.components.insert(c.id.clone(), c);
        Ok(())
    }

    pub fn register_handoff(&mut self, e: Handoff) -> Result<(), Error> {
        if !all_present(&[
            &e.id, &e.producer, &e.consumer, &e.artifact_type,
            &e.source_revision, &e.processing_owner, &e.acceptance_ref, &e.rollback_ref,
        ]) || e.producer == e.consumer {
            return Err(Error::EmptyIdentity);
        }
        if self.handoffs.contains_key(&e.id) {
            return Err(Error::DuplicateHandoff);
        }
        let from = self.components.get(&e.producer).ok_or(Error::UnknownComponent)?;
        let to = self.components.get(&e.consumer).ok_or(Error::UnknownComponent)?;
        if from.revision != e.source_revision {
            return Err(Error::StaleSourceRevision);
        }
        if !to.owner.cfa3_owned() {
            return Err(Error::ExternalRecipientOutOfScope);
        }
        self.handoffs.insert(e.id.clone(), e);
        Ok(())
    }

    /// Propagate only through explicitly registered producer -> consumer edges.
    pub fn plan(&self, changes: &[&str], trigger: Trigger) -> Result<Plan, Error> {
        let mut changed = BTreeSet::new();
        for id in changes {
            let c = self.components.get(*id).ok_or(Error::UnknownComponent)?;
            if c.owner.cfa3_owned() {
                changed.insert((*id).to_owned());
            }
        }
        if changed.is_empty() {
            return Ok(Plan {
                mode: Mode::None, affected: vec![], obligations: vec![],
                reason: "EXTERNAL_PRODUCT_OUTSIDE_CFA3_SCOPE",
            });
        }
        let mut affected = changed.clone();
        let mode;
        if trigger.requires_full() {
            affected = self.components.values().filter(|c| c.owner.cfa3_owned())
                .map(|c| c.id.clone()).collect();
            mode = Mode::Full;
        } else {
            mode = Mode::Scoped;
            let mut pending: VecDeque<String> = changed.into_iter().collect();
            while let Some(producer) = pending.pop_front() {
                for e in self.handoffs.values().filter(|e| e.producer == producer) {
                    let receiver = self.components.get(&e.consumer).ok_or(Error::UnknownComponent)?;
                    if receiver.owner.cfa3_owned() && affected.insert(receiver.id.clone()) {
                        pending.push_back(receiver.id.clone());
                    }
                }
            }
        }

        let mut obligations: BTreeSet<Obligation> = BTreeSet::new();
        for id in &affected {
            let c = self.components.get(id).ok_or(Error::UnknownComponent)?;
            let level = if c.layer == "FOUNDATION" { Level::Foundation } else { Level::Layer };
            for case in [TestCase::Positive, TestCase::Negative, TestCase::Rollback] {
                obligations.insert(Obligation { level, component_id: id.clone(),
                                                case, handoff_id: None });
            }
            if c.gui {
                obligations.insert(Obligation {
                    level, component_id: id.clone(),
                    case: TestCase::StandaloneGui, handoff_id: None,
                });
                if let Some(parent) = &c.parent_id {
                    if !self.components.contains_key(parent) {
                        return Err(Error::MissingRealGuiParent);
                    }
                    obligations.insert(Obligation {
                        level, component_id: id.clone(), case: TestCase::ParentGui,
                        handoff_id: None,
                    });
                }
            }
        }
        for e in self.handoffs.values() {
            // Changed CFA3 recipient means its actual inbound bridge is touched.
            // External producer receives NO product-test obligations.
            if affected.contains(&e.consumer) {
                let from = self.components.get(&e.producer).ok_or(Error::UnknownComponent)?;
                let to = self.components.get(&e.consumer).ok_or(Error::UnknownComponent)?;
                let level = if from.owner.cfa3_owned() && from.layer != to.layer {
                    Level::Global
                } else if to.layer == "FOUNDATION" {
                    Level::Foundation
                } else {
                    Level::Layer
                };
                obligations.insert(Obligation {
                    level, component_id: e.consumer.clone(),
                    case: TestCase::Handoff, handoff_id: Some(e.id.clone()),
                });
            }
        }
        Ok(Plan {
            mode, affected: affected.into_iter().collect(),
            obligations: obligations.into_iter().collect(),
            reason: if mode == Mode::Full { "GLOBAL_CONTRACT_CHANGED" } else { "REAL_EDGE_IMPACT" },
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExternalProof {
    pub obligation: Obligation,
    pub revision: String,
    pub physical_host_id: String,
    pub evidence_digest: String,
    pub authority_receipt: String,
    pub physical: bool,
    pub test_pass: bool,
}

/// Implemented by a separately approved Evidence authority, not Current Host.
pub trait PhysicalProofVerifier {
    fn verify(&self, receipt: &ExternalProof) -> bool;
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReviewState {
    NoTestingNeeded,
    PendingProof,
    RejectedUnqualifiedProof,
    PendingEvidenceAuthority,
    ReadyForExternalAuthorityReview,
}

/// Never returns Current Host PASS, and cannot mint evidence itself.
pub fn review_evidence(
    plan: &Plan,
    graph: &Graph,
    reports: &[ExternalProof],
    verifier: Option<&dyn PhysicalProofVerifier>,
) -> ReviewState {
    if plan.mode == Mode::None { return ReviewState::NoTestingNeeded; }
    for test in &plan.obligations {
        let matches: Vec<_> = reports.iter().filter(|p| p.obligation == *test).collect();
        if matches.is_empty() { return ReviewState::PendingProof; }
        if matches.len() != 1 { return ReviewState::RejectedUnqualifiedProof; }
        let p = matches[0];
        let expected_revision = match graph.components.get(&test.component_id) {
            Some(c) => &c.revision,
            None => return ReviewState::RejectedUnqualifiedProof,
        };
        if !p.physical || !p.test_pass || &p.revision != expected_revision
           || !all_present(&[&p.physical_host_id, &p.evidence_digest, &p.authority_receipt])
        {
            return ReviewState::RejectedUnqualifiedProof;
        }
        match verifier {
            None => return ReviewState::PendingEvidenceAuthority,
            Some(check) if !check.verify(p) => return ReviewState::PendingEvidenceAuthority,
            _ => (),
        }
    }
    ReviewState::ReadyForExternalAuthorityReview
}

#[cfg(test)]
mod tests {
    use super::*;
    fn node(id: &str, layer: &str, owner: Owner) -> Component {
        Component {
            id: id.into(), layer: layer.into(), revision: "v1".into(), owner,
            gui: false, parent_id: None,
        }
    }
    fn edge(id: &str, from: &str, to: &str) -> Handoff {
        Handoff {
            id: id.into(), producer: from.into(), consumer: to.into(),
            artifact_type: "asset".into(), source_revision: "v1".into(),
            processing_owner: to.into(), acceptance_ref: "accept".into(),
            rollback_ref: "rollback".into(),
        }
    }
    fn graph() -> Graph {
        let mut g = Graph::new();
        for (id, layer, owner) in [
            ("foundation", "FOUNDATION", Owner::Cfa3Component),
            ("3d", "3D", Owner::Cfa3Component),
            ("video", "VIDEO", Owner::Cfa3Component),
            ("audio", "AUDIO", Owner::Cfa3Component),
            ("plugin-host", "VIDEO", Owner::Cfa3PluginHost),
            ("vendor-driver", "EXTERNAL", Owner::VendorDriver),
            ("commercial", "EXTERNAL", Owner::CommercialSoftware),
            ("community", "EXTERNAL", Owner::CommunityPlugin),
        ] {
            g.register_component(node(id, layer, owner)).unwrap();
        }
        g.register_handoff(edge("3d-video", "3d", "video")).unwrap();
        g.register_handoff(edge("video-audio", "video", "audio")).unwrap();
        g.register_handoff(edge("video-plugin", "video", "plugin-host")).unwrap();
        g
    }

    #[test]
    fn scoped_real_edges_and_proofs() {
        let p = graph().plan(&["3d"], Trigger::Cfa3Code).unwrap();
        assert_eq!(p.mode, Mode::Scoped);
        assert_eq!(p.affected, vec!["3d", "audio", "plugin-host", "video"]);
        assert_eq!(p.obligations.iter().filter(|x| x.case == TestCase::Handoff).count(), 3);
    }

    #[test]
    fn external_products_not_recursively_certified() {
        let g = graph();
        for name in ["vendor-driver", "commercial", "community"] {
            let p = g.plan(&[name], Trigger::Cfa3Code).unwrap();
            assert_eq!(p.mode, Mode::None);
            assert!(p.obligations.is_empty());
        }
    }

    #[test]
    fn one_app_change_does_not_retest_upstream() {
        let p = graph().plan(&["audio"], Trigger::Cfa3Code).unwrap();
        assert_eq!(p.affected, vec!["audio"]);
        assert_eq!(p.obligations.len(), 3);
    }

    #[test]
    fn full_trigger_only_checks_cfa3_owned_components() {
        let p = graph().plan(&["foundation"], Trigger::GlobalSecurityPolicy).unwrap();
        assert_eq!(p.mode, Mode::Full);
        assert_eq!(p.affected.len(), 5);
        assert!(!p.affected.contains(&"commercial".into()));
    }

    #[test]
    fn gui_parent_test_only_when_real_parent_declared() {
        let mut g = graph();
        g.components.get_mut("video").unwrap().gui = true;
        g.components.get_mut("video").unwrap().parent_id = Some("foundation".into());
        let p = g.plan(&["video"], Trigger::Cfa3Code).unwrap();
        assert!(p.obligations.iter().any(|x| x.case == TestCase::ParentGui));
    }

    #[test]
    fn missing_parent_is_a_failure_not_synthetic_pass() {
        let mut g = graph();
        g.components.get_mut("video").unwrap().gui = true;
        g.components.get_mut("video").unwrap().parent_id = Some("missing".into());
        assert_eq!(g.plan(&["video"], Trigger::Cfa3Code), Err(Error::MissingRealGuiParent));
    }

    #[test]
    fn cannot_claim_physical_pass_without_evidence() {
        let g = graph();
        let p = g.plan(&["audio"], Trigger::Cfa3Code).unwrap();
        assert_eq!(review_evidence(&p, &g, &[], None), ReviewState::PendingProof);
    }

    #[test]
    fn synthetic_proofs_fail_closed() {
        let g = graph();
        let p = g.plan(&["audio"], Trigger::Cfa3Code).unwrap();
        let claims = p.obligations.iter().map(|obligation| ExternalProof {
            obligation: obligation.clone(), revision: "v1".into(),
            physical_host_id: "fake".into(), evidence_digest: "fake".into(),
            authority_receipt: "fake".into(), physical: false, test_pass: true,
        }).collect::<Vec<_>>();
        assert_eq!(review_evidence(&p, &g, &claims, None),
                   ReviewState::RejectedUnqualifiedProof);
    }

    #[test]
    fn claimed_physical_evidence_still_needs_real_authority() {
        let g = graph();
        let p = g.plan(&["audio"], Trigger::Cfa3Code).unwrap();
        let claims = p.obligations.iter().map(|obligation| ExternalProof {
            obligation: obligation.clone(), revision: "v1".into(),
            physical_host_id: "host".into(), evidence_digest: "digest".into(),
            authority_receipt: "pending".into(), physical: true, test_pass: true,
        }).collect::<Vec<_>>();
        assert_eq!(review_evidence(&p, &g, &claims, None),
                   ReviewState::PendingEvidenceAuthority);
    }

    #[test]
    fn cannot_register_handoff_to_vendor_product() {
        let mut g = graph();
        assert_eq!(g.register_handoff(edge("bad", "video", "commercial")),
                   Err(Error::ExternalRecipientOutOfScope));
    }

    #[test]
    fn reject_stale_handoff() {
        let mut g = graph();
        let mut e = edge("stale", "video", "audio");
        e.source_revision = "v0".into();
        assert_eq!(g.register_handoff(e), Err(Error::StaleSourceRevision));
    }
}
