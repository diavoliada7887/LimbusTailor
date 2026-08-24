from pathlib import Path
SRC = Path('/tmp/stu')

p = SRC / 'src/core/filters/output/Task.cpp'
t = p.read_text()
raw = '''    QImage out_img;\n    BinaryImage automask_img;\n    BinaryImage speckles_img;'''
with_score = raw + '''\n    double archiveScannerBackground = 0.0;'''
if raw in t:
    t = t.replace(raw, with_score)
p.write_text(t)

p = SRC / 'src/core/filters/output/OutputParams.cpp'
t = p.read_text()
if '#include <QString>' not in t:
    t = t.replace('#include <QDomElement>\n', '#include <QDomElement>\n#include <QString>\n', 1)
p.write_text(t)

print('geometry QC post-fix applied')
