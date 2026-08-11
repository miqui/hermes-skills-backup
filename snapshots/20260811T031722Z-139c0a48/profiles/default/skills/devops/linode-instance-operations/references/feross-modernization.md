# Feross article modernization map

## Source

- Feross Aboukhadijeh, [How To Set Up Your Linode For Maximum Awesomeness](https://feross.org/how-to-setup-your-linode/)
- The article identifies itself as last updated in June 2020.

## What to retain

The article’s lifecycle remains useful:

1. Provision deliberately.
2. Establish non-root administrative access.
3. Harden remote access and network exposure.
4. Patch and monitor the host.
5. Plan and test recovery.

## What not to copy verbatim

| Historical guidance | Modern skill treatment |
| --- | --- |
| Ubuntu 18.04 | Select a currently supported LTS image at execution time. |
| RSA 4096 as the default SSH key | Prefer Ed25519 when compatible; document exceptions. |
| Change SSH to port 444 | Optional policy decision only; never a substitute for keys, allowlists, patching, or monitoring. |
| Manual root-password bootstrap assumptions | Use provider-supported SSH key and least-privilege bootstrap paths where available. |
| Fail2Ban as universal baseline | Add only when the authentication model, logs, and local-firewall integration justify it. |
| Automatic OOM reboot / generic kernel tuning | Treat as workload-specific after diagnosis and capacity review. |
| Install Nginx, Node.js, MySQL in the same guide | Hand off to service-specific skills. |
| Enable backups | Define RPO/RTO, coverage, restore ownership, and restore-test evidence. |

## Design rule

Use a historical article as a source of problems and lifecycle sequencing, not as a frozen command reference. Verify provider controls, operating-system support, service names, and CLI/API behavior against current official documentation before acting.
