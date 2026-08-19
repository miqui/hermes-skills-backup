---
name: ansible
description: "Use when writing, reviewing, troubleshooting, or designing Ansible playbooks, inventories, roles, variables, modules, and collection-based automation workflows, including Proxmox VE and Docker integrations."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ansible, iac, automation, playbooks, inventory, roles, jinja2, proxmox, docker, configuration-management]
    related_skills: [cloud-architect, terraform-infrastructure, crossplane]
---

# Ansible

## Overview

Ansible is an agentless automation framework for configuration management, application deployment, orchestration, and repeatable operational workflows. It is most effective when you model desired state declaratively, organize reusable automation into inventories and roles, and verify that repeated runs remain idempotent.

This skill is a compact working reference for:

- playbook structure and execution flow
- inventory layout and host/group targeting
- variable precedence and Jinja2 usage
- common module usage patterns
- troubleshooting failed runs and privilege escalation issues
- collection-based integrations such as `community.general` and `community.docker`

Prefer Ansible-native modules over shell commands whenever possible. Reach for ad-hoc commands sparingly, and treat playbooks as versioned automation assets rather than disposable command wrappers.

## When to Use

Use this skill when you need to:

- write or review Ansible playbooks
- design inventory, `group_vars`, `host_vars`, and role layouts
- troubleshoot failed Ansible runs, module resolution, SSH access, or privilege escalation
- choose between ad-hoc commands, reusable roles, and structured playbooks
- work with common Ansible modules and collection-based integrations
- improve idempotency, check-mode behavior, and repeatability in infrastructure automation

Do not use this skill as the primary reference for:

- provider-specific cloud architecture decisions that are not mainly about Ansible
- general container orchestration design unrelated to Ansible automation
- secrets-management policy design beyond the immediate Ansible usage surface

## Quick Reference

```bash
# Test connectivity
ansible all -m ping
ansible <group> -m ping

# Run playbook
ansible-playbook playbook.yml
ansible-playbook playbook.yml -l <host>    # Limit to host
ansible-playbook playbook.yml --check      # Dry-run
ansible-playbook playbook.yml -vvv         # Verbose

# Tags
ansible-playbook playbook.yml --tags "deploy"
ansible-playbook playbook.yml --skip-tags "backup"
ansible-playbook playbook.yml --list-tags

# Variables
ansible-playbook playbook.yml -e "var=value"
ansible-playbook playbook.yml -e "@vars.yml"

# Ad-hoc commands
ansible <group> -m shell -a "command"
ansible <group> -m copy -a "src=file dest=/path"
ansible <group> -m apt -a "name=package state=present"

# Galaxy
ansible-galaxy collection install -r requirements.yml
ansible-galaxy role install <role>
```

## Reference Files

Load on-demand based on task:

| Topic | File | When to Load |
|-------|------|--------------|
| Playbook Structure | [playbooks.md](references/playbooks.md) | Writing playbooks |
| Inventory | [inventory.md](references/inventory.md) | Host/group configuration |
| Variables | [variables.md](references/variables.md) | Variable precedence, facts |
| Modules | [modules.md](references/modules.md) | Common module reference |
| Troubleshooting | [troubleshooting.md](references/troubleshooting.md) | Common errors, debugging |
| NOPASSWD Sudo | [nopasswd-sudo.md](references/nopasswd-sudo.md) | `become`, sudoers scope, validation, testing |

## Playbook Quick Reference

```yaml
---
- name: Deploy application
  hosts: webservers
  become: true
  vars:
    app_port: 8080

  pre_tasks:
    - name: Validate requirements
      ansible.builtin.assert:
        that:
          - app_secret is defined

  tasks:
    - name: Install packages
      ansible.builtin.apt:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - python3

    - name: Deploy config
      ansible.builtin.template:
        src: app.conf.j2
        dest: /etc/app/app.conf
      notify: Restart app

  handlers:
    - name: Restart app
      ansible.builtin.service:
        name: app
        state: restarted

  post_tasks:
    - name: Verify deployment
      ansible.builtin.uri:
        url: "http://localhost:{{ app_port }}/health"
```

## Variable Precedence (High to Low)

1. Extra vars (`-e "var=value"`)
2. Task vars
3. Block vars
4. Role/include vars
5. Play vars
6. Host facts
7. `host_vars/`
8. `group_vars/`
9. Role defaults

Use `extra vars` sparingly for stable automation because they are the hardest layer to override safely and can hide configuration drift.

## Directory Structure

```text
ansible/
├── ansible.cfg
├── inventory/
│   └── hosts.yml
├── group_vars/
│   ├── all.yml
│   └── webservers.yml
├── host_vars/
│   └── server1.yml
├── roles/
│   └── app/
│       ├── tasks/
│       ├── handlers/
│       ├── templates/
│       ├── files/
│       └── defaults/
├── playbooks/
│   └── deploy.yml
├── templates/
│   └── config.j2
└── requirements.yml
```

## Idempotency Checklist

- [ ] Tasks produce the same result on repeated runs
- [ ] No `changed_when: true` unless truly justified
- [ ] Native modules are preferred over `shell` and `command` where feasible
- [ ] Check mode (`--check`) reflects expected changes accurately
- [ ] A second run converges mostly to `ok` rather than repeated `changed`

## Common Pitfalls

1. **Using shell commands where a native module exists.** This usually reduces idempotency and makes check mode less trustworthy.
2. **Letting variable precedence become implicit.** When behavior is surprising, inspect `group_vars`, `host_vars`, role vars/defaults, and `-e` overrides before changing task logic.
3. **Mixing inventory structure and environment structure inconsistently.** Keep host targeting predictable and avoid inventing one-off layouts per playbook.
4. **Skipping `--check` and verbose runs during debugging.** `--check`, `--diff`, and `-vvv` often reveal logic or connectivity problems quickly.
5. **Treating privilege escalation as a playbook default instead of a scoped need.** Use `become` deliberately and keep escalation narrow.

## Verification Checklist

- [ ] The selected hosts/groups are the intended execution target
- [ ] Required collections or roles are installed before the run
- [ ] Variables and vault inputs are available for the target environment
- [ ] The playbook succeeds in `--check` mode when the workflow supports it
- [ ] Repeated execution is acceptably idempotent
- [ ] Any troubleshooting guidance used from `references/` matches the current environment and privilege model
