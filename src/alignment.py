class Alignment:
    def __init__(self, source, target, source_sub_ids = [], target_sub_ids = []):
        """

        """
        self.source = source
        self.target = target
        self.source_ids = [i for x in source_sub_ids for i in x]
        self.target_ids = [i for x in target_sub_ids for i in x]

        # Set externally
        self.source_subs = []
        self.target_subs = []

    def start(self) -> int:
        return min([sub.start for sub in (self.source_subs + self.target_subs)])

    def end(self) -> int:
        return max([sub.end for sub in (self.source_subs + self.target_subs)])

    def __str__(self):
        return f'{self.source} <-> {self.target}'

    def __eq__(self, other: "Alignment"):
        return str(self) == str(other)
