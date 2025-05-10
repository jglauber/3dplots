class DataRangeFileMismatch(Exception):
    """
    Error class when number of data ranges does not match number of provided filenames.
    """

    def __init__(self, num_filenames: int, num_ranges: int, num_devices: int):
        self.num_filenames = num_filenames
        self.num_ranges = num_ranges
        self.num_devices = num_devices
        self.error_code = 1
        self.msg = "The number of filenames and devices must equal the number of data ranges"
        super().__init__(self.msg)

    def __str__(self):
        return (f"[Error {self.error_code}] List Size Mismatch\n"
               f"    filenames: {self.num_filenames}, devices: {self.num_devices},"
               f" dataranges: {self.num_ranges} -> {self.msg}.")