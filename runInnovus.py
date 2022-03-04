import subprocess

def runInnovusSoC():
    process = subprocess.Popen(['/w/apps3/Cadence/INNOVUS191/bin/innovus', '-no_cmd', '-no_logv', '-no_gui', '-init', 'scripts_own/pdflow/pdSoc.tcl'], shell=False, stdin=subprocess.PIPE)
    process.communicate(b'exit')

def runInnovusF2B():
    process = subprocess.Popen(['/w/apps3/Cadence/INNOVUS191/bin/innovus', '-no_cmd', '-no_logv', '-no_gui', '-init', 'scripts_own/pdflow/pdf2bbot.tcl'], shell=False, stdin=subprocess.PIPE)
    process.communicate(b'exit')
    process = subprocess.Popen(['/w/apps3/Cadence/INNOVUS191/bin/innovus', '-no_cmd', '-no_logv', '-no_gui', '-init', 'scripts_own/pdflow/pdf2btop.tcl'], shell=False, stdin=subprocess.PIPE)
    process.communicate(b'exit')

def runInnovusF2F():
    raise NotImplementedError('f2f flow')
    process = subprocess.Popen(['/w/apps3/Cadence/INNOVUS191/bin/innovus', '-no_cmd', '-no_logv', '-no_gui', '-init', 'scripts_own/pdflow/pdf2fbot.tcl'], shell=False, stdin=subprocess.PIPE)
    process.communicate(b'exit')
    process = subprocess.Popen(['/w/apps3/Cadence/INNOVUS191/bin/innovus', '-no_cmd', '-no_logv', '-no_gui', '-init', 'scripts_own/pdflow/pdf2ftop.tcl'], shell=False, stdin=subprocess.PIPE)
    process.communicate(b'exit')
