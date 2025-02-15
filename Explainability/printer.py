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
            item = super().pop(0)
            self._cond.notify_all()
            return item
    
    def await_empty(self):
        with self._cond:
            while len(self):
                self._cond.wait()
        
class ListPrinter:
    def __init__(self, ):
        self.data_list:BlockingList = BlockingList()
        self.printing = False
        self.speed = 0.2
        self.start()

    def add_string(self, string:str):
        self.data_list.append(string)

    def add_and_wait(self, string:str):
        self.data_list.append(string)
        self.await_print()

    def print_chunk(self, chunk:str):
        self.await_print()
        print(chunk, end="", flush=True)


    def _print_strings(self):
        while True:
            string:str = self.data_list.pop_or_sleep()
            speed = self.speed
            self.printing = True
            if string == "DONE":
                break
            for word in string.split(" "):
                if len(word) > 5:
                    for i in range(0, len(word), 5):
                        print(f"\033[90m{word[i:i+5]}\033[0m", end="", flush=True)
                        time.sleep(speed)
                    print(" ", end="", flush=True)
                    continue
                print(f"\033[90m{word}\033[0m", end=" ", flush=True)
                time.sleep(speed)
            print()
            self.printing = False
    
    def await_print(self):
        self.data_list.await_empty()
        while self.printing:
            time.sleep(0.1)
    
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