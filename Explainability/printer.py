import threading
import time

class BlockingList (list):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cond = threading.Condition()

    def append(self, item):
        with self._cond:
            super().append(item)
            self._cond.notify_all()

    def pop_or_sleep(self):
        with self._cond:
            while not len(self):
                self._cond.wait()
            return self.pop()
        
class ListPrinter:
    def __init__(self, ):
        self.data_list:BlockingList = BlockingList()
        self.start()

    def add_string(self, string:str):
        self.data_list.append(string)

    def _print_strings(self):
        while True:
            string = self.data_list.pop_or_sleep()
            if string == "DONE":
                break
            for char in string:
                print(char, end="")
                time.sleep(0.1)
            print()
    
    def start(self):
        thread = threading.Thread(target=self._print_strings)
        thread.start()
    
    def stop(self):
        self.add_string("DONE")
        

def main():
    data = ["string1", "string2", "string3", "string4"]
    printer = ListPrinter(data)

    threads = []
    for _ in range(2):  # Create 2 threads for demonstration
        thread = threading.Thread(target=printer.print_strings)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()