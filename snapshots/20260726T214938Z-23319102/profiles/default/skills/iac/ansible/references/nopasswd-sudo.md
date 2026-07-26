# Ansible NOPASSWD Sudo Reference

This note captures practical guidance for running Ansible with `become` in environments that use `NOPASSWD` sudo rules.

Source reviewed:
- OneUptime blog: "How to Use Ansible become with NOPASSWD sudo Rules" (2026-02-21)
- URL: https://oneuptime.com/blog/post/2026-02-21-how-to-use-ansible-become-with-nopasswd-sudo-rules/view

## Key Takeaways

- `NOPASSWD` is common in automated Ansible environments because non-interactive runs cannot reliably stop for password entry.
- `user ALL=(ALL) NOPASSWD: ALL` works, but it is the **least restrictive** option.
- For Ansible, command-restricted sudo rules are often trickier than they appear because Ansible typically invokes Python modules through a shell wrapper rather than directly running the task-facing command path.
- A practical middle ground is usually to restrict **which target users** the Ansible service account can become, rather than trying to enumerate every command path.
- When deploying sudoers rules, validate them with `visudo -cf %s` before writing them in place.

## Why command restrictions are tricky with Ansible

With verbose output, Ansible often ends up executing something structurally similar to:

```bash
sudo -H -S -n -u root /bin/bash -c '/usr/bin/python3 /tmp/.ansible/tmp/AnsiballZ_<module>.py'
```

This means sudo may see `/bin/bash` or `/bin/sh` driving a temporary Python module wrapper, not the high-level module name or the apparent business command from the playbook. Because of that:

- very narrow command allowlists can fail unexpectedly
- troubleshooting becomes confusing if sudo policy and Ansible execution paths do not match
- target-user restrictions are often easier to reason about than large command allowlists

## Preferred pattern: restrict by target user

Prefer rules like:

```sudoers
# /etc/sudoers.d/ansible
Defaults:deploy !requiretty

deploy ALL=(root) NOPASSWD: ALL
deploy ALL=(postgres) NOPASSWD: ALL
deploy ALL=(www-data) NOPASSWD: ALL
```

This is still powerful, but narrower than allowing the Ansible user to become any user on the system.

## Environment-specific examples

Production or shared environments usually deserve more constrained rules than development boxes.

```sudoers
# Safer shared-environment pattern
Defaults:deploy !requiretty
Defaults:deploy log_output
Defaults:deploy logfile=/var/log/ansible-sudo.log
Defaults:deploy secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults:deploy env_reset

deploy ALL=(root,postgres,www-data) NOPASSWD: ALL
```

```sudoers
# Broader development-only pattern
Defaults:deploy !requiretty

deploy ALL=(ALL) NOPASSWD: ALL
```

Treat the broad development pattern as a convenience trade-off, not the default recommendation.

## Deploying rules with Ansible

Prefer managing sudoers via a validated file under `/etc/sudoers.d/`.

```yaml
- name: Deploy sudoers configuration
  ansible.builtin.template:
    src: templates/ansible-sudoers.j2
    dest: /etc/sudoers.d/ansible
    mode: '0440'
    owner: root
    group: root
    validate: "visudo -cf %s"
```

Useful companion settings:

```sudoers
Defaults:deploy !requiretty
Defaults:deploy log_output
Defaults:deploy logfile=/var/log/ansible-sudo.log
```

## Testing NOPASSWD behavior

After rollout, verify both Ansible `become` and non-interactive sudo behavior.

```yaml
- name: Test become to root
  ansible.builtin.command: whoami
  become: true
  become_user: root

- name: Test non-interactive sudo
  ansible.builtin.command: sudo -n -u root whoami
```

Also useful during debugging:

```bash
ansible web1 -m command -a "whoami" --become -vvvv 2>&1 | grep sudo
```

## Recommendations for this skill

- Prefer **target-user restriction** over a large command allowlist unless you have verified the actual sudo invocation path for the environment.
- Treat `NOPASSWD: ALL` as acceptable only when explicitly scoped to the users the Ansible service account must become.
- Avoid presenting `ubuntu ALL=(ALL) NOPASSWD: ALL` as the generic default without context.
- Keep `--ask-become-pass` documented as a fallback for hosts that intentionally do not use `NOPASSWD`.
