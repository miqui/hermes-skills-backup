# Ansible Troubleshooting Reference

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| SSH connection failed | Wrong host/key/user | Check ansible_host, ansible_user, key |
| Permission denied | Need sudo/wrong user | Add `become: true`, check sudo config |
| Module not found | Collection not installed | `ansible-galaxy collection install` |
| Variable undefined | Missing var/typo | Check var name, define in vars |
| Syntax error | YAML/Jinja2 issue | Run `ansible-playbook --syntax-check` |
| Host unreachable | Network/SSH issue | `ansible host -m ping`, check firewall |

## Debug Commands

```bash
# Test connectivity
ansible all -m ping
ansible host -m ping -vvv

# Syntax check
ansible-playbook playbook.yml --syntax-check

# Dry run (check mode)
ansible-playbook playbook.yml --check

# Diff mode (show changes)
ansible-playbook playbook.yml --diff

# Verbose output
ansible-playbook playbook.yml -v     # Minimal
ansible-playbook playbook.yml -vv    # More
ansible-playbook playbook.yml -vvv   # Connection debug
ansible-playbook playbook.yml -vvvv  # Full debug

# List tasks without running
ansible-playbook playbook.yml --list-tasks

# List hosts
ansible-playbook playbook.yml --list-hosts

# Start at specific task
ansible-playbook playbook.yml --start-at-task="Task name"

# Step through tasks
ansible-playbook playbook.yml --step
```

## Connection Issues

### Test SSH

```bash
# Direct SSH test
ssh -i ~/.ssh/key user@host

# Ansible ping
ansible host -m ping -vvv

# Check SSH config
ansible host -m debug -a "var=ansible_ssh_private_key_file"
```

### Common SSH Fixes

```yaml
# In inventory or ansible.cfg
ansible_ssh_private_key_file: ~/.ssh/mykey
ansible_user: ubuntu
ansible_host: 192.168.1.10
host_key_checking: False  # Only for testing
```

### SSH Connection Options

```yaml
# In inventory
host1:
  ansible_host: 192.168.1.10
  ansible_ssh_common_args: '-o StrictHostKeyChecking=no'
  ansible_ssh_extra_args: '-o ConnectTimeout=10'
```

## Permission Issues

### Sudo Not Working

Start by confirming that the play or task is using privilege escalation intentionally:

```yaml
# Minimal become example
- hosts: all
  become: true
  become_method: sudo
  become_user: root
```

If the host is intended to support non-interactive automation, prefer validated sudoers rules under `/etc/sudoers.d/` rather than broad manual edits.

```bash
# Validate sudoers syntax before deployment or after changes
visudo -cf /etc/sudoers
visudo -cf /etc/sudoers.d/ansible
```

Safer guidance for Ansible automation:

- `NOPASSWD` is common for automated Ansible runs, but `user ALL=(ALL) NOPASSWD: ALL` is the broadest option.
- Prefer restricting which **target users** the Ansible account can become, for example `root`, `postgres`, or `www-data`, instead of treating unrestricted `ALL=(ALL)` as the default.
- Be careful with command-restricted sudo rules: Ansible often runs modules through `/bin/bash` plus a temporary Python wrapper, so narrow command allowlists may fail in surprising ways.
- When managing sudoers via Ansible, write files under `/etc/sudoers.d/` and validate with `visudo -cf %s`.

See [nopasswd-sudo.md](nopasswd-sudo.md) for patterns, testing steps, and environment-specific trade-offs.

### Ask for Sudo Password

```bash
ansible-playbook playbook.yml --ask-become-pass
```

## Variable Issues

### Debug Variables

```yaml
- name: Print all vars
  ansible.builtin.debug:
    var: vars

- name: Print specific var
  ansible.builtin.debug:
    var: my_var

- name: Print hostvars
  ansible.builtin.debug:
    var: hostvars[inventory_hostname]

- name: Print facts
  ansible.builtin.debug:
    var: ansible_facts
```

### Check Variable Precedence

```bash
# See where variable comes from
ansible-inventory --host hostname --yaml
```

### Undefined Variable

```yaml
# Provide default
value: "{{ my_var | default('fallback') }}"

# Check if defined
- name: Task
  when: my_var is defined

# Fail early if required
- name: Validate
  ansible.builtin.assert:
    that: my_var is defined
    fail_msg: "my_var must be set"
```

## Module Issues

### Module Not Found

```bash
# Install collection
ansible-galaxy collection install community.docker

# Check installed
ansible-galaxy collection list

# Update collections
ansible-galaxy collection install -r requirements.yml --force
```

### Module Arguments

```bash
# Get module documentation
ansible-doc ansible.builtin.copy
ansible-doc community.docker.docker_compose_v2
```

## Idempotency Issues

### Task Always Shows "changed"

```yaml
# Bad - always changed
- name: Run script
  ansible.builtin.command: /bin/script.sh

# Good - check first
- name: Run script
  ansible.builtin.command: /bin/script.sh
  args:
    creates: /opt/app/.installed

# Good - explicit changed_when
- name: Run script
  ansible.builtin.command: /bin/script.sh
  register: result
  changed_when: "'Created' in result.stdout"
```

### Test Idempotency

```bash
# Run twice, second should show all "ok"
ansible-playbook playbook.yml
ansible-playbook playbook.yml  # Should show "changed=0"
```

## Handler Issues

### Handler Not Running

- Handlers only run if task reports "changed"
- Handlers run at end of play, not immediately
- Force handler run: `ansible-playbook --force-handlers`

```yaml
# Force handler to run immediately
- name: Config change
  ansible.builtin.template:
    src: config.j2
    dest: /etc/app/config
  notify: Restart app

- name: Flush handlers
  ansible.builtin.meta: flush_handlers

- name: Continue with restarted service
  ansible.builtin.uri:
    url: http://localhost:8080/health
```

## Performance Issues

### Slow Playbook

```yaml
# Disable fact gathering if not needed
- hosts: all
  gather_facts: false

# Or gather specific facts
- hosts: all
  gather_facts: true
  gather_subset:
    - network
```

```bash
# Increase parallelism
ansible-playbook playbook.yml -f 20  # 20 forks

# Use pipelining (add to ansible.cfg)
# [ssh_connection]
# pipelining = True
```

### Callback Timer

```ini
# ansible.cfg
[defaults]
callbacks_enabled = timer, profile_tasks
```

## Recovery

### Failed Playbook

```bash
# Retry failed hosts
ansible-playbook playbook.yml --limit @playbook.retry

# Start at failed task
ansible-playbook playbook.yml --start-at-task="Failed Task Name"
```

### Cleanup After Failure

```yaml
- name: Risky operation
  block:
    - name: Do something
      ansible.builtin.command: /bin/risky
  rescue:
    - name: Cleanup on failure
      ansible.builtin.file:
        path: /tmp/incomplete
        state: absent
  always:
    - name: Always cleanup
      ansible.builtin.file:
        path: /tmp/lock
        state: absent
```
