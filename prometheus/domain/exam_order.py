"""Keep a teacher-chosen ordering of the global question selection."""


class ExamOrder:
    def __init__(self):
        self.ids = []

    def preview(self, selected):
        selected = set(selected)
        retained = [question_id for question_id in self.ids if question_id in selected]
        known = set(retained)
        return tuple(retained + sorted(selected - known))

    def synchronize(self, selected):
        self.ids = list(self.preview(selected))
        return tuple(self.ids)

    def move(self, index, delta):
        target = index + delta
        if not (0 <= index < len(self.ids) and 0 <= target < len(self.ids)):
            return index
        self.ids[index], self.ids[target] = self.ids[target], self.ids[index]
        return target
