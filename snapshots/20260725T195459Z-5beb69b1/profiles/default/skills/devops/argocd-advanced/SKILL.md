---
name: argocd-advanced
description: Use when working on advanced Argo CD automation: ApplicationSet generators and templating, Argo CD Image Updater, new-cluster bootstrapping, workload onboarding patterns, and related troubleshooting.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [argocd, applicationset, image-updater, gitops, kubernetes, multi-cluster]
    related_skills: [argocd, argo-workflows, deployment-engineer]
---

# ArgoCD Advanced

## Overview

Use this skill when core Argo CD application operations are not enough and the task shifts into higher-order GitOps automation: fleet-style ApplicationSet generation, automated image updates, multi-cluster bootstrap, or standardized workload onboarding.

This skill complements `argocd`; it does not replace it. Start with `argocd` for normal application lifecycle work, and move here when the task is about scale, automation, or platform patterns. If the task is about running workflow graphs on Kubernetes rather than reconciling GitOps applications, route to `argo-workflows`.

## When to Use

- Designing or troubleshooting ApplicationSet generators and templates
- Operating Argo CD Image Updater and git write-back flows
- Bootstrapping new Kubernetes clusters into an Argo CD multi-cluster setup
- Standardizing workload onboarding via ApplicationSet templates and repo patterns

## Scope routing

| If you need to… | Read |
|---|---|
| Implement multi-cluster app propagation with ApplicationSet generators (list / cluster / git / matrix / merge / SCM / pull-request / plugin) | `References/applicationset.md` plus `References/applicationset/` for deep-dive reference docs |
| Automate container image updates for ArgoCD-managed workloads (update strategies, ImageUpdater CRD, git write-back) | `References/image-updater.md` + `References/image-updater/` + `References/ArgocdImageUpdater/` + `Samples/image-updater/` |
| Bootstrap a new Kubernetes cluster into the multi-repo GitOps environment | `References/cluster-bootstrapping.md` + `References/cluster-bootstrapping/` + `References/ArgocdClusterBootstrapping/` |
| Onboard a new workload via the standardized ApplicationSet template | `References/application-install.md` + `Workflows/application-install/` |
| Look up which clusters target which services | `References/ClusterInventory.md` |

## Decision tree

```
Need new cluster registered with ArgoCD?           -> cluster-bootstrapping
Need new service deployed to existing clusters?    -> application-install
Need to fan one app definition across N clusters?  -> applicationset
Need images to roll forward automatically?         -> image-updater
```

## Gotchas

- **ApplicationSet generators are ordered.** With matrix/merge generators, the parent generator's result is the input to the child — get the order wrong and you get an empty parameter set with no error.
- **Image Updater + git write-back requires a write credential.** A read-only repo cred will silently leave images stuck on the original version. Check Image Updater pod logs for `permission denied` on push.
- **Bootstrap cluster secrets must carry the labels your ApplicationSet generators select on.** A cluster registered without the expected label key/value is invisible to existing ApplicationSets — and there is no error, just zero apps.
- **`application-install` ships a Hypera/Cafehyna-specific template.** The Workflows assume the multi-repo layout. If you're not in that environment, treat it as a reference pattern, not a runnable recipe.
- **CRD versions matter.** ApplicationSet ships with ArgoCD 2.3+; certain generators (SCM, pull request) need 2.5+. Read `References/applicationset.md` Version Compatibility before adopting.
