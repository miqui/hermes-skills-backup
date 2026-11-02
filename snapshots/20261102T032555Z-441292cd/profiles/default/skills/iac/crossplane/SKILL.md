---
name: crossplane
description: "Use when designing, reviewing, or troubleshooting Crossplane-based infrastructure APIs on Kubernetes, including provider packages, managed resources, XRDs, compositions, claims, composition functions, and production operating patterns for self-service cloud provisioning."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [crossplane, iac, kubernetes, platform-engineering, managed-resources, xrd, composition, claims, providers, multi-cloud]
    related_skills: [cloud-architect, terraform-infrastructure, cdk-patterns]
---

# Crossplane

## Overview

Crossplane turns Kubernetes into a control plane for cloud infrastructure and higher-level platform APIs. Use it to model external resources as Kubernetes objects, then layer reusable abstractions on top so application teams request infrastructure through stable, self-service APIs instead of provider-specific YAML.

Core hierarchy:

```text
Claim (namespace-scoped, optional)
  -> Composite Resource / XR (cluster-scoped)
    -> Managed Resources
      -> External cloud resources
```

Effective Crossplane work usually means:

- installing only the provider packages you actually need
- creating secure `ProviderConfig` objects for each account or environment
- exposing opinionated APIs through XRDs and claims
- composing managed resources with patches, transforms, and functions
- debugging reconciliation through conditions, events, and provider logs
- treating compositions and provider versions like APIs that require rollout discipline

## When to Use

Use this skill when you need to:

- build internal platform APIs for infrastructure on Kubernetes
- design or review Crossplane providers, managed resources, XRDs, compositions, or claims
- translate cloud-specific resources into safer self-service abstractions
- decide between direct managed resources and composite abstractions
- troubleshoot why a claim, XR, or managed resource is not becoming ready
- plan production patterns for multi-account, multi-team, or multi-environment setups

Do not default to Crossplane when the task is only a small one-off resource change and the organization does not already operate Kubernetes as a platform control plane.

## Core Concepts

### Providers and ProviderConfigs

- **Provider** installs a controller package that reconciles a family of external resources.
- **ProviderConfig** tells those resources how to authenticate and which account, project, or subscription to use.

Guidance:

- Prefer scoped providers or provider families when practical instead of a giant install footprint.
- Treat provider package versions as verified inputs, not copy-paste constants.
- Keep credentials and account selection out of tenant-controlled paths unless that is an intentional platform feature.
- Prefer workload identity mechanisms over long-lived static secrets when available.

Example provider skeleton:

```yaml
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws-s3
spec:
  package: xpkg.upbound.io/upbound/provider-aws-s3:<verified-version>
```

Example `ProviderConfig` pattern:

```yaml
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: platform-prod
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-creds
      key: creds
```

Recommended pattern:

- one `ProviderConfig` per environment or account
- explicit names like `platform-dev`, `platform-staging`, `platform-prod`
- compositions select the right config unless tenant choice is intentional

### Managed Resources

Managed resources are the lowest practical abstraction. They are useful for:

- early exploration
- platform team experiments
- cases where abstraction adds little value
- debugging the exact provider schema before wrapping it in a composite

Example:

```yaml
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: app-data
spec:
  forProvider:
    region: us-west-2
    tags:
      ManagedBy: crossplane
      Environment: dev
  providerConfigRef:
    name: platform-dev
  deletionPolicy: Delete
```

Use managed resources directly only when consumers truly need provider-specific control. Otherwise, promote them behind an XR or claim.

## Designing XRDs and Claims

### XRDs

An XRD defines the API you want platform users to consume. Keep it:

- small
- opinionated
- validated
- versioned
- decoupled from raw provider fields

Good XRDs expose business-meaningful parameters like `size`, `region`, `backupRetentionDays`, or `highAvailability`, not dozens of provider knobs.

Example skeleton:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xpostgresqlinstances.database.example.org
spec:
  group: database.example.org
  names:
    kind: XPostgreSQLInstance
    plural: xpostgresqlinstances
  claimNames:
    kind: PostgreSQLInstance
    plural: postgresqlinstances
  versions:
    - name: v1alpha1
      served: true
      referenceable: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                parameters:
                  type: object
                  properties:
                    size:
                      type: string
                      enum: [small, medium, large]
                    storageGB:
                      type: integer
                      minimum: 20
                    highAvailability:
                      type: boolean
                      default: false
                  required:
                    - size
```

### Claims vs XRs

Scope matters:

- **Claims are namespace-scoped**
- **Composite resources (XRs) are cluster-scoped**
- **Managed resources are usually cluster-scoped**

Implications:

- claims are the self-service interface for app teams
- RBAC should usually be granted on claims, not on XRs or managed resources
- claim metadata and XR metadata live in different scopes
- labels like `crossplane.io/claim-name` and `crossplane.io/claim-namespace` often bridge the two

Example claim:

```yaml
apiVersion: database.example.org/v1alpha1
kind: PostgreSQLInstance
metadata:
  name: orders-db
  namespace: team-a
spec:
  parameters:
    size: medium
    storageGB: 100
    highAvailability: true
  writeConnectionSecretToRef:
    name: orders-db-conn
```

## Writing Compositions That Age Well

A composition maps an XR to one or more managed resources.

## Output Discipline for Manifest-Only Requests

When the user asks to "complete the code for the yaml files," "only fill the manifests," or otherwise constrains the deliverable to Kubernetes/Crossplane YAML, treat that as a hard output-shape requirement.

Required behavior:

- return only the requested manifest files, in the requested filenames and order
- do not add README work, PR/publish workflow, repo-maintenance steps, or extra explanatory deliverables unless the user explicitly asks for them
- keep architectural claims synchronized with the manifests that actually exist; do not describe flexibility, resources, or post-processing that the YAML does not implement
- represent hard-coded values, placeholders, and manual follow-up points in the manifests themselves or in terse file-local comments, not in a separate speculative document
- when the request is for the standard Crossplane bundle shape, default to `providers.yaml`, `provider-config.yaml`, `xrd.yaml`, `composition.yaml`, and `claim.yaml`

See `references/manifest-bundle-output.md` for a concise checklist tailored to manifest-only Crossplane tasks.

### Prefer stable platform inputs over raw cloud inputs

Good composition design:

- accept `small|medium|large`
- map to instance class with transforms
- choose network defaults centrally
- apply platform tags automatically
- expose only the connection details users need

Example:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xpostgresqlinstances.aws
  labels:
    provider: aws
    service: postgres
spec:
  compositeTypeRef:
    apiVersion: database.example.org/v1alpha1
    kind: XPostgreSQLInstance
  writeConnectionSecretsToNamespace: crossplane-system
  resources:
    - name: db
      base:
        apiVersion: rds.aws.upbound.io/v1beta1
        kind: Instance
        spec:
          forProvider:
            engine: postgres
            skipFinalSnapshot: false
            publiclyAccessible: false
          providerConfigRef:
            name: platform-prod
      patches:
        - type: FromCompositeFieldPath
          fromFieldPath: spec.parameters.size
          toFieldPath: spec.forProvider.instanceClass
          transforms:
            - type: map
              map:
                small: db.t3.micro
                medium: db.t3.medium
                large: db.m6i.large
        - type: FromCompositeFieldPath
          fromFieldPath: spec.parameters.storageGB
          toFieldPath: spec.forProvider.allocatedStorage
        - type: ToCompositeFieldPath
          fromFieldPath: status.atProvider.endpoint
          toFieldPath: status.address
```

### Composition selection

Use intentionally:

- `compositionRef` when the exact composition should be fixed
- `compositionSelector` when label-based selection is part of the platform design
- XRD defaults when users should not need to choose

Avoid making composition choice a tenant burden unless it is itself a supported product feature.

### Composition updates affect live systems

Treat composition changes carefully.

Do not assume a composition edit is safe because no new claims are being created. Existing composites may adopt new revisions depending on revision and update policy.

Operational advice:

- review composition changes like API changes
- promote through dev, staging, and prod
- use composition revisions intentionally
- document which fields may cause replacement or disruptive drift
- communicate rollout expectations to application teams

## Composition Functions and Conditional Resources

Use composition functions when patch-and-transform alone becomes too rigid.

Best use cases:

- conditional resource creation
- loops or fan-out logic
- nontrivial naming or derived values
- combining multiple sources into rendered resources

Important caution: optional resources are not free. In classic compositions, a resource listed in `resources:` is part of desired state. If you truly need conditional creation, prefer:

1. separate compositions for distinct product tiers, or
2. a pipeline composition with a function that conditionally emits resources

Minimal pipeline example:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xappplatform.pipeline.aws
spec:
  compositeTypeRef:
    apiVersion: platform.example.org/v1alpha1
    kind: XAppPlatform
  mode: Pipeline
  pipeline:
    - step: render
      functionRef:
        name: function-patch-and-transform
```

Guidance:

- use separate compositions if the variation is large or product-level
- use a function when the variation is tactical and maintainable
- do not fake conditionals with placeholder resources
- keep the rendered resource set predictable and testable

## Debugging Workflow

When Crossplane is failing, debug from top to bottom.

### 1. Check the claim or XR

```bash
kubectl describe postgresqlinstance orders-db -n team-a
kubectl get postgresqlinstance orders-db -n team-a -o yaml
```

Look for:

- `Ready` and `Synced` conditions
- events
- whether the claim bound to an XR
- whether the connection secret was written

### 2. Inspect the XR

```bash
kubectl get xpostgresqlinstances
kubectl describe xpostgresqlinstance <name>
```

Look for:

- selected composition
- composition revision
- propagated status
- references to child managed resources

### 3. Inspect managed resources

```bash
kubectl get managed
kubectl describe <managed-kind> <managed-name>
```

Look for:

- provider auth errors
- invalid cloud parameters
- missing dependencies such as subnet groups or security groups
- external-name mismatch or immutable field problems

### 4. Inspect providers and package health

```bash
kubectl get providers
kubectl describe provider provider-aws-s3
kubectl get providerconfigs
kubectl describe providerconfig platform-prod
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider
```

Focus on:

- unhealthy provider package
- missing or broken credentials
- API throttling
- CRD or provider schema mismatch after upgrades

## Production Patterns

### Version discipline

- pin provider and function packages to versions you have verified
- upgrade deliberately, not implicitly
- re-check examples against installed CRDs before applying them
- expect provider schema drift over time

### Secure account isolation

- separate prod and non-prod accounts or projects
- bind them to separate `ProviderConfig` objects
- use least-privilege credentials
- prefer workload identity over static keys

### Safe deletion behavior

- use `deletionPolicy: Delete` only where teardown is expected
- use `Orphan` selectively for critical data stores when policy requires manual cleanup
- document deletion semantics clearly for tenants

### Connection secret hygiene

- expose only necessary keys
- write secrets to intended namespaces
- avoid leaking admin credentials broadly
- standardize secret key names across XRDs

### API design discipline

- keep XRDs focused on one logical product
- encode guardrails with enums, min/max, patterns, and defaults
- publish examples for the supported happy path
- document mutable vs disruptive parameters

## Common Pitfalls

1. **Using stale package versions.** Provider and function examples age quickly; verify current package coordinates and schemas before reuse. See `references/official-docs.md` for canonical Crossplane and Marketplace links.
2. **Confusing scope.** Claims are namespace-scoped; XRs and managed resources are not.
3. **Exposing raw provider fields in the XRD.** This makes the platform API brittle.
4. **Assuming composition updates only affect new resources.** Existing composites may adopt new revisions depending on policy.
5. **Trying to do conditional creation in static compositions.** Use separate compositions or functions.
6. **Letting tenants choose ProviderConfigs without guardrails.** That can create privilege or account-isolation problems.
7. **Ignoring immutable fields.** Many provider fields trigger replacement or are not updatable in place.
8. **Skipping tags and labels.** You lose ownership, cost visibility, and debugging context.
9. **Writing oversized “do everything” XRDs.** Smaller APIs are easier to validate, compose, and version.

## References

- Crossplane docs home: https://docs.crossplane.io/latest/
- Install Crossplane: https://docs.crossplane.io/latest/get-started/install/
- Composition overview: https://docs.crossplane.io/latest/composition/
- Managed resources: https://docs.crossplane.io/latest/managed-resources/
- Packages: https://docs.crossplane.io/latest/packages/
- Upbound Marketplace: https://marketplace.upbound.io/
- Supplemental reference file: `references/official-docs.md`

## Verification Checklist

- [ ] Provider and function packages are pinned to currently verified versions.
- [ ] Each managed resource resolves a valid `ProviderConfig`.
- [ ] Claim, XR, and managed resource scopes are reflected correctly in RBAC and docs.
- [ ] XRD schemas use validation, defaults, and clear required fields.
- [ ] The composition hides provider-specific complexity behind stable platform inputs.
- [ ] Connection secrets land in the correct namespace with the correct keys.
- [ ] Conditional resources are implemented with separate compositions or functions.
- [ ] Composition update behavior for existing composites is understood before rollout.
- [ ] Deletion policies match environment and data-retention expectations.
- [ ] Conditions, events, package health, and provider logs are part of the operating workflow.
