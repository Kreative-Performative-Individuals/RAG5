import time
import sys

text = """Retrieving data of _List of machines_\n\
Selecting dates from _begin_ to _end_\n\
Using _KPI_calculation_engine_ to compute _Nome KPI_\n\
Formulating textual response"""
for char in text:
    sys.stdout.write(char)
    sys.stdout.flush()
    time.sleep(0.1)
for i in range(5):
    sys.stdout.write('\rFormulating textual response      ')
    sys.stdout.flush()
    time.sleep(0.2)
    sys.stdout.write('\rFormulating textual response.      ')
    sys.stdout.flush()
    time.sleep(0.2)
    sys.stdout.write('\rFormulating textual response..      ')
    sys.stdout.flush()
    time.sleep(0.2)
    sys.stdout.write('\rFormulating textual response...      ')
    sys.stdout.flush()
    time.sleep(0.3)

answer = """\n\nExample answer, from rag\n"""
for char in answer:
    sys.stdout.write(char)
    sys.stdout.flush()
    time.sleep(0.1)