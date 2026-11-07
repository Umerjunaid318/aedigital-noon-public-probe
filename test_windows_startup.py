"""Windows integration tests for current-user autostart, isolated in temp folders."""
import subprocess,unittest,os,tempfile,sys,time
from pathlib import Path
from startup_control import write_startup_launcher,start_background
@unittest.skipUnless(os.name=='nt','Windows required')
class Startup(unittest.TestCase):
    def test_startup_batch_executes_worker_from_space_path(self):
        with tempfile.TemporaryDirectory(prefix='AE monitor ') as d:
            root=Path(d);worker=root/'sample worker.py';worker.write_text("from pathlib import Path\nPath('started.txt').write_text('ok')\n")
            launcher=write_startup_launcher(root,root/'Startup test',python=sys.executable,worker=worker)
            r=subprocess.run([os.environ['COMSPEC'],'/d','/c',str(launcher)],text=True,capture_output=True,timeout=20)
            self.assertEqual(r.returncode,0,r.stderr)
            for _ in range(50):
                if (root/'started.txt').exists():break
                time.sleep(.1)
            self.assertEqual((root/'started.txt').read_text(),'ok')
    def test_background_worker_runs_and_captures_actual_failure(self):
        with tempfile.TemporaryDirectory(prefix='AE monitor ') as d:
            root=Path(d);(root/'logs').mkdir();worker=root/'worker.py';worker.write_text("raise RuntimeError('SIMULATED_VISIBLE_FAILURE')")
            p=start_background(root,python=sys.executable,worker=worker);self.assertEqual(p.wait(timeout=20),1)
            self.assertIn('SIMULATED_VISIBLE_FAILURE',(root/'logs/launcher.log').read_text())
    def test_missing_worker_does_not_create_autostart(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(FileNotFoundError):write_startup_launcher(root,root/'Startup')
            self.assertFalse((root/'Startup').exists())
    def test_existing_unrelated_startup_file_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder=root/'Startup';folder.mkdir();other=folder/'Other app.cmd';other.write_text('example')
            worker=root/'worker.py';worker.write_text('pass')
            write_startup_launcher(root,folder,python=sys.executable,worker=worker)
            self.assertEqual(other.read_text(),'example')
    def test_launcher_requires_no_powershell_or_elevation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);worker=root/'worker.py';worker.write_text('pass')
            file=write_startup_launcher(root,root/'Startup',python=sys.executable,worker=worker)
            text=file.read_text(encoding='mbcs').lower()
            for forbidden in ('powershell','schtasks','runas','executionpolicy','reg add'):self.assertNotIn(forbidden,text)
if __name__=='__main__':unittest.main(verbosity=2)
