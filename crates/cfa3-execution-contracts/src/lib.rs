//! Bootstrap-only, dependency-free *data contract* types.
//! No runtime routing, hardware admission or Evidence authority is implemented here.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BackendClass {
    Cpu,
    Accelerator,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObservedRoute {
    pub requested: BackendClass,
    pub actual: BackendClass,
    pub fallback_declared: bool,
}

impl ObservedRoute {
    /// Structural consistency, NOT authorization, execution proof, or Current Host PASS.
    pub fn is_structurally_consistent(&self) -> bool {
        self.fallback_declared == (self.requested != self.actual)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn cpu_native_route_is_not_fallback() {
        assert!(ObservedRoute { requested: BackendClass::Cpu, actual: BackendClass::Cpu, fallback_declared: false }.is_structurally_consistent());
    }
    #[test]
    fn gpu_to_cpu_requires_explicit_fallback_flag() {
        assert!(!ObservedRoute { requested: BackendClass::Accelerator, actual: BackendClass::Cpu, fallback_declared: false }.is_structurally_consistent());
        assert!(ObservedRoute { requested: BackendClass::Accelerator, actual: BackendClass::Cpu, fallback_declared: true }.is_structurally_consistent());
    }
    #[test]
    fn false_fallback_is_rejected() {
        assert!(!ObservedRoute { requested: BackendClass::Cpu, actual: BackendClass::Cpu, fallback_declared: true }.is_structurally_consistent());
    }
}

pub mod cram;
