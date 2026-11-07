"""Actual Windows PowerShell regression checks. No keys, Noon or Sheets access."""
import subprocess,unittest,os
from windows_tasks import STOP_OWNED_TASKS
OLD=r"$ErrorActionPreference='Stop'; foreach($n in @('AEDIGITAL Noon Monitor','AEDIGITAL Noon Public Monitor 10min')) { $t=Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue; if($t){ Stop-ScheduledTask -TaskName $n; Disable-ScheduledTask -TaskName $n | Out-Null } }"
MOCK_EMPTY=r"function Get-ScheduledTask { [CmdletBinding()]param([string]$TaskName); if($TaskName){Write-Error 'The specified task does not exist'} }"+'\n'
def powershell(script):return subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],text=True,capture_output=True)
@unittest.skipUnless(os.name=='nt','Windows PowerShell required')
class Startup(unittest.TestCase):
    def test_reproduce_old_hidden_failure(self):
        result=powershell(MOCK_EMPTY+OLD)
        print('OLD_SCRIPT_EXIT',result.returncode,'STDERR_LENGTH',len(result.stderr))
        self.assertNotEqual(result.returncode,0)
    def test_new_empty_task_list_succeeds(self):
        r=powershell(MOCK_EMPTY+STOP_OWNED_TASKS);self.assertEqual(r.returncode,0,r.stderr);self.assertIn('owned tasks found: 0',r.stdout)
    def test_enumeration_failure_is_visible(self):
        r=powershell("function Get-ScheduledTask { throw 'SIMULATED_ENUMERATION_FAILURE' }\n"+STOP_OWNED_TASKS)
        self.assertEqual(r.returncode,1);self.assertIn('SIMULATED_ENUMERATION_FAILURE',r.stderr)
    def test_stop_failure_is_visible(self):
        setup="function Get-ScheduledTask { [pscustomobject]@{TaskName='AEDIGITAL Noon Monitor'} }; function Stop-ScheduledTask { throw 'SIMULATED_STOP_FAILURE' }\n"
        r=powershell(setup+STOP_OWNED_TASKS);self.assertEqual(r.returncode,1);self.assertIn('SIMULATED_STOP_FAILURE',r.stderr)
    def test_existing_owned_task_stopped(self):
        setup="function Get-ScheduledTask { [pscustomobject]@{TaskName='AEDIGITAL Noon Monitor'}; [pscustomobject]@{TaskName='UNRELATED TASK'} }; function Stop-ScheduledTask {param($TaskName) Write-Output ('STOPPED:'+ $TaskName)}; function Disable-ScheduledTask {param($TaskName) Write-Output ('DISABLED:'+ $TaskName)}\n"
        r=powershell(setup+STOP_OWNED_TASKS);self.assertEqual(r.returncode,0,r.stderr);self.assertIn('STOPPED:AEDIGITAL Noon Monitor',r.stdout);self.assertNotIn('STOPPED:UNRELATED TASK',r.stdout)
    def test_real_scheduler_read_only(self):
        r=powershell("$ErrorActionPreference='Stop'; Get-ScheduledTask -ErrorAction Stop | Select-Object -First 1 -ExpandProperty State; exit 0")
        self.assertEqual(r.returncode,0,r.stderr)
if __name__=='__main__':unittest.main(verbosity=2)
