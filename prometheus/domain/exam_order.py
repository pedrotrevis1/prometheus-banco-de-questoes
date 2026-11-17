"""Keep a teacher-chosen ordering of the global question selection."""


class ExamOrder:
    def __init__(self):
        self.ids = []

    def synchronize(self, selected):
        selected = set(selected)
        self.ids = [question_id for question_id in self.ids if question_id in selected]
        known = set(self.ids)
        self.ids.extend(sorted(selected - known))
        return tuple(self.ids)

    def move(self, index, delta):
        target = index + delta
        if not (0 <= index < len(self.ids) and 0 <= target < len(self.ids)):
            return index
        self.ids[index], self.ids[target] = self.ids[target], self.ids[index]
        return target
