# Manifest-only Crossplane bundle output

Use this reference when the user asks for YAML files only, especially for a standard Crossplane project layout.

## Default file set

When the request names a Crossplane project layout without asking for extra docs, the default deliverable is:

1. `providers.yaml`
2. `provider-config.yaml`
3. `xrd.yaml`
4. `composition.yaml`
5. `claim.yaml`

## Output rules

- Keep the response focused on the YAML manifests.
- Do not add README edits, repo publishing, PR creation, or ancillary documentation.
- If something cannot be fully automated in the manifests, leave a concise placeholder or comment at the relevant manifest location instead of expanding the scope.
- Ensure resource counts, names, parameters, status fields, and connection-secret keys described in comments match the actual YAML.

## Crossplane-specific checks

- Provider package names and apiVersions match the targeted provider family.
- `ProviderConfig` name matches every managed resource reference.
- XRD schema required fields, defaults, and claim names align with composition patches.
- Composition patches reference valid XR field paths.
- Any unresolved IRSA/OIDC trust relationship is marked as a placeholder rather than presented as finished automation.
- Claim example uses the API and fields actually defined by the XRD.

## Anti-patterns

- Adding explanatory prose that implies resources or behaviors not encoded in the manifests.
- Creating extra project files when the user asked for YAML only.
- Treating architecture notes as permission to drift away from the requested file set.
