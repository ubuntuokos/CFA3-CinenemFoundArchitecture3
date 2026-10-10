//! CRAM-02: structural contracts for three distinct CrAM technologies.
//! This module DOES NOT grant rights, select models, allocate resources,
//! authorize operations, perform execution, or attest to Current Host PASS.
use crate::{BackendClass, ObservedRoute};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Variant { CompressionAware2023, CredibilityAware2025, AdaptiveMoe2026 }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Operation { OptimizeModel, ScoreEvidence, ModifyAttention, InspectExperts, TrainExperts }
impl Operation {
    pub fn variant(self) -> Variant {
        match self {
            Self::OptimizeModel => Variant::CompressionAware2023,
            Self::ScoreEvidence | Self::ModifyAttention => Variant::CredibilityAware2025,
            Self::InspectExperts | Self::TrainExperts => Variant::AdaptiveMoe2026,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CodeUse { ReferenceOnly, IndependentImplementation, UpstreamCode }
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Rights { Unknown, Verified, Rejected }
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SourcePin {
    pub repository: &'static str,
    pub commit: &'static str,
    /// Repository root license observed, NOT third-party/dependency admission.
    pub root_license_verified: bool,
}
impl Variant {
    pub fn pinned_source(self) -> SourcePin {
        match self {
            Self::CompressionAware2023 => SourcePin {
                repository: "https://github.com/IST-DASLab/CrAM",
                commit: "b89d9ff2b0c7d343736d587dd27f95d86a2df1cf",
                root_license_verified: true,
            },
            Self::CredibilityAware2025 => SourcePin {
                repository: "https://github.com/Aatrox103/CrAM",
                commit: "b6403d002a7bb445410f277a73907d7a2e3a8bf1",
                root_license_verified: false,
            },
            Self::AdaptiveMoe2026 => SourcePin {
                repository: "https://github.com/LAMDA-CL/EMNLP2026-CRAM",
                commit: "576edf0f0a4c23052f275d6a57d36197d4c067ba",
                root_license_verified: true,
            },
        }
    }
}

/// Opaque references. The actual CFA3 authorities must verify signature,
/// revision, digest, actor, operation, expiry, resource lease and permissions.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ExternalAuthorityRefs<'a> {
    pub grant: &'a str,
    pub router: &'a str,
    pub hrb: &'a str,
    pub workload_mode: &'a str,
    pub security: &'a str,
    pub rights: &'a str,
    pub approval: &'a str,
    pub budget: &'a str,
}
impl ExternalAuthorityRefs<'_> {
    fn populated(self) -> bool {
        [self.grant, self.router, self.hrb, self.workload_mode,
         self.security, self.rights, self.approval, self.budget]
            .iter().all(|s| !s.trim().is_empty())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Request<'a> {
    pub id: &'a str,
    pub variant: Variant,
    pub operation: Operation,
    pub source_commit: &'a str,
    pub code_use: CodeUse,
    pub upstream_code_rights: Rights,
    pub actor: &'a str,
    pub project: &'a str,
    pub work_context: &'a str,
    pub model_id: &'a str,
    pub model_revision: &'a str,
    pub input_digest: &'a str,
    pub dataset_provenance: Option<&'a str>,
    pub authority: ExternalAuthorityRefs<'a>,
    pub backend: BackendClass,
    pub rollback_ref: &'a str,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ContractError {
    VariantMismatch, SourceRevisionMismatch, MissingField,
    UnverifiedCodeRights, UnsupportedReferenceBackend,
    UndeclaredBackendChange, MissingOutputArtifact, UnknownOutcomeRetry,
}

impl Request<'_> {
    /// Only validates syntax/shape. Does NOT authorize the request.
    pub fn validate_structure(self) -> Result<(), ContractError> {
        if self.variant != self.operation.variant() { return Err(ContractError::VariantMismatch); }
        if self.source_commit != self.variant.pinned_source().commit {
            return Err(ContractError::SourceRevisionMismatch);
        }
        if [self.id, self.actor, self.project, self.work_context, self.model_id,
            self.model_revision, self.input_digest, self.rollback_ref]
            .iter().any(|s| s.trim().is_empty()) || !self.authority.populated()
        { return Err(ContractError::MissingField); }
        if matches!(self.operation, Operation::OptimizeModel | Operation::TrainExperts)
            && !self.dataset_provenance.is_some_and(|s| !s.trim().is_empty())
        { return Err(ContractError::MissingField); }
        if self.code_use == CodeUse::UpstreamCode
            && (!self.variant.pinned_source().root_license_verified
                || self.upstream_code_rights != Rights::Verified)
        { return Err(ContractError::UnverifiedCodeRights); }
        // The pinned 2026 upstream training environment requires a CUDA GPU.
        // Future independently qualified CPU implementations are separate.
        if self.code_use == CodeUse::UpstreamCode
            && self.operation == Operation::TrainExperts
            && self.backend == BackendClass::Cpu
        { return Err(ContractError::UnsupportedReferenceBackend); }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Outcome { Completed, Failed, Rejected, Unknown }
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Receipt<'a> {
    pub request: Request<'a>,
    pub outcome: Outcome,
    pub route: ObservedRoute,
    pub output_digest: Option<&'a str>,
    pub retry_permitted: bool,
}
impl Receipt<'_> {
    /// Structural receipt validation, NOT evidence of a real successful run.
    pub fn validate_structure(self) -> Result<(), ContractError> {
        self.request.validate_structure()?;
        if self.route.requested != self.request.backend || !self.route.is_structurally_consistent() {
            return Err(ContractError::UndeclaredBackendChange);
        }
        if self.outcome == Outcome::Completed
            && !self.output_digest.is_some_and(|s| !s.trim().is_empty())
        { return Err(ContractError::MissingOutputArtifact); }
        if self.outcome == Outcome::Unknown && self.retry_permitted {
            return Err(ContractError::UnknownOutcomeRetry);
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn sample(variant: Variant, operation: Operation) -> Request<'static> {
        Request {
            id: "id", variant, operation, source_commit: variant.pinned_source().commit,
            code_use: CodeUse::IndependentImplementation, upstream_code_rights: Rights::Unknown,
            actor: "actor", project: "project", work_context: "context",
            model_id: "model", model_revision: "rev", input_digest: "sha256:source",
            dataset_provenance: Some("dataset"), backend: BackendClass::Cpu,
            rollback_ref: "rollback",
            authority: ExternalAuthorityRefs {
                grant: "grant", router: "router", hrb: "lease", workload_mode: "mode",
                security: "security", rights: "rights", approval: "approval", budget: "budget",
            },
        }
    }
    #[test] fn three_distinct_source_pins() {
        let a = Variant::CompressionAware2023.pinned_source();
        let b = Variant::CredibilityAware2025.pinned_source();
        let c = Variant::AdaptiveMoe2026.pinned_source();
        assert_ne!(a.repository, b.repository);
        assert_ne!(b.repository, c.repository);
        for pin in [a, b, c] { assert_eq!(pin.commit.len(), 40); }
    }
    #[test] fn cpu_optimization_request_is_structural_only() {
        assert_eq!(sample(Variant::CompressionAware2023, Operation::OptimizeModel).validate_structure(), Ok(()));
    }
    #[test] fn reject_cross_variant_operation() {
        assert_eq!(sample(Variant::CompressionAware2023, Operation::ModifyAttention).validate_structure(),
                   Err(ContractError::VariantMismatch));
    }
    #[test] fn reject_missing_authority_ref() {
        let mut r = sample(Variant::CompressionAware2023, Operation::OptimizeModel);
        r.authority.hrb = " ";
        assert_eq!(r.validate_structure(), Err(ContractError::MissingField));
    }
    #[test] fn reject_missing_training_dataset() {
        let mut r = sample(Variant::CompressionAware2023, Operation::OptimizeModel);
        r.dataset_provenance = None;
        assert_eq!(r.validate_structure(), Err(ContractError::MissingField));
    }
    #[test] fn reject_unpinned_revision() {
        let mut r = sample(Variant::CompressionAware2023, Operation::OptimizeModel);
        r.source_commit = "unverified";
        assert_eq!(r.validate_structure(), Err(ContractError::SourceRevisionMismatch));
    }
    #[test] fn deny_2025_upstream_code_without_root_license() {
        let mut r = sample(Variant::CredibilityAware2025, Operation::ModifyAttention);
        r.code_use = CodeUse::UpstreamCode;
        r.upstream_code_rights = Rights::Verified;
        assert_eq!(r.validate_structure(), Err(ContractError::UnverifiedCodeRights));
    }
    #[test] fn independent_2025_contract_is_describable() {
        assert_eq!(sample(Variant::CredibilityAware2025, Operation::ScoreEvidence).validate_structure(), Ok(()));
    }
    #[test] fn deny_cuda_reference_training_on_cpu() {
        let mut r = sample(Variant::AdaptiveMoe2026, Operation::TrainExperts);
        r.code_use = CodeUse::UpstreamCode;
        r.upstream_code_rights = Rights::Verified;
        assert_eq!(r.validate_structure(), Err(ContractError::UnsupportedReferenceBackend));
    }
    #[test] fn deny_silent_backend_change() {
        let receipt = Receipt {
            request: sample(Variant::CompressionAware2023, Operation::OptimizeModel),
            outcome: Outcome::Failed,
            route: ObservedRoute {
                requested: BackendClass::Cpu, actual: BackendClass::Accelerator,
                fallback_declared: false,
            },
            output_digest: None, retry_permitted: false,
        };
        assert_eq!(receipt.validate_structure(), Err(ContractError::UndeclaredBackendChange));
    }
    #[test] fn deny_false_completion_without_artifact() {
        let receipt = Receipt {
            request: sample(Variant::CompressionAware2023, Operation::OptimizeModel),
            outcome: Outcome::Completed,
            route: ObservedRoute {
                requested: BackendClass::Cpu, actual: BackendClass::Cpu, fallback_declared: false,
            },
            output_digest: None, retry_permitted: false,
        };
        assert_eq!(receipt.validate_structure(), Err(ContractError::MissingOutputArtifact));
    }
    #[test] fn deny_blind_retry_of_unknown_execution() {
        let receipt = Receipt {
            request: sample(Variant::CompressionAware2023, Operation::OptimizeModel),
            outcome: Outcome::Unknown,
            route: ObservedRoute {
                requested: BackendClass::Cpu, actual: BackendClass::Cpu, fallback_declared: false,
            },
            output_digest: None, retry_permitted: true,
        };
        assert_eq!(receipt.validate_structure(), Err(ContractError::UnknownOutcomeRetry));
    }
}
