import os, re, subprocess, shutil, tempfile, collections

Icon = collections.namedtuple("Icon", ["id", "width", "height", "bits", "data"])

def _exec(cmd, ignoreError=False):
  process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = process.communicate()
  if process.returncode and not ignoreError:
    raise Exception("Command failed: %s, %s" % (cmd, err))
  return out

def _extractExeIcons(path, targetDir, onlyNr=None):
  if not os.path.exists(targetDir):
    os.mkdirs(targetDir)
  
def readIcoIcons(icoFile):
  icons = []
  for line in _exec(["icotool", "-l", icoFile]).splitlines():
    f = re.match("--icon --index=([0-9]+) --width=([0-9]+) --height=([0-9]+) --bit-depth=([0-9]+) --palette-size=([0-9]+)", line)
    index, width, height, bits = int(f.group(1)), int(f.group(2)), int(f.group(3)), int(f.group(4))
    try:
      data = _exec(["icotool", "-x", "--icon", "--index=%d" % index, "-o", "-", icoFile])
    except:
      data = None
    icons.append(Icon(index, width, height, bits, data))
  return icons

def readExeIcons(path, onlyNr=None):
  tmpdir = tempfile.mkdtemp()
  if onlyNr == None:
    _exec(["wrestool", "-x", "-t14", "--output", tmpdir, path])
  else:
    _exec(["wrestool", "-x", "-t14", "-n%d" % onlyNr, "--output", tmpdir, path])
  icons = []
  for fname in os.listdir(tmpdir):
    icons += readIcoIcons(os.path.join(tmpdir, fname))
  shutil.rmtree(tmpdir)
  return icons
  
def bestIcon(icons):
  icons.sort(reverse=True, key=lambda i: i.bits * 10 + i.width + i.height - i.id)
  return icons[0] if icons else None