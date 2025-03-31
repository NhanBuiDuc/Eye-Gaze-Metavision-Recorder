class FileSet:
    def __init__(self, index):
        self.index = index
        self.yaml_path = ""
        self.csv_path = ""
        self.raw_path = ""
        self.yaml_data = None
        self.csv_headers = None
        self.csv_rows = None
        self.raw_size = None
        self.raw_data = None  # Store raw data for visualization