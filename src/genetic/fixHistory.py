class FixHistory:
    def __init__(self):
        self._fixed_locations = set()

    def is_fixed(self, *args):
        return args in self._fixed_locations

    def add_fixed_location(self, *args):
        self._fixed_locations.add(args)