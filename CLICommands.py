from OneDriveCLI import OneDriveCLI

# Base Class

class CLICommand:
    
    def _get_arg(self, arglist, index, default=None):
        try:
            return arglist[index]
        except(IndexError):
            return default

    def execute(self):
        raise NotImplementedError

# Commands 
    
class Get(CLICommand):

    def __init__(self, arglist) -> None:
        self._source = self._get_arg(arglist,2)
        if self._source is None:
            print("error: no source file specified")
            raise ValueError
        self._destination = self._get_arg(arglist, 3, './')

    def execute(self):
        odc = OneDriveCLI()
        odc.get(self._source, self._destination)
