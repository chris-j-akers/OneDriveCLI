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

class Init(CLICommand):

    def execute(self):
        odc = OneDriveCLI()
        odc.initialise()
        print('OneDrive CLI for Linux initialised')


class IsInit(CLICommand):

    def execute(self):
        odc = OneDriveCLI()
        return odc.is_initialised()


class DebugOn(CLICommand):

    def execute(self):
        odc = OneDriveCLI()
        odc.debug_on(True)


class DebugOff(CLICommand):

    def execute(self):
        odc = OneDriveCLI()
        odc.debug_on(False)


class Pwd(CLICommand):

    def execute(self):
        odc = OneDriveCLI()
        print(odc.pwd())
        

class Ls(CLICommand):

    def execute(self):
        odc = OneDriveCLI()
        print(odc.ls())


class Cd(CLICommand):

    def __init__(self, arglist) -> None:
        self._path = self._get_arg(arglist, 2, '/')

    def execute(self):
        odc = OneDriveCLI()
        print(odc.cd(self._path))


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


class Put(CLICommand):

    def __init__(self, arglist) -> None:
        self.source = self.get_arg(arglist, 2)
        if self._source is None:
            print("error: no source file specified")
            raise ValueError
        self._destination = self._get_arg(arglist, 3, './')

    def execute(self):
        odc = OneDriveCLI()
        odc.put(self.source, self._destination)

