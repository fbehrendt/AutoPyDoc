from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
import sys
import os
sys.path.append(os.path.abspath("C:/Users/Fabian/Projekte/AutoPyDoc"))

from working_repo.main import main

#with PyCallGraph(output=GraphvizOutput()):
    #main()

import pyan
from IPython.display import HTML
html_callgraph = pyan.create_callgraph(filenames="working_repo/src/*.py", format="html")
with open("myuses2.html","w") as f:
    f.write(html_callgraph)