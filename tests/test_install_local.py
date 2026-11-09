import importlib.util
import json
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("install_local", SOURCE / "scripts/install-local.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallLocalTests(unittest.TestCase):
    def test_install_preserves_utilities_settings_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            def put(name, text):
                p = home / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
                return p
            settings = put('.claude/settings.json', json.dumps({
                "enabledPlugins": {"lib@local": True, "octo@nyldn-plugins": True},
                "unrelated": {"keep": 42}}))
            config = put('.codex/config.toml', '[plugins."sprint@claude-local"]\nenabled = true\n\n'
                         '[plugins."lib@claude-local"]\nenabled = true\n')
            old = put('.claude/plugins/cache/local/lib/1/skills/babysit-pr/SKILL.md', 'old workflow')
            utility = put('.claude/plugins/cache/local/lib/1/skills/github/SKILL.md', 'keep utility')
            source = home / 'octopus-source'
            source.mkdir()
            export = home / '.agents/skills/claude-octopus'
            export.parent.mkdir(parents=True)
            export.symlink_to(source)
            project = home / 'project'
            instructions = put('project/AGENTS.md', '# Project\n\n## Team Sprint Mode\nold\n\n## Other\nkeep\n')
            retired = [put(f'{host}/skills/sol-loop/SKILL.md', 'old sol-loop') for host in ('.claude', '.codex')]
            backup, changes = installer.install(home, project)
            for old_skill in retired:
                self.assertFalse(old_skill.parent.exists())
                record = next(x for x in changes if x['path'] == str(old_skill.parent))
                self.assertEqual((Path(record['backup']) / 'SKILL.md').read_text(), 'old sol-loop')
            self.assertEqual(len(list((home / '.claude/skills').glob('*/SKILL.md'))), 9)
            self.assertEqual(len(list((home / '.codex/skills').glob('*/SKILL.md'))), 9)
            self.assertEqual((home / '.claude/skills/full-stop/SKILL.md').read_bytes(),
                             (SOURCE / 'skills/full-stop/SKILL.md').read_bytes())
            for host in ('.claude', '.codex'):
                entry = home / host / 'skills/review-loop/SKILL.md'
                self.assertTrue((entry.parent / '../full-send/references/project-context.md').resolve().is_file())
            data = json.loads(settings.read_text())
            self.assertEqual(data['unrelated'], {'keep': 42})
            self.assertTrue(data['enabledPlugins']['lib@local'])
            self.assertFalse(data['enabledPlugins']['octo@nyldn-plugins'])
            self.assertEqual(data['env']['JEV_DISABLED'], '1')
            data = tomllib.loads(config.read_text())
            self.assertFalse(data['plugins']['sprint@claude-local']['enabled'])
            self.assertTrue(data['plugins']['lib@claude-local']['enabled'])
            self.assertEqual(data['shell_environment_policy']['set']['JEV_DISABLED'], '1')
            self.assertIn('canonical babysit-pr', old.read_text())
            self.assertEqual(utility.read_text(), 'keep utility')
            self.assertTrue(source.is_dir())
            self.assertFalse(export.is_symlink())
            self.assertIn('## Other\nkeep', instructions.read_text())
            self.assertNotIn('## Team Sprint Mode', instructions.read_text())
            record = next(x for x in changes if x['path'] == str(old))
            self.assertEqual(Path(record['backup']).read_text(), 'old workflow')
            record = next(x for x in changes if x['path'] == str(export))
            self.assertEqual(record['symlink'], str(source))
            self.assertTrue((backup / 'manifest.json').exists())
            # Rerunning keeps utility settings and installs a complete dependency set.
            installer.install(home, project)
            self.assertEqual(utility.read_text(), 'keep utility')

    def test_refuses_writing_inside_git_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            subprocess.run(['git', 'init', '-q', str(home)], check=True)
            with self.assertRaisesRegex(RuntimeError, 'inside a git checkout'):
                installer.install(home)
            self.assertFalse((home / '.claude/skills/full-stop/SKILL.md').exists())
            self.assertFalse((home / '.local/state/tstack').exists())

    def test_symlink_into_git_checkout_is_rejected_before_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            home, repo = root / 'home', root / 'dotfiles'
            home.mkdir()
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            target = repo / 'settings.json'
            original = '{"enabledPlugins": {"octo@nyldn-plugins": true}}'
            target.write_text(original)
            (home / '.claude').mkdir()
            (home / '.claude/settings.json').symlink_to(target)
            with self.assertRaisesRegex(RuntimeError, 'inside a git checkout'):
                installer.install(home)
            self.assertEqual(target.read_text(), original)
            self.assertFalse((home / '.codex/skills').exists())
            self.assertFalse((home / '.local/state/tstack').exists())

    def test_safe_settings_symlink_is_preserved_and_real_file_backed_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            target = home / 'actual-settings.json'
            original = '{"enabledPlugins": {"octo@nyldn-plugins": true}}'
            target.write_text(original)
            (home / '.claude').mkdir()
            link = home / '.claude/settings.json'
            link.symlink_to(target)
            backup, changes = installer.install(home)
            self.assertTrue(link.is_symlink())
            self.assertFalse(json.loads(target.read_text())['enabledPlugins']['octo@nyldn-plugins'])
            record = next(x for x in changes if x['path'] == str(target))
            self.assertEqual(Path(record['backup']).read_text(), original)

    def test_commented_toml_disables_retired_plugins_and_keeps_other_tables(self):
        text = ('[plugins."sprint@claude-local"] # installed\n'
                'enabled = true # current installation\n\n'
                '[plugins."lib@claude-local"]\nenabled = true\n')
        updated = installer.disable_retired_codex_plugins(text)
        parsed = tomllib.loads(updated)
        self.assertFalse(parsed['plugins']['sprint@claude-local']['enabled'])
        self.assertTrue(parsed['plugins']['lib@claude-local']['enabled'])
        self.assertIn('# current installation', updated)

    def test_bad_export_or_config_fails_before_install(self):
        for failure in ('export', 'json', 'toml'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp).resolve()
                if failure == 'export':
                    (home / '.agents/skills/claude-octopus').mkdir(parents=True)
                elif failure == 'json':
                    p = home / '.claude/settings.json'
                    p.parent.mkdir()
                    p.write_text('{invalid')
                else:
                    p = home / '.codex/config.toml'
                    p.parent.mkdir()
                    p.write_text('[broken')
                with self.assertRaises((RuntimeError, ValueError)):
                    installer.install(home)
                self.assertFalse((home / '.claude/skills').exists())
                self.assertFalse((home / '.local/state/tstack').exists())

    def test_codex_environment_preserves_existing_values_and_is_repeatable(self):
        original = '[shell_environment_policy.set]\nKEEP = "value"\nJEV_DISABLED = "0"\n'
        updated = installer.configure_codex(original)
        self.assertEqual(tomllib.loads(updated)['shell_environment_policy']['set'],
                         {'KEEP': 'value', 'JEV_DISABLED': '1'})
        self.assertEqual(installer.configure_codex(updated), updated)

    def test_project_instructions_drop_retired_workflow_sections(self):
        claude = ('# CLAUDE.md\n\n- `kanban/` — File-based Kanban boards for team sprints\n- `plans/` — keep\n\n'
                  '## Team Sprint Mode\n\n### Every Turn\nspawn agents\n\n## Session Progress Log\nkeep\n')
        agents = ('<!-- BEGIN BEADS INTEGRATION -->\n- ✅ Use bd for ALL task tracking\n'
                  '- ❌ Do NOT use external issue trackers\n\n'
                  '## Landing the Plane (Session Completion)\n\n- NEVER stop before pushing\n\n'
                  '<!-- END BEADS INTEGRATION -->\n')
        claude_out = installer.migrate_project_instructions(claude)
        self.assertNotIn('kanban/', claude_out)
        self.assertNotIn('spawn agents', claude_out)
        self.assertIn('## Delivery workflows', claude_out)
        self.assertIn('## Session Progress Log\nkeep', claude_out)
        agents_out = installer.migrate_project_instructions(agents)
        self.assertNotIn('NEVER stop before pushing', agents_out)
        self.assertNotIn('external issue trackers', agents_out)
        self.assertIn('## Ending a session', agents_out)
        self.assertTrue(agents_out.endswith('<!-- END BEADS INTEGRATION -->\n'))
        for text in (claude_out, agents_out):
            self.assertEqual(installer.migrate_project_instructions(text), text)

    def test_project_root_migrates_claude_md_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            project = home / 'project'
            project.mkdir()
            (project / 'CLAUDE.md').write_text('## Team Sprint Mode\nold\n\n## Other\nkeep\n')
            backup, changes = installer.install(home, project)
            text = (project / 'CLAUDE.md').read_text()
            self.assertNotIn('Team Sprint Mode', text)
            self.assertIn('## Other\nkeep', text)
            self.assertIn(str(project / 'CLAUDE.md'), [c['path'] for c in changes])


if __name__ == '__main__':
    unittest.main()
